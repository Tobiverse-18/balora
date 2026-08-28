from django.test import TestCase

from services.models import Service
from services.serializers import ServiceSerializer


class ServiceSerializerTests(TestCase):

    def setUp(self):
        self.service = Service.objects.create(
            name="Airtime",
            service_type=Service.ServiceType.AIRTIME,
            description="Purchase airtime for mobile networks.",
        )

    def test_serializer_returns_service_data(self):
        serializer = ServiceSerializer(
            self.service,
        )

        self.assertEqual(
            serializer.data["id"],
            self.service.id,
        )

        self.assertEqual(
            serializer.data["name"],
            "Airtime",
        )

        self.assertEqual(
            serializer.data["service_type"],
            Service.ServiceType.AIRTIME,
        )

        self.assertEqual(
            serializer.data["description"],
            "Purchase airtime for mobile networks.",
        )

        self.assertTrue(
            serializer.data["is_active"],
        )

    def test_id_is_read_only(self):
        serializer = ServiceSerializer(
            instance=self.service,
            data={
                "id": 9999,
                "name": "Updated Airtime",
            },
            partial=True,
        )

        self.assertTrue(
            serializer.is_valid(),
            serializer.errors,
        )

        service = serializer.save()

        self.assertNotEqual(
            service.id,
            9999,
        )

        self.assertEqual(
            service.name,
            "Updated Airtime",
        )

    def test_created_at_is_read_only(self):
        original_created_at = self.service.created_at

        serializer = ServiceSerializer(
            instance=self.service,
            data={
                "created_at": "2000-01-01T00:00:00Z",
            },
            partial=True,
        )

        self.assertTrue(
            serializer.is_valid(),
            serializer.errors,
        )

        service = serializer.save()

        self.assertEqual(
            service.created_at,
            original_created_at,
        )

    def test_updated_at_is_read_only(self):
        serializer = ServiceSerializer(
            instance=self.service,
            data={
                "updated_at": "2000-01-01T00:00:00Z",
            },
            partial=True,
        )

        self.assertTrue(
            serializer.is_valid(),
            serializer.errors,
        )

        service = serializer.save()

        self.assertNotEqual(
            str(service.updated_at),
            "2000-01-01 00:00:00+00:00",
        )

    def test_serializer_requires_name(self):
        serializer = ServiceSerializer(
            data={
                "service_type": Service.ServiceType.DATA,
            },
        )

        self.assertFalse(
            serializer.is_valid(),
        )

        self.assertIn(
            "name",
            serializer.errors,
        )

    def test_serializer_requires_service_type(self):
        serializer = ServiceSerializer(
            data={
                "name": "Data",
            },
        )

        self.assertFalse(
            serializer.is_valid(),
        )

        self.assertIn(
            "service_type",
            serializer.errors,
        )