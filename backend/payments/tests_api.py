from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from payments.models import Payment
from users.models import User
from wallets.models import Wallet


class PaymentAPITests(TestCase):

    def setUp(self):
        self.client = APIClient()

        self.user_a = User.objects.create_user(
            email="paymentapiA@balora.com",
            phone_number="08000000121",
            password="TestPassword123!",
        )

        self.user_b = User.objects.create_user(
            email="paymentapiB@balora.com",
            phone_number="08000000122",
            password="TestPassword123!",
        )

        self.wallet_a = Wallet.objects.create(
            user=self.user_a,
            balance=10_000,
        )

        self.wallet_b = Wallet.objects.create(
            user=self.user_b,
            balance=20_000,
        )

    def authenticate(self, user):
        refresh = RefreshToken.for_user(user)

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}"
        )

    def create_payment(
        self,
        user,
        wallet,
        reference,
        amount=5_000,
    ):
        return Payment.objects.create(
            user=user,
            wallet=wallet,
            provider=Payment.Provider.PAYSTACK,
            reference=reference,
            amount=amount,
            status=Payment.Status.PENDING,
            description="Wallet funding",
        )

    def test_unauthenticated_user_cannot_view_payments(self):
        response = self.client.get(
            "/api/payments/"
        )

        self.assertEqual(
            response.status_code,
            401,
        )

    def test_authenticated_user_can_view_own_payments(self):
        payment = self.create_payment(
            user=self.user_a,
            wallet=self.wallet_a,
            reference="PAY-API-A-001",
        )

        self.authenticate(self.user_a)

        response = self.client.get(
            "/api/payments/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        references = [
            item["reference"]
            for item in response.data
        ]

        self.assertIn(
            payment.reference,
            references,
        )

    def test_user_cannot_view_another_users_payments(self):
        self.create_payment(
            user=self.user_a,
            wallet=self.wallet_a,
            reference="PAY-API-A-002",
        )

        self.create_payment(
            user=self.user_b,
            wallet=self.wallet_b,
            reference="PAY-API-B-001",
        )

        self.authenticate(self.user_a)

        response = self.client.get(
            "/api/payments/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        references = [
            item["reference"]
            for item in response.data
        ]

        self.assertIn(
            "PAY-API-A-002",
            references,
        )

        self.assertNotIn(
            "PAY-API-B-001",
            references,
        )

    def test_user_with_no_payments_gets_empty_list(self):
        self.authenticate(self.user_a)

        response = self.client.get(
            "/api/payments/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data,
            [],
        )

    def test_payments_are_ordered_newest_first(self):
        self.create_payment(
            user=self.user_a,
            wallet=self.wallet_a,
            reference="PAY-API-OLDER",
        )

        self.create_payment(
            user=self.user_a,
            wallet=self.wallet_a,
            reference="PAY-API-NEWER",
        )

        self.authenticate(self.user_a)

        response = self.client.get(
            "/api/payments/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        references = [
            item["reference"]
            for item in response.data
        ]

        self.assertEqual(
            references[0],
            "PAY-API-NEWER",
        )

        self.assertEqual(
            references[1],
            "PAY-API-OLDER",
        )

    def test_user_cannot_access_payment_using_another_users_reference(self):
        self.create_payment(
            user=self.user_b,
            wallet=self.wallet_b,
            reference="PAY-PRIVATE-B",
        )

        self.authenticate(self.user_a)

        response = self.client.get(
            "/api/payments/PAY-PRIVATE-B/"
        )

        self.assertEqual(
            response.status_code,
            404,
        )

    def test_payment_response_does_not_expose_user_or_wallet(self):
        self.create_payment(
            user=self.user_a,
            wallet=self.wallet_a,
            reference="PAY-API-A-003",
        )

        self.authenticate(self.user_a)

        response = self.client.get(
            "/api/payments/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        payment = response.data[0]

        self.assertNotIn(
            "user",
            payment,
        )

        self.assertNotIn(
            "wallet",
            payment,
        )

    def test_payment_api_does_not_allow_posting_payment_directly(self):
        self.authenticate(self.user_a)

        response = self.client.post(
            "/api/payments/",
            {
                "provider": Payment.Provider.PAYSTACK,
                "reference": "PAY-FORGED-001",
                "amount": 100_000,
                "status": Payment.Status.SUCCESS,
            },
            format="json",
        )

        self.assertIn(
            response.status_code,
            [405, 400],
        )

        self.assertFalse(
            Payment.objects.filter(
                reference="PAY-FORGED-001",
            ).exists()
        )

    def test_payment_api_does_not_allow_user_to_modify_payment(self):
        payment = self.create_payment(
            user=self.user_a,
            wallet=self.wallet_a,
            reference="PAY-API-A-004",
        )

        self.authenticate(self.user_a)

        response = self.client.patch(
            f"/api/payments/{payment.reference}/",
            {
                "status": Payment.Status.SUCCESS,
                "amount": 999_999,
            },
            format="json",
        )

        self.assertIn(
            response.status_code,
            [405, 404],
        )

        payment.refresh_from_db()

        self.assertEqual(
            payment.status,
            Payment.Status.PENDING,
        )

        self.assertEqual(
            payment.amount,
            5_000,
        )