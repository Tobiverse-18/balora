from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from users.models import User
from agents.models import Agent
from wallets.models import Wallet


class AgentProfileAPITests(TestCase):

    def setUp(self):
        self.client = APIClient()

        self.user_a = User.objects.create_user(
            email="agentprofilea@balora.com",
            phone_number="08000000071",
            password="TestPassword123!",
        )

        self.user_b = User.objects.create_user(
            email="agentprofileb@balora.com",
            phone_number="08000000072",
            password="TestPassword123!",
        )

        self.wallet_a = Wallet.objects.create(
            user=self.user_a,
        )

        self.wallet_b = Wallet.objects.create(
            user=self.user_b,
        )

        self.agent_a = Agent.objects.create(
            user=self.user_a,
            business_name="Agent A Store",
            agent_code="BAL-PROFILE-001",
            status=Agent.Status.PENDING,
            commission_rate="5.00",
        )

        self.agent_b = Agent.objects.create(
            user=self.user_b,
            business_name="Agent B Store",
            agent_code="BAL-PROFILE-002",
            status=Agent.Status.ACTIVE,
            commission_rate="10.00",
        )

    def authenticate(self, user):
        refresh = RefreshToken.for_user(user)

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}"
        )

    def test_unauthenticated_user_cannot_view_agent_profile(self):
        response = self.client.get(
            "/api/agents/me/"
        )

        self.assertEqual(
            response.status_code,
            401,
        )

    def test_authenticated_user_can_view_own_agent_profile(self):
        self.authenticate(self.user_a)

        response = self.client.get(
            "/api/agents/me/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data["business_name"],
            "Agent A Store",
        )

        self.assertEqual(
            response.data["agent_code"],
            "BAL-PROFILE-001",
        )

        self.assertEqual(
            response.data["status"],
            Agent.Status.PENDING,
        )

        self.assertEqual(
            response.data["commission_rate"],
            "5.00",
        )

    def test_user_cannot_view_another_users_agent_profile(self):
        self.authenticate(self.user_a)

        response = self.client.get(
            "/api/agents/me/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertNotEqual(
            response.data["agent_code"],
            self.agent_b.agent_code,
        )

        self.assertNotEqual(
            response.data["business_name"],
            self.agent_b.business_name,
        )

    def test_profile_returns_only_authenticated_users_agent(self):
        self.authenticate(self.user_a)

        response = self.client.get(
            "/api/agents/me/"
        )

        self.assertEqual(
            response.data["agent_code"],
            self.agent_a.agent_code,
        )

        self.assertNotEqual(
            response.data["agent_code"],
            self.agent_b.agent_code,
        )

    def test_customer_without_agent_profile_gets_404(self):
        user = User.objects.create_user(
            email="customeronly@balora.com",
            phone_number="08000000073",
            password="TestPassword123!",
        )

        Wallet.objects.create(
            user=user,
        )

        self.authenticate(user)

        response = self.client.get(
            "/api/agents/me/"
        )

        self.assertEqual(
            response.status_code,
            404,
        )

    def test_agent_profile_does_not_expose_user_password(self):
        self.authenticate(self.user_a)

        response = self.client.get(
            "/api/agents/me/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertNotIn(
            "password",
            response.data,
        )

    def test_agent_profile_does_not_expose_wallet_balance(self):
        self.wallet_a.balance = 50_000
        self.wallet_a.save()

        self.authenticate(self.user_a)

        response = self.client.get(
            "/api/agents/me/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertNotIn(
            "balance",
            response.data,
        )

    def test_pending_agent_can_view_profile(self):
        self.authenticate(self.user_a)

        response = self.client.get(
            "/api/agents/me/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data["status"],
            Agent.Status.PENDING,
        )

    def test_active_agent_can_view_profile(self):
        self.authenticate(self.user_b)

        response = self.client.get(
            "/api/agents/me/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data["status"],
            Agent.Status.ACTIVE,
        )