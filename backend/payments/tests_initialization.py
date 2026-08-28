from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from payments.models import Payment
from users.models import User
from wallets.models import Wallet


class PaymentInitializationTests(TestCase):

    def setUp(self):
        self.client = APIClient()

        self.user = User.objects.create_user(
            email="funding@balora.com",
            phone_number="08000000131",
            password="TestPassword123!",
        )

        self.wallet = Wallet.objects.create(
            user=self.user,
            balance=10_000,
        )

    def authenticate(self):
        refresh = RefreshToken.for_user(self.user)

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}"
        )

    def test_unauthenticated_user_cannot_initialize_payment(self):
        response = self.client.post(
            "/api/payments/initialize/",
            {
                "amount": 5_000,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            401,
        )

    def test_authenticated_user_can_initialize_payment(self):
        self.authenticate()

        response = self.client.post(
            "/api/payments/initialize/",
            {
                "amount": 5_000,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        self.assertIn(
            "reference",
            response.data,
        )

        self.assertIn(
            "amount",
            response.data,
        )

        self.assertIn(
            "status",
            response.data,
        )

        self.assertEqual(
            response.data["amount"],
            5_000,
        )

        self.assertEqual(
            response.data["status"],
            Payment.Status.PENDING,
        )

    def test_initializing_payment_creates_pending_payment(self):
        self.authenticate()

        response = self.client.post(
            "/api/payments/initialize/",
            {
                "amount": 5_000,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        payment = Payment.objects.get(
            reference=response.data["reference"],
        )

        self.assertEqual(
            payment.user,
            self.user,
        )

        self.assertEqual(
            payment.wallet,
            self.wallet,
        )

        self.assertEqual(
            payment.amount,
            5_000,
        )

        self.assertEqual(
            payment.status,
            Payment.Status.PENDING,
        )

        self.assertEqual(
            payment.provider,
            Payment.Provider.PAYSTACK,
        )

    def test_initializing_payment_does_not_change_wallet_balance(self):
        self.authenticate()

        self.client.post(
            "/api/payments/initialize/",
            {
                "amount": 5_000,
            },
            format="json",
        )

        self.wallet.refresh_from_db()

        self.assertEqual(
            self.wallet.balance,
            10_000,
        )

    def test_payment_reference_is_generated(self):
        self.authenticate()

        response = self.client.post(
            "/api/payments/initialize/",
            {
                "amount": 5_000,
            },
            format="json",
        )

        reference = response.data["reference"]

        self.assertTrue(
            reference,
        )

        self.assertTrue(
            Payment.objects.filter(
                reference=reference,
            ).exists()
        )

    def test_each_payment_gets_a_unique_reference(self):
        self.authenticate()

        response_1 = self.client.post(
            "/api/payments/initialize/",
            {
                "amount": 5_000,
            },
            format="json",
        )

        response_2 = self.client.post(
            "/api/payments/initialize/",
            {
                "amount": 5_000,
            },
            format="json",
        )

        self.assertEqual(
            response_1.status_code,
            201,
        )

        self.assertEqual(
            response_2.status_code,
            201,
        )

        self.assertNotEqual(
            response_1.data["reference"],
            response_2.data["reference"],
        )

    def test_amount_is_required(self):
        self.authenticate()

        response = self.client.post(
            "/api/payments/initialize/",
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

    def test_amount_must_be_positive(self):
        self.authenticate()

        response = self.client.post(
            "/api/payments/initialize/",
            {
                "amount": 0,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

    def test_negative_amount_is_rejected(self):
        self.authenticate()

        response = self.client.post(
            "/api/payments/initialize/",
            {
                "amount": -5_000,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        def test_user_cannot_initialize_payment_for_another_wallet(self):
            other_user = User.objects.create_user(
                email="otherfunding@balora.com",
                phone_number="08000000132",
                password="TestPassword123!",
            )

            other_wallet = Wallet.objects.create(
                user=other_user,
                balance=20_000,
            )

            self.authenticate()

            response = self.client.post(
                "/api/payments/initialize/",
                {
                    "amount": 5_000,
                    "wallet": other_wallet.id,
                },
                format="json",
            )

            self.assertEqual(
                response.status_code,
                201,
            )

            payment = Payment.objects.get(
                reference=response.data["reference"],
            )

            self.assertEqual(
                payment.user,
                self.user,
            )

            self.assertEqual(
                payment.wallet,
                self.wallet,
            )

            self.assertNotEqual(
                payment.wallet,
                other_wallet,
            )

    def test_client_cannot_choose_payment_status(self):
        self.authenticate()

        response = self.client.post(
            "/api/payments/initialize/",
            {
                "amount": 5_000,
                "status": Payment.Status.SUCCESS,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        payment = Payment.objects.get(
            reference=response.data["reference"],
        )

        self.assertEqual(
            payment.status,
            Payment.Status.PENDING,
        )

    def test_client_cannot_choose_payment_provider(self):
        self.authenticate()

        response = self.client.post(
            "/api/payments/initialize/",
            {
                "amount": 5_000,
                "provider": Payment.Provider.MONNIFY,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        payment = Payment.objects.get(
            reference=response.data["reference"],
        )

        self.assertEqual(
            payment.provider,
            Payment.Provider.PAYSTACK,
        )

    def test_client_cannot_choose_payment_user(self):
        other_user = User.objects.create_user(
            email="hacker@balora.com",
            phone_number="08000000133",
            password="TestPassword123!",
        )

        self.authenticate()

        response = self.client.post(
            "/api/payments/initialize/",
            {
                "amount": 5_000,
                "user": other_user.id,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        payment = Payment.objects.get(
            reference=response.data["reference"],
        )

        self.assertEqual(
            payment.user,
            self.user,
        )