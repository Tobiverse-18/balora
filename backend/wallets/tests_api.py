from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from users.models import User
from wallets.models import Wallet


class WalletAPITests(APITestCase):
    def setUp(self):
        self.user_a = User.objects.create_user(
            email="usera@balora.com",
            phone_number="08000000011",
            password="TestPassword123!",
        )

        self.user_b = User.objects.create_user(
            email="userb@balora.com",
            phone_number="08000000012",
            password="TestPassword123!",
        )

        self.wallet_a = Wallet.objects.create(
            user=self.user_a,
            balance=1_000_000,
        )

        self.wallet_b = Wallet.objects.create(
            user=self.user_b,
            balance=2_000_000,
        )

        self.url = reverse("my-wallet")

    def test_wallet_requires_authentication(self):
        response = self.client.get(self.url)

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_user_can_only_view_own_wallet(self):
        self.client.force_authenticate(user=self.user_a)

        response = self.client.get(self.url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["id"],
            self.wallet_a.id,
        )

        self.assertEqual(
            response.data["balance"],
            1_000_000,
        )

    def test_user_b_gets_user_b_wallet(self):
        self.client.force_authenticate(user=self.user_b)

        response = self.client.get(self.url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["id"],
            self.wallet_b.id,
        )

        self.assertEqual(
            response.data["balance"],
            2_000_000,
        )

    def test_wallet_endpoint_does_not_allow_post(self):
        self.client.force_authenticate(user=self.user_a)

        response = self.client.post(
            self.url,
            {
                "balance": 999_999_999,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def test_wallet_endpoint_does_not_allow_patch(self):
        self.client.force_authenticate(user=self.user_a)

        response = self.client.patch(
            self.url,
            {
                "balance": 999_999_999,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def test_wallet_endpoint_does_not_allow_delete(self):
        self.client.force_authenticate(user=self.user_a)

        response = self.client.delete(self.url)

        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )