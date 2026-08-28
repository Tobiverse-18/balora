from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from services.models import Service, ServiceProduct
from users.models import User


class ServiceProductAPITests(TestCase):

    def setUp(self):
        self.client = APIClient()

        self.customer = User.objects.create_user(
            email="productcustomer@balora.com",
            phone_number="08000000091",
            password="TestPassword123!",
        )

        self.agent = User.objects.create_user(
            email="productagent@balora.com",
            phone_number="08000000092",
            password="TestPassword123!",
        )

        self.data_service = Service.objects.create(
            name="Data",
            service_type=Service.ServiceType.DATA,
            description="Mobile data services.",
        )

        self.cable_service = Service.objects.create(
            name="Cable TV",
            service_type=Service.ServiceType.CABLE,
            description="Cable television services.",
        )

        self.inactive_service = Service.objects.create(
            name="Electricity",
            service_type=Service.ServiceType.ELECTRICITY,
            description="Electricity bill services.",
            is_active=False,
        )

        self.data_product = ServiceProduct.objects.create(
            service=self.data_service,
            name="MTN 10GB",
            code="MTN-DATA-10GB",
            amount=3_000,
            description="MTN 10GB data plan.",
        )

        self.data_product_two = ServiceProduct.objects.create(
            service=self.data_service,
            name="MTN 5GB",
            code="MTN-DATA-5GB",
            amount=2_000,
            description="MTN 5GB data plan.",
        )

        self.cable_product = ServiceProduct.objects.create(
            service=self.cable_service,
            name="DStv Compact",
            code="DSTV-COMPACT",
            amount=12_000,
            description="DStv Compact package.",
        )

        self.inactive_product = ServiceProduct.objects.create(
            service=self.data_service,
            name="MTN Old Plan",
            code="MTN-OLD-PLAN",
            amount=1_000,
            description="Inactive data plan.",
            is_active=False,
        )

        self.product_of_inactive_service = ServiceProduct.objects.create(
            service=self.inactive_service,
            name="Electricity Product",
            code="ELECTRICITY-001",
            amount=5_000,
            description="Inactive service product.",
        )

    def authenticate(self, user):
        refresh = RefreshToken.for_user(user)

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}"
        )

    def test_unauthenticated_user_can_view_products(self):
        response = self.client.get(
            "/api/services/products/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

    def test_customer_can_view_products(self):
        self.authenticate(self.customer)

        response = self.client.get(
            "/api/services/products/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

    def test_agent_can_view_products(self):
        self.authenticate(self.agent)

        response = self.client.get(
            "/api/services/products/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

    def test_only_active_products_are_returned(self):
        response = self.client.get(
            "/api/services/products/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        names = [
            product["name"]
            for product in response.data
        ]

        self.assertIn(
            "MTN 10GB",
            names,
        )

        self.assertIn(
            "MTN 5GB",
            names,
        )

        self.assertIn(
            "DStv Compact",
            names,
        )

        self.assertNotIn(
            "MTN Old Plan",
            names,
        )

    def test_products_of_inactive_services_are_not_returned(self):
        response = self.client.get(
            "/api/services/products/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        names = [
            product["name"]
            for product in response.data
        ]

        self.assertNotIn(
            "Electricity Product",
            names,
        )

    def test_products_are_ordered_by_name(self):
        response = self.client.get(
            "/api/services/products/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        names = [
            product["name"]
            for product in response.data
        ]

        self.assertEqual(
            names,
            sorted(names),
        )

    def test_products_can_be_filtered_by_service(self):
        response = self.client.get(
            f"/api/services/products/?service={self.data_service.id}"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        service_ids = [
            product["service"]
            for product in response.data
        ]

        self.assertEqual(
            set(service_ids),
            {self.data_service.id},
        )

        names = [
            product["name"]
            for product in response.data
        ]

        self.assertIn(
            "MTN 10GB",
            names,
        )

        self.assertIn(
            "MTN 5GB",
            names,
        )

        self.assertNotIn(
            "DStv Compact",
            names,
        )

    def test_filtering_by_another_users_service_does_not_bypass_access_rules(self):
        response = self.client.get(
            f"/api/services/products/?service={self.inactive_service.id}"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data,
            [],
        )

    def test_product_response_contains_expected_fields(self):
        response = self.client.get(
            "/api/services/products/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        product = response.data[0]

        expected_fields = {
            "id",
            "service",
            "name",
            "code",
            "amount",
            "description",
            "is_active",
            "created_at",
            "updated_at",
        }

        self.assertEqual(
            set(product.keys()),
            expected_fields,
        )

    def test_empty_service_filter_returns_empty_list(self):
        response = self.client.get(
            "/api/services/products/?service=999999"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data,
            [],
        )