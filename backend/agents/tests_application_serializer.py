from django.test import TestCase
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIRequestFactory

from users.models import User
from agents.models import Agent
from agents.serializers import AgentApplicationSerializer


class AgentApplicationSerializerTests(TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()

        self.user = User.objects.create_user(
            email="applicant@balora.com",
            phone_number="08000000051",
            password="TestPassword123!",
        )

        request = self.factory.post("/api/agents/apply/")

        request.user = self.user

        self.context = {
            "request": request,
        }

    def test_application_creates_pending_agent(self):
        serializer = AgentApplicationSerializer(
            data={
                "business_name": "Balora Test Store",
            },
            context=self.context,
        )

        self.assertTrue(
            serializer.is_valid(),
            serializer.errors,
        )

        agent = serializer.save()

        self.assertEqual(
            agent.business_name,
            "Balora Test Store",
        )

        self.assertEqual(
            agent.status,
            Agent.Status.PENDING,
        )

        self.assertEqual(
            agent.commission_rate,
            0,
        )

        self.assertEqual(
            agent.user,
            self.user,
        )

    def test_application_generates_agent_code(self):
        serializer = AgentApplicationSerializer(
            data={
                "business_name": "Balora Test Store",
            },
            context=self.context,
        )

        self.assertTrue(
            serializer.is_valid(),
            serializer.errors,
        )

        agent = serializer.save()

        self.assertEqual(
            agent.agent_code,
            f"BAL-{self.user.id:06d}",
        )

    def test_business_name_is_required(self):
        serializer = AgentApplicationSerializer(
            data={},
            context=self.context,
        )

        self.assertFalse(
            serializer.is_valid(),
        )

        self.assertIn(
            "business_name",
            serializer.errors,
        )

    def test_business_name_cannot_be_blank(self):
        serializer = AgentApplicationSerializer(
            data={
                "business_name": "   ",
            },
            context=self.context,
        )

        self.assertFalse(
            serializer.is_valid(),
        )

        self.assertIn(
            "business_name",
            serializer.errors,
        )

    def test_user_cannot_create_second_agent_profile(self):
        Agent.objects.create(
            user=self.user,
            business_name="Existing Store",
            agent_code=f"BAL-{self.user.id:06d}",
        )

        serializer = AgentApplicationSerializer(
            data={
                "business_name": "Second Store",
            },
            context=self.context,
        )

        self.assertTrue(
            serializer.is_valid(),
            serializer.errors,
        )

        with self.assertRaises(ValidationError):
            serializer.save()

    def test_application_does_not_change_user_role(self):
        serializer = AgentApplicationSerializer(
            data={
                "business_name": "Balora Test Store",
            },
            context=self.context,
        )

        self.assertTrue(
            serializer.is_valid(),
            serializer.errors,
        )

        serializer.save()

        self.user.refresh_from_db()

        self.assertEqual(
            self.user.role,
            User.Role.CUSTOMER,
        )

    def test_client_cannot_set_agent_status(self):
        serializer = AgentApplicationSerializer(
            data={
                "business_name": "Balora Test Store",
                "status": Agent.Status.ACTIVE,
            },
            context=self.context,
        )

        self.assertTrue(
            serializer.is_valid(),
            serializer.errors,
        )

        agent = serializer.save()

        self.assertEqual(
            agent.status,
            Agent.Status.PENDING,
        )

    def test_client_cannot_set_commission_rate(self):
        serializer = AgentApplicationSerializer(
            data={
                "business_name": "Balora Test Store",
                "commission_rate": "99.00",
            },
            context=self.context,
        )

        self.assertTrue(
            serializer.is_valid(),
            serializer.errors,
        )

        agent = serializer.save()

        self.assertEqual(
            agent.commission_rate,
            0,
        )