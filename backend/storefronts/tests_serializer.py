from django.test import TestCase

from agents.models import Agent
from users.models import User
from wallets.models import Wallet
from storefronts.models import Storefront
from storefronts.serializers import StorefrontSerializer


class StorefrontSerializerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="serializerstore@balora.com",
            phone_number="08000000061",
            password="TestPassword123!",
        )

        self.agent = Agent.objects.create(
            user=self.user,
            business_name="Serializer Store",
            agent_code="BAL-SERIALIZER-001",
            commission_rate="5.00",
        )

        self.wallet = Wallet.objects.create(
            user=self.user,
        )

        self.storefront = Storefront.objects.create(
            agent=self.agent,
            name="Serializer Store",
            slug="serializer-store",
        )

    def test_serializer_returns_storefront_data(self):
        serializer = StorefrontSerializer(
            self.storefront,
        )

        self.assertEqual(
            serializer.data["id"],
            self.storefront.id,
        )

        self.assertEqual(
            serializer.data["name"],
            "Serializer Store",
        )

        self.assertEqual(
            serializer.data["slug"],
            "serializer-store",
        )

        self.assertTrue(
            serializer.data["is_active"],
        )

    def test_serializer_returns_agent_code(self):
        serializer = StorefrontSerializer(
            self.storefront,
        )

        self.assertEqual(
            serializer.data["agent_code"],
            "BAL-SERIALIZER-001",
        )

    def test_serializer_returns_agent_status(self):
        serializer = StorefrontSerializer(
            self.storefront,
        )

        self.assertEqual(
            serializer.data["agent_status"],
            Agent.Status.PENDING,
        )

    def test_agent_fields_are_read_only(self):
        serializer = StorefrontSerializer(
            instance=self.storefront,
            data={
                "name": "Updated Store",
                "slug": "updated-store",
                "agent_code": "ATTACK-CODE",
                "agent_status": Agent.Status.ACTIVE,
            },
            partial=True,
        )

        self.assertTrue(
            serializer.is_valid(),
            serializer.errors,
        )

        updated_storefront = serializer.save()

        self.assertEqual(
            updated_storefront.name,
            "Updated Store",
        )

        self.assertEqual(
            updated_storefront.slug,
            "updated-store",
        )

        self.assertEqual(
            updated_storefront.agent,
            self.agent,
        )

        self.assertEqual(
            updated_storefront.agent.agent_code,
            "BAL-SERIALIZER-001",
        )

        self.assertEqual(
            updated_storefront.agent.status,
            Agent.Status.PENDING,
        )

    def test_id_and_timestamps_are_read_only(self):
        serializer = StorefrontSerializer(
            instance=self.storefront,
            data={
                "id": 9999,
                "name": "Timestamp Test Store",
                "slug": "timestamp-test-store",
                "created_at": "2000-01-01T00:00:00Z",
                "updated_at": "2000-01-01T00:00:00Z",
            },
            partial=True,
        )

        self.assertTrue(
            serializer.is_valid(),
            serializer.errors,
        )

        updated_storefront = serializer.save()

        self.assertNotEqual(
            updated_storefront.id,
            9999,
        )

        self.assertNotEqual(
            str(updated_storefront.created_at),
            "2000-01-01 00:00:00+00:00",
        )

    def test_serializer_does_not_expose_user_password(self):
        serializer = StorefrontSerializer(
            self.storefront,
        )

        self.assertNotIn(
            "password",
            serializer.data,
        )

    def test_serializer_does_not_expose_wallet_balance(self):
        serializer = StorefrontSerializer(
            self.storefront,
        )

        self.assertNotIn(
            "balance",
            serializer.data,
        )

    def test_serializer_requires_name(self):
        serializer = StorefrontSerializer(
            data={
                "slug": "missing-name",
            },
        )

        self.assertFalse(
            serializer.is_valid(),
        )

        self.assertIn(
            "name",
            serializer.errors,
        )

    def test_serializer_requires_slug(self):
        serializer = StorefrontSerializer(
            data={
                "name": "Missing Slug Store",
            },
        )

        self.assertFalse(
            serializer.is_valid(),
        )

        self.assertIn(
            "slug",
            serializer.errors,
        )