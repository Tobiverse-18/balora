from django.test import TestCase

from users.models import User
from agents.models import Agent
from agents.serializers import AgentSerializer


class AgentSerializerTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email="serializer@balora.com",
            phone_number="08000000031",
            password="TestPassword123!",
        )

        self.agent = Agent.objects.create(
            user=self.user,
            business_name="Serializer Test Store",
            agent_code="BAL-SERIALIZER-001",
            commission_rate="5.00",
        )

    def test_agent_serializer_returns_expected_fields(self):
        serializer = AgentSerializer(self.agent)

        self.assertEqual(
            set(serializer.data.keys()),
            {
                "id",
                "business_name",
                "agent_code",
                "status",
                "commission_rate",
                "created_at",
                "updated_at",
            },
        )

    def test_agent_code_is_read_only(self):
        serializer = AgentSerializer(self.agent)

        self.assertIn(
            "agent_code",
            serializer.Meta.read_only_fields,
        )

    def test_status_is_read_only(self):
        serializer = AgentSerializer(self.agent)

        self.assertIn(
            "status",
            serializer.Meta.read_only_fields,
        )

    def test_commission_rate_is_read_only(self):
        serializer = AgentSerializer(self.agent)

        self.assertIn(
            "commission_rate",
            serializer.Meta.read_only_fields,
        )

    def test_id_is_read_only(self):
        serializer = AgentSerializer(self.agent)

        self.assertIn(
            "id",
            serializer.Meta.read_only_fields,
        )

    def test_created_at_is_read_only(self):
        serializer = AgentSerializer(self.agent)

        self.assertIn(
            "created_at",
            serializer.Meta.read_only_fields,
        )

    def test_updated_at_is_read_only(self):
        serializer = AgentSerializer(self.agent)

        self.assertIn(
            "updated_at",
            serializer.Meta.read_only_fields,
        )