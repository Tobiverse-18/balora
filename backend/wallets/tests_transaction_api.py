from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from users.models import User
from wallets.models import Transaction, Wallet


class TransactionHistoryAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.user_a = User.objects.create_user(
            email="customerA@balora.com",
            phone_number="08000000041",
            password="TestPassword123!",
        )

        self.user_b = User.objects.create_user(
            email="customerB@balora.com",
            phone_number="08000000042",
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

    def test_unauthenticated_user_cannot_view_transactions(self):
        response = self.client.get(
            "/api/wallet/transactions/"
        )

        self.assertEqual(
            response.status_code,
            401,
        )

    def test_authenticated_user_can_view_own_transactions(self):
        Transaction.objects.create(
            wallet=self.wallet_a,
            transaction_type=Transaction.TransactionType.AIRTIME,
            status=Transaction.Status.SUCCESS,
            amount=1_000,
            reference="TX-A-001",
            description="Customer A airtime",
        )

        self.authenticate(self.user_a)

        response = self.client.get(
            "/api/wallet/transactions/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data["count"],
            1,
        )

        self.assertEqual(
            len(response.data["results"]),
            1,
        )

        self.assertEqual(
            response.data["results"][0]["reference"],
            "TX-A-001",
        )

    def test_user_cannot_see_another_users_transactions(self):
        Transaction.objects.create(
            wallet=self.wallet_a,
            transaction_type=Transaction.TransactionType.AIRTIME,
            status=Transaction.Status.SUCCESS,
            amount=1_000,
            reference="TX-A-002",
            description="Customer A transaction",
        )

        Transaction.objects.create(
            wallet=self.wallet_b,
            transaction_type=Transaction.TransactionType.DATA,
            status=Transaction.Status.SUCCESS,
            amount=2_000,
            reference="TX-B-001",
            description="Customer B transaction",
        )

        self.authenticate(self.user_a)

        response = self.client.get(
            "/api/wallet/transactions/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        references = [
            transaction["reference"]
            for transaction in response.data["results"]
        ]

        self.assertIn(
            "TX-A-002",
            references,
        )

        self.assertNotIn(
            "TX-B-001",
            references,
        )

    def test_user_with_no_transactions_gets_empty_list(self):
        self.authenticate(self.user_a)

        response = self.client.get(
            "/api/wallet/transactions/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data["count"],
            0,
        )

        self.assertEqual(
            response.data["results"],
            [],
        )

    def test_transactions_are_ordered_newest_first(self):
        Transaction.objects.create(
            wallet=self.wallet_a,
            transaction_type=Transaction.TransactionType.AIRTIME,
            status=Transaction.Status.SUCCESS,
            amount=1_000,
            reference="TX-OLDER",
            description="Older transaction",
        )

        Transaction.objects.create(
            wallet=self.wallet_a,
            transaction_type=Transaction.TransactionType.DATA,
            status=Transaction.Status.SUCCESS,
            amount=2_000,
            reference="TX-NEWER",
            description="Newer transaction",
        )

        self.authenticate(self.user_a)

        response = self.client.get(
            "/api/wallet/transactions/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data["results"][0]["reference"],
            "TX-NEWER",
        )

        self.assertEqual(
            response.data["results"][1]["reference"],
            "TX-OLDER",
        )

    def test_wallet_id_does_not_allow_access_to_another_users_transactions(self):
        Transaction.objects.create(
            wallet=self.wallet_b,
            transaction_type=Transaction.TransactionType.AIRTIME,
            status=Transaction.Status.SUCCESS,
            amount=5_000,
            reference="TX-B-ATTACK",
            description="Private customer B transaction",
        )

        self.authenticate(self.user_a)

        response = self.client.get(
            f"/api/wallet/transactions/?wallet_id={self.wallet_b.id}"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        references = [
            transaction["reference"]
            for transaction in response.data["results"]
        ]

        self.assertNotIn(
            "TX-B-ATTACK",
            references,
        )