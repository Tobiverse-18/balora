from django.test import TestCase

from services.models import Service


class ServiceModelTests(TestCase):

    def test_service_can_be_created(self):
        service = Service.objects.create(
            name="Airtime",
            service_type=Service.ServiceType.AIRTIME,
            description="Purchase airtime for mobile networks.",
        )

        self.assertEqual(
            service.name,
            "Airtime",
        )

        self.assertEqual(
            service.service_type,
            Service.ServiceType.AIRTIME,
        )

        self.assertEqual(
            service.description,
            "Purchase airtime for mobile networks.",
        )

        self.assertTrue(
            service.is_active,
        )

    def test_service_defaults_to_active(self):
        service = Service.objects.create(
            name="Data",
            service_type=Service.ServiceType.DATA,
        )

        self.assertTrue(
            service.is_active,
        )

    def test_service_string_representation(self):
        service = Service.objects.create(
            name="Cable TV",
            service_type=Service.ServiceType.CABLE,
        )

        self.assertEqual(
            str(service),
            "Cable TV",
        )

    def test_service_type_choices_exist(self):
        self.assertEqual(
            Service.ServiceType.AIRTIME,
            "AIRTIME",
        )

        self.assertEqual(
            Service.ServiceType.DATA,
            "DATA",
        )

        self.assertEqual(
            Service.ServiceType.CABLE,
            "CABLE",
        )

        self.assertEqual(
            Service.ServiceType.ELECTRICITY,
            "ELECTRICITY",
        )

        self.assertEqual(
            Service.ServiceType.TRANSFER,
            "TRANSFER",
        )

    def test_service_name_must_be_unique(self):
        Service.objects.create(
            name="Airtime",
            service_type=Service.ServiceType.AIRTIME,
        )

        with self.assertRaises(Exception):
            Service.objects.create(
                name="Airtime",
                service_type=Service.ServiceType.DATA,
            )

    def test_service_type_must_be_unique(self):
        Service.objects.create(
            name="Airtime",
            service_type=Service.ServiceType.AIRTIME,
        )

        with self.assertRaises(Exception):
            Service.objects.create(
                name="Mobile Airtime",
                service_type=Service.ServiceType.AIRTIME,
            )