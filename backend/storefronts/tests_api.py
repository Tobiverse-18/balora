from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from agents.models import Agent
from users.models import User
from storefronts.models import Storefront


class StorefrontAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.customer = User.objects.create_user(
            email="storecustomer@balora.com",
            phone_number="08000000071",
            password="TestPassword123!",
        )

        self.agent_user = User.objects.create_user(
            email="storeagent@balora.com",
            phone_number="08000000072",
            password="TestPassword123!",
        )

        self.other_agent_user = User.objects.create_user(
            email="otherstoreagent@balora.com",
            phone_number="08000000073",
            password="TestPassword123!",
        )

        self.agent = Agent.objects.create(
            user=self.agent_user,
            business_name="Store Agent Business",
            agent_code="BAL-STORE-AGENT-001",
            commission_rate="5.00",
        )

        self.other_agent = Agent.objects.create(
            user=self.other_agent_user,
            business_name="Other Agent Business",
            agent_code="BAL-STORE-AGENT-002",
            commission_rate="5.00",
        )

    def authenticate(self, user):
        refresh = RefreshToken.for_user(user)

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}"
        )

    def test_unauthenticated_user_cannot_access_storefront(self):
        response = self.client.get(
            "/api/storefronts/me/"
        )

        self.assertEqual(
            response.status_code,
            401,
        )

    def test_customer_cannot_create_storefront(self):
        self.authenticate(self.customer)

        response = self.client.post(
            "/api/storefronts/me/",
            {
                "name": "Customer Store",
                "slug": "customer-store",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            404,
        )

        self.assertEqual(
            Storefront.objects.count(),
            0,
        )

    def test_agent_can_create_storefront(self):
        self.authenticate(self.agent_user)

        response = self.client.post(
            "/api/storefronts/me/",
            {
                "name": "My Agent Store",
                "slug": "my-agent-store",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        self.assertEqual(
            response.data["name"],
            "My Agent Store",
        )

        self.assertEqual(
            response.data["slug"],
            "my-agent-store",
        )

        self.assertEqual(
            response.data["agent_code"],
            "BAL-STORE-AGENT-001",
        )

        self.assertEqual(
            Storefront.objects.count(),
            1,
        )

    def test_agent_can_view_own_storefront(self):
        Storefront.objects.create(
            agent=self.agent,
            name="My Store",
            slug="my-store",
        )

        self.authenticate(self.agent_user)

        response = self.client.get(
            "/api/storefronts/me/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data["name"],
            "My Store",
        )

        self.assertEqual(
            response.data["slug"],
            "my-store",
        )

    def test_agent_cannot_view_another_agents_storefront(self):
        Storefront.objects.create(
            agent=self.other_agent,
            name="Other Agent Store",
            slug="other-agent-store",
        )

        self.authenticate(self.agent_user)

        response = self.client.get(
            "/api/storefronts/me/"
        )

        self.assertEqual(
            response.status_code,
            404,
        )

    def test_agent_can_update_own_storefront(self):
        Storefront.objects.create(
            agent=self.agent,
            name="Original Store",
            slug="original-store",
        )

        self.authenticate(self.agent_user)

        response = self.client.patch(
            "/api/storefronts/me/",
            {
                "name": "Updated Store",
                "slug": "updated-store",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data["name"],
            "Updated Store",
        )

        self.assertEqual(
            response.data["slug"],
            "updated-store",
        )

    def test_agent_cannot_update_another_agents_storefront(self):
        Storefront.objects.create(
            agent=self.other_agent,
            name="Other Store",
            slug="other-store",
        )

        self.authenticate(self.agent_user)

        response = self.client.patch(
            "/api/storefronts/me/",
            {
                "name": "Hacked Store",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            404,
        )

        storefront = Storefront.objects.get(
            agent=self.other_agent,
        )

        self.assertEqual(
            storefront.name,
            "Other Store",
        )

    def test_agent_cannot_create_second_storefront(self):
        Storefront.objects.create(
            agent=self.agent,
            name="First Store",
            slug="first-store",
        )

        self.authenticate(self.agent_user)

        response = self.client.post(
            "/api/storefronts/me/",
            {
                "name": "Second Store",
                "slug": "second-store",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertEqual(
            Storefront.objects.filter(
                agent=self.agent
            ).count(),
            1,
        )

    def test_agent_cannot_change_agent_code(self):
        Storefront.objects.create(
            agent=self.agent,
            name="My Store",
            slug="my-store",
        )

        self.authenticate(self.agent_user)

        response = self.client.patch(
            "/api/storefronts/me/",
            {
                "agent_code": "HACKED-CODE",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data["agent_code"],
            "BAL-STORE-AGENT-001",
        )

        self.assertEqual(
            self.agent.agent_code,
            "BAL-STORE-AGENT-001",
        )

    def test_agent_cannot_change_agent_status(self):
        Storefront.objects.create(
            agent=self.agent,
            name="My Store",
            slug="my-store",
        )

        self.authenticate(self.agent_user)

        response = self.client.patch(
            "/api/storefronts/me/",
            {
                "agent_status": Agent.Status.ACTIVE,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data["agent_status"],
            Agent.Status.PENDING,
        )

        self.agent.refresh_from_db()

        self.assertEqual(
            self.agent.status,
            Agent.Status.PENDING,
        )

    def test_agent_cannot_assign_storefront_to_another_agent(self):
        self.authenticate(self.agent_user)

        response = self.client.post(
            "/api/storefronts/me/",
            {
                "name": "Attack Store",
                "slug": "attack-store",
                "agent": self.other_agent.id,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        storefront = Storefront.objects.get(
            slug="attack-store",
        )

        self.assertEqual(
            storefront.agent,
            self.agent,
        )

        self.assertNotEqual(
            storefront.agent,
            self.other_agent,
        )