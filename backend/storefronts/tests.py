from django.test import TestCase

from agents.models import Agent
from users.models import User
from storefronts.models import Storefront


class StorefrontModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="storefronttest@balora.com",
            phone_number="08000000051",
            password="TestPassword123!",
        )

        self.agent = Agent.objects.create(
            user=self.user,
            business_name="Storefront Test Business",
            agent_code="BAL-STORE-001",
            commission_rate="5.00",
        )

    def test_storefront_can_be_created(self):
        storefront = Storefront.objects.create(
            agent=self.agent,
            name="Storefront Test Business",
            slug="storefront-test-business",
        )

        self.assertEqual(
            storefront.agent,
            self.agent,
        )

        self.assertEqual(
            storefront.name,
            "Storefront Test Business",
        )

        self.assertEqual(
            storefront.slug,
            "storefront-test-business",
        )

        self.assertTrue(
            storefront.is_active,
        )

    def test_storefront_defaults_to_active(self):
        storefront = Storefront.objects.create(
            agent=self.agent,
            name="Active Store",
            slug="active-store",
        )

        self.assertTrue(
            storefront.is_active,
        )

    def test_storefront_has_one_to_one_agent_relationship(self):
        Storefront.objects.create(
            agent=self.agent,
            name="My Store",
            slug="my-store",
        )

        with self.assertRaises(Exception):
            Storefront.objects.create(
                agent=self.agent,
                name="Another Store",
                slug="another-store",
            )

    def test_storefront_string_representation(self):
        storefront = Storefront.objects.create(
            agent=self.agent,
            name="My Store",
            slug="my-store",
        )

        self.assertEqual(
            str(storefront),
            "My Store - my-store",
        )