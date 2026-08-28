from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from users.models import User
from agents.models import Agent
from wallets.models import Wallet


class AgentApplicationAPITests(TestCase):

    def setUp(self):
        self.client = APIClient()

        self.user = User.objects.create_user(
            email="agentapplicant@balora.com",
            phone_number="08000000061",
            password="TestPassword123!",
        )

        self.wallet = Wallet.objects.create(
            user=self.user,
            balance=10_000,
        )

    def authenticate(self, user):
        refresh = RefreshToken.for_user(user)

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}"
        )

    def test_unauthenticated_user_cannot_apply(self):
        response = self.client.post(
            "/api/agents/apply/",
            {
                "business_name": "Unauthenticated Store",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            401,
        )

    def test_authenticated_customer_can_apply(self):
        self.authenticate(self.user)

        response = self.client.post(
            "/api/agents/apply/",
            {
                "business_name": "Balora Test Store",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        self.assertEqual(
            response.data["business_name"],
            "Balora Test Store",
        )

        self.assertEqual(
            response.data["status"],
            Agent.Status.PENDING,
        )

        self.assertEqual(
            response.data["commission_rate"],
            "0.00",
        )

        self.assertEqual(
            response.data["agent_code"],
            f"BAL-{self.user.id:06d}",
        )

    def test_application_does_not_change_user_role(self):
        self.authenticate(self.user)

        response = self.client.post(
            "/api/agents/apply/",
            {
                "business_name": "Balora Test Store",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        self.user.refresh_from_db()

        self.assertEqual(
            self.user.role,
            User.Role.CUSTOMER,
        )

    def test_application_does_not_change_wallet_balance(self):
        self.authenticate(self.user)

        response = self.client.post(
            "/api/agents/apply/",
            {
                "business_name": "Balora Test Store",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        self.wallet.refresh_from_db()

        self.assertEqual(
            self.wallet.balance,
            10_000,
        )

    def test_business_name_is_required(self):
        self.authenticate(self.user)

        response = self.client.post(
            "/api/agents/apply/",
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertIn(
            "business_name",
            response.data,
        )

    def test_business_name_cannot_be_blank(self):
        self.authenticate(self.user)

        response = self.client.post(
            "/api/agents/apply/",
            {
                "business_name": "   ",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertIn(
            "business_name",
            response.data,
        )

    def test_user_cannot_submit_second_application(self):
        self.authenticate(self.user)

        first_response = self.client.post(
            "/api/agents/apply/",
            {
                "business_name": "First Store",
            },
            format="json",
        )

        self.assertEqual(
            first_response.status_code,
            201,
        )

        second_response = self.client.post(
            "/api/agents/apply/",
            {
                "business_name": "Second Store",
            },
            format="json",
        )

        self.assertEqual(
            second_response.status_code,
            400,
        )

        self.assertEqual(
            Agent.objects.filter(
                user=self.user
            ).count(),
            1,
        )

    def test_client_cannot_make_themselves_active(self):
        self.authenticate(self.user)

        response = self.client.post(
            "/api/agents/apply/",
            {
                "business_name": "Balora Test Store",
                "status": "ACTIVE",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        self.assertEqual(
            response.data["status"],
            Agent.Status.PENDING,
        )

    def test_client_cannot_set_commission_rate(self):
        self.authenticate(self.user)

        response = self.client.post(
            "/api/agents/apply/",
            {
                "business_name": "Balora Test Store",
                "commission_rate": "99.00",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        self.assertEqual(
            response.data["commission_rate"],
            "0.00",
        )

    def test_client_cannot_choose_agent_code(self):
        self.authenticate(self.user)

        response = self.client.post(
            "/api/agents/apply/",
            {
                "business_name": "Balora Test Store",
                "agent_code": "HACKED-CODE",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        self.assertEqual(
            response.data["agent_code"],
            f"BAL-{self.user.id:06d}",
        )