from django.test import TestCase

from payments.models import Payment
from payments.serializers import PaymentSerializer
from users.models import User
from wallets.models import Wallet


class PaymentSerializerTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email="serializerpayment@balora.com",
            phone_number="08000000111",
            password="TestPassword123!",
        )

        self.wallet = Wallet.objects.create(
            user=self.user,
            balance=10_000,
        )

        self.payment = Payment.objects.create(
            user=self.user,
            wallet=self.wallet,
            provider=Payment.Provider.PAYSTACK,
            reference="PAY-SERIALIZER-001",
            amount=5_000,
            status=Payment.Status.PENDING,
            description="Wallet funding",
        )

    def test_serializer_returns_payment_data(self):
        serializer = PaymentSerializer(
            self.payment,
        )

        self.assertEqual(
            serializer.data["id"],
            self.payment.id,
        )

        self.assertEqual(
            serializer.data["provider"],
            Payment.Provider.PAYSTACK,
        )

        self.assertEqual(
            serializer.data["reference"],
            "PAY-SERIALIZER-001",
        )

        self.assertEqual(
            serializer.data["amount"],
            5_000,
        )

        self.assertEqual(
            serializer.data["status"],
            Payment.Status.PENDING,
        )

        self.assertEqual(
            serializer.data["description"],
            "Wallet funding",
        )

    def test_serializer_does_not_expose_user_or_wallet_fields(self):
        serializer = PaymentSerializer(
            self.payment,
        )

        self.assertNotIn(
            "user",
            serializer.data,
        )

        self.assertNotIn(
            "wallet",
            serializer.data,
        )

    def test_all_payment_fields_are_read_only(self):
        serializer = PaymentSerializer(
            self.payment,
        )

        for field_name in serializer.fields:
            self.assertTrue(
                serializer.fields[field_name].read_only,
                f"{field_name} should be read-only.",
            )

    def test_serializer_cannot_change_payment_status(self):
        serializer = PaymentSerializer(
            self.payment,
            data={
                "status": Payment.Status.SUCCESS,
            },
            partial=True,
        )

        self.assertTrue(
            serializer.is_valid(),
            serializer.errors,
        )

        serializer.save()

        self.payment.refresh_from_db()

        self.assertEqual(
            self.payment.status,
            Payment.Status.PENDING,
        )

    def test_serializer_cannot_change_payment_amount(self):
        serializer = PaymentSerializer(
            self.payment,
            data={
                "amount": 100_000,
            },
            partial=True,
        )

        self.assertTrue(
            serializer.is_valid(),
            serializer.errors,
        )

        serializer.save()

        self.payment.refresh_from_db()

        self.assertEqual(
            self.payment.amount,
            5_000,
        )

    def test_serializer_returns_provider_reference(self):
        self.payment.provider_reference = "PSK-SERIALIZER-123"
        self.payment.save()

        serializer = PaymentSerializer(
            self.payment,
        )

        self.assertEqual(
            serializer.data["provider_reference"],
            "PSK-SERIALIZER-123",
        )

    def test_serializer_returns_completed_at(self):
        from django.utils import timezone

        completed_at = timezone.now()

        self.payment.completed_at = completed_at
        self.payment.status = Payment.Status.SUCCESS
        self.payment.save()

        serializer = PaymentSerializer(
            self.payment,
        )

        self.assertIsNotNone(
            serializer.data["completed_at"],
        )