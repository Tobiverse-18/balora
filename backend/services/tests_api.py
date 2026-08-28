from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from services.models import Service
from users.models import User


class ServiceAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.customer = User.objects.create_user(
            email="servicecustomer@balora.com",
            phone_number="08000000081",
            password="TestPassword123!",
        )

        self.agent = User.objects.create_user(
            email="serviceagent@balora.com",
            phone_number="08000000082",
            password="TestPassword123!",
        )

        self.airtime = Service.objects.create(
            name="Airtime",
            service_type=Service.ServiceType.AIRTIME,
            description="Purchase airtime.",
        )

        self.data = Service.objects.create(
            name="Data",
            service_type=Service.ServiceType.DATA,
            description="Purchase mobile data.",
        )

        self.inactive_service = Service.objects.create(
            name="Electricity",
            service_type=Service.ServiceType.ELECTRICITY,
            description="Pay electricity bills.",
            is_active=False,
        )

    def authenticate(self, user):
        refresh = RefreshToken.for_user(user)

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}"
        )

    def test_unauthenticated_user_can_view_services(self):
        response = self.client.get(
            "/api/services/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

    def test_customer_can_view_services(self):
        self.authenticate(self.customer)

        response = self.client.get(
            "/api/services/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

    def test_agent_can_view_services(self):
        self.authenticate(self.agent)

        response = self.client.get(
            "/api/services/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

    def test_only_active_services_are_returned(self):
        response = self.client.get(
            "/api/services/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        names = [
            service["name"]
            for service in response.data
        ]

        self.assertIn(
            "Airtime",
            names,
        )

        self.assertIn(
            "Data",
            names,
        )

        self.assertNotIn(
            "Electricity",
            names,
        )

    def test_services_are_ordered_by_name(self):
        response = self.client.get(
            "/api/services/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        names = [
            service["name"]
            for service in response.data
        ]

        self.assertEqual(
            names,
            sorted(names),
        )

    def test_service_response_contains_expected_fields(self):
        response = self.client.get(
            "/api/services/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        service = response.data[0]

        expected_fields = {
            "id",
            "name",
            "service_type",
            "description",
            "is_active",
            "created_at",
            "updated_at",
        }

        self.assertEqual(
            set(service.keys()),
            expected_fields,
        )