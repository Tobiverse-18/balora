from django.test import TestCase
from django.core.exceptions import ValidationError

from users.models import User
from wallets.models import Wallet
from payments.models import Payment


class PaymentModelTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email="paymenttest@balora.com",
            phone_number="08000000101",
            password="TestPassword123!",
        )

        self.wallet = Wallet.objects.create(
            user=self.user,
            balance=10_000,
        )

    def create_payment(
        self,
        reference="PAY-TEST-001",
    ):
        return Payment.objects.create(
            user=self.user,
            wallet=self.wallet,
            provider=Payment.Provider.PAYSTACK,
            reference=reference,
            amount=5_000,
        )

    def test_payment_can_be_created(self):
        payment = self.create_payment()

        self.assertEqual(
            payment.user,
            self.user,
        )

        self.assertEqual(
            payment.wallet,
            self.wallet,
        )

        self.assertEqual(
            payment.provider,
            Payment.Provider.PAYSTACK,
        )

        self.assertEqual(
            payment.reference,
            "PAY-TEST-001",
        )

        self.assertEqual(
            payment.amount,
            5_000,
        )

    def test_payment_defaults_to_pending(self):
        payment = self.create_payment()

        self.assertEqual(
            payment.status,
            Payment.Status.PENDING,
        )

    def test_payment_can_have_provider_reference(self):
        payment = self.create_payment()

        payment.provider_reference = "PSK-123456789"
        payment.save()

        payment.refresh_from_db()

        self.assertEqual(
            payment.provider_reference,
            "PSK-123456789",
        )

    def test_payment_provider_reference_is_optional(self):
        payment = self.create_payment()

        self.assertIsNone(
            payment.provider_reference,
        )

    def test_payment_completed_at_is_optional(self):
        payment = self.create_payment()

        self.assertIsNone(
            payment.completed_at,
        )

    def test_payment_string_representation(self):
        payment = self.create_payment()

        self.assertEqual(
            str(payment),
            "PAY-TEST-001 - PENDING",
        )

    def test_payment_reference_must_be_unique(self):
        self.create_payment(
            reference="PAY-DUPLICATE-001",
        )

        with self.assertRaises(Exception):
            self.create_payment(
                reference="PAY-DUPLICATE-001",
            )

    def test_payment_amount_must_be_positive(self):
        payment = Payment(
            user=self.user,
            wallet=self.wallet,
            provider=Payment.Provider.PAYSTACK,
            reference="PAY-INVALID-001",
            amount=0,
        )

        with self.assertRaises(ValidationError):
            payment.full_clean()

    def test_payment_can_be_marked_success(self):
        payment = self.create_payment()

        payment.status = Payment.Status.SUCCESS
        payment.save()

        payment.refresh_from_db()

        self.assertEqual(
            payment.status,
            Payment.Status.SUCCESS,
        )

    def test_payment_can_be_marked_failed(self):
        payment = self.create_payment()

        payment.status = Payment.Status.FAILED
        payment.save()

        payment.refresh_from_db()

        self.assertEqual(
            payment.status,
            Payment.Status.FAILED,
        )