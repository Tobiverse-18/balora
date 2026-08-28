from decimal import Decimal

from django.db import IntegrityError
from django.test import TestCase

from users.models import User
from agents.models import Agent


class AgentModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="agenttest@balora.com",
            phone_number="08000000051",
            password="TestPassword123!",
        )

    def test_agent_can_be_created(self):
        agent = Agent.objects.create(
            user=self.user,
            business_name="Test Business",
            agent_code="BAL-AGENT-001",
            commission_rate=Decimal("5.00"),
        )

        self.assertEqual(
            agent.user,
            self.user,
        )

        self.assertEqual(
            agent.business_name,
            "Test Business",
        )

        self.assertEqual(
            agent.agent_code,
            "BAL-AGENT-001",
        )

        self.assertEqual(
            agent.status,
            Agent.Status.PENDING,
        )

        self.assertEqual(
            agent.commission_rate,
            Decimal("5.00"),
        )

    def test_agent_is_connected_to_user(self):
        agent = Agent.objects.create(
            user=self.user,
            business_name="Test Business",
            agent_code="BAL-AGENT-002",
            commission_rate=Decimal("5.00"),
        )

        self.assertEqual(
            self.user.agent,
            agent,
        )

    def test_agent_code_must_be_unique(self):
        Agent.objects.create(
            user=self.user,
            business_name="First Business",
            agent_code="BAL-AGENT-003",
            commission_rate=Decimal("5.00"),
        )

        another_user = User.objects.create_user(
            email="anotheragent@balora.com",
            phone_number="08000000052",
            password="TestPassword123!",
        )

        with self.assertRaises(IntegrityError):
            Agent.objects.create(
                user=another_user,
                business_name="Second Business",
                agent_code="BAL-AGENT-003",
                commission_rate=Decimal("5.00"),
            )

    def test_user_can_only_have_one_agent(self):
        Agent.objects.create(
            user=self.user,
            business_name="First Business",
            agent_code="BAL-AGENT-004",
            commission_rate=Decimal("5.00"),
        )

        with self.assertRaises(IntegrityError):
            Agent.objects.create(
                user=self.user,
                business_name="Second Business",
                agent_code="BAL-AGENT-005",
                commission_rate=Decimal("5.00"),
            )

    def test_default_status_is_pending(self):
        agent = Agent.objects.create(
            user=self.user,
            business_name="Pending Business",
            agent_code="BAL-AGENT-006",
            commission_rate=Decimal("5.00"),
        )

        self.assertEqual(
            agent.status,
            Agent.Status.PENDING,
        )

    def test_default_commission_is_zero(self):
        agent = Agent.objects.create(
            user=self.user,
            business_name="Zero Commission Business",
            agent_code="BAL-AGENT-007",
        )

        self.assertEqual(
            agent.commission_rate,
            Decimal("0.00"),
        )

    def test_commission_rate_cannot_exceed_100(self):
        agent = Agent(
            user=self.user,
            business_name="Invalid Commission Business",
            agent_code="BAL-AGENT-008",
            commission_rate=Decimal("101.00"),
        )

        with self.assertRaises(Exception):
            agent.full_clean()