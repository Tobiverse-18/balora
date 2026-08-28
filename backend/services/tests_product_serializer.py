from django.test import TestCase
from rest_framework.exceptions import ValidationError

from services.models import Service, ServiceProduct
from services.serializers import ServiceProductSerializer


class ServiceProductSerializerTests(TestCase):

    def setUp(self):
        self.service = Service.objects.create(
            name="Data",
            service_type=Service.ServiceType.DATA,
            description="Mobile data services.",
        )

        self.product = ServiceProduct.objects.create(
            service=self.service,
            name="MTN 10GB",
            code="MTN-DATA-10GB",
            amount=3_000,
            description="MTN 10GB data plan.",
        )

    def test_serializer_returns_product_data(self):
        serializer = ServiceProductSerializer(
            self.product,
        )

        self.assertEqual(
            serializer.data["id"],
            self.product.id,
        )

        self.assertEqual(
            serializer.data["service"],
            self.service.id,
        )

        self.assertEqual(
            serializer.data["name"],
            "MTN 10GB",
        )

        self.assertEqual(
            serializer.data["code"],
            "MTN-DATA-10GB",
        )

        self.assertEqual(
            serializer.data["amount"],
            3_000,
        )

        self.assertEqual(
            serializer.data["description"],
            "MTN 10GB data plan.",
        )

        self.assertTrue(
            serializer.data["is_active"],
        )

    def test_serializer_requires_service(self):
        serializer = ServiceProductSerializer(
            data={
                "name": "MTN 5GB",
                "code": "MTN-DATA-5GB",
                "amount": 2_000,
            },
        )

        self.assertFalse(
            serializer.is_valid(),
        )

        self.assertIn(
            "service",
            serializer.errors,
        )

    def test_serializer_requires_name(self):
        serializer = ServiceProductSerializer(
            data={
                "service": self.service.id,
                "code": "MTN-DATA-5GB",
                "amount": 2_000,
            },
        )

        self.assertFalse(
            serializer.is_valid(),
        )

        self.assertIn(
            "name",
            serializer.errors,
        )

    def test_serializer_requires_code(self):
        serializer = ServiceProductSerializer(
            data={
                "service": self.service.id,
                "name": "MTN 5GB",
                "amount": 2_000,
            },
        )

        self.assertFalse(
            serializer.is_valid(),
        )

        self.assertIn(
            "code",
            serializer.errors,
        )

    def test_serializer_requires_amount(self):
        serializer = ServiceProductSerializer(
            data={
                "service": self.service.id,
                "name": "MTN 5GB",
                "code": "MTN-DATA-5GB",
            },
        )

        self.assertFalse(
            serializer.is_valid(),
        )

        self.assertIn(
            "amount",
            serializer.errors,
        )

    def test_created_at_and_updated_at_are_read_only(self):
        serializer = ServiceProductSerializer(
            instance=self.product,
            data={
                "created_at": "2000-01-01T00:00:00Z",
                "updated_at": "2000-01-01T00:00:00Z",
            },
            partial=True,
        )

        self.assertTrue(
            serializer.is_valid(),
            serializer.errors,
        )

        serializer.save()

        self.product.refresh_from_db()

        self.assertNotEqual(
            str(self.product.created_at),
            "2000-01-01 00:00:00+00:00",
        )

        self.assertNotEqual(
            str(self.product.updated_at),
            "2000-01-01 00:00:00+00:00",
        )

    def test_amount_must_be_positive(self):
        serializer = ServiceProductSerializer(
            data={
                "service": self.service.id,
                "name": "Invalid Product",
                "code": "INVALID-001",
                "amount": 0,
            },
        )

        self.assertFalse(
            serializer.is_valid(),
        )

        self.assertIn(
            "amount",
            serializer.errors,
        )