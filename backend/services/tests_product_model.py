from django.test import TestCase

from services.models import Service, ServiceProduct


class ServiceProductModelTests(TestCase):

    def setUp(self):
        self.service = Service.objects.create(
            name="Data",
            service_type=Service.ServiceType.DATA,
            description="Mobile data services.",
        )

    def test_product_can_be_created(self):
        product = ServiceProduct.objects.create(
            service=self.service,
            name="MTN 10GB",
            code="MTN-DATA-10GB",
            amount=3_000,
            description="MTN 10GB data plan.",
        )

        self.assertEqual(
            product.service,
            self.service,
        )

        self.assertEqual(
            product.name,
            "MTN 10GB",
        )

        self.assertEqual(
            product.code,
            "MTN-DATA-10GB",
        )

        self.assertEqual(
            product.amount,
            3_000,
        )

        self.assertTrue(
            product.is_active,
        )

    def test_product_defaults_to_active(self):
        product = ServiceProduct.objects.create(
            service=self.service,
            name="MTN 1GB",
            code="MTN-DATA-1GB",
            amount=1_000,
        )

        self.assertTrue(
            product.is_active,
        )

    def test_product_string_representation(self):
        product = ServiceProduct.objects.create(
            service=self.service,
            name="MTN 10GB",
            code="MTN-DATA-10GB",
            amount=3_000,
        )

        self.assertEqual(
            str(product),
            "Data - MTN 10GB",
        )

    def test_product_belongs_to_service(self):
        product = ServiceProduct.objects.create(
            service=self.service,
            name="MTN 10GB",
            code="MTN-DATA-10GB",
            amount=3_000,
        )

        self.assertIn(
            product,
            self.service.products.all(),
        )

    def test_product_code_must_be_unique_within_service(self):
        ServiceProduct.objects.create(
            service=self.service,
            name="MTN 10GB",
            code="MTN-DATA-10GB",
            amount=3_000,
        )

        with self.assertRaises(Exception):
            ServiceProduct.objects.create(
                service=self.service,
                name="Another MTN 10GB",
                code="MTN-DATA-10GB",
                amount=3_500,
            )

    def test_same_product_code_can_exist_for_different_services(self):
        cable_service = Service.objects.create(
            name="Cable TV",
            service_type=Service.ServiceType.CABLE,
            description="Cable TV services.",
        )

        first_product = ServiceProduct.objects.create(
            service=self.service,
            name="MTN 10GB",
            code="PRODUCT-001",
            amount=3_000,
        )

        second_product = ServiceProduct.objects.create(
            service=cable_service,
            name="Cable Package",
            code="PRODUCT-001",
            amount=5_000,
        )

        self.assertEqual(
            first_product.code,
            second_product.code,
        )

        self.assertNotEqual(
            first_product.service,
            second_product.service,
        )

    def test_product_amount_must_be_positive(self):
        product = ServiceProduct(
            service=self.service,
            name="Invalid Product",
            code="INVALID-001",
            amount=0,
        )

        with self.assertRaises(Exception):
            product.full_clean()