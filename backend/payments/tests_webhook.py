import hashlib
import hmac
import json
from unittest.mock import patch

from django.conf import settings
from django.urls import reverse

from rest_framework.test import APITestCase

from payments.models import Payment
from users.models import User
from wallets.models import LedgerEntry, Wallet
from wallets.models import Transaction


class PaystackWebhookTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email="webhook@example.com",
            phone_number="08012345678",
            password="TestPassword123",
        )

        self.wallet = Wallet.objects.create(
            user=self.user,
            balance=1000,
        )

        self.payment = Payment.objects.create(
            user=self.user,
            wallet=self.wallet,
            provider=Payment.Provider.PAYSTACK,
            reference="BAL-PAY-WEBHOOK001",
            amount=5000,
            status=Payment.Status.PENDING,
            description="Wallet funding",
        )

        self.url = reverse("payment-webhook")

    def make_signature(self, payload):
        return hmac.new(
            settings.PAYSTACK_SECRET_KEY.encode(),
            payload,
            hashlib.sha512,
        ).hexdigest()

    def make_payload(self, **overrides):
        data = {
            "event": "charge.success",
            "data": {
                "id": 123456,
                "status": "success",
                "reference": self.payment.reference,
                "amount": 500000,
                "currency": "NGN",
                "customer": {
                    "email": self.user.email,
                },
            },
        }

        data.update(overrides)

        return json.dumps(data).encode()

    def post_webhook(self, payload):
        signature = self.make_signature(payload)

        return self.client.post(
            self.url,
            data=payload,
            content_type="application/json",
            HTTP_X_PAYSTACK_SIGNATURE=signature,
        )

    def test_valid_charge_success_is_accepted(self):
        payload = self.make_payload()

        with patch(
            "payments.views.verify_paystack_payment"
        ) as mock_verify:
            mock_verify.return_value = {
                "status": "success",
                "reference": self.payment.reference,
                "amount": 500000,
                "currency": "NGN",
            }

            response = self.post_webhook(payload)

        self.assertEqual(
            response.status_code,
            200,
        )

    def test_invalid_signature_is_rejected(self):
        payload = self.make_payload()

        response = self.client.post(
            self.url,
            data=payload,
            content_type="application/json",
            HTTP_X_PAYSTACK_SIGNATURE="invalid-signature",
        )

        self.assertEqual(
            response.status_code,
            401,
        )

    def test_successful_payment_credits_wallet(self):
        payload = self.make_payload()

        with patch(
            "payments.views.verify_paystack_payment"
        ) as mock_verify:
            mock_verify.return_value = {
                "status": "success",
                "reference": self.payment.reference,
                "amount": 500000,
                "currency": "NGN",
            }

            self.post_webhook(payload)

        self.wallet.refresh_from_db()

        self.assertEqual(
            self.wallet.balance,
            6000,
        )

    def test_successful_payment_marks_payment_success(self):
        payload = self.make_payload()

        with patch(
            "payments.views.verify_paystack_payment"
        ) as mock_verify:
            mock_verify.return_value = {
                "status": "success",
                "reference": self.payment.reference,
                "amount": 500000,
                "currency": "NGN",
            }

            self.post_webhook(payload)

        self.payment.refresh_from_db()

        self.assertEqual(
            self.payment.status,
            Payment.Status.SUCCESS,
        )

    def test_successful_payment_stores_provider_reference(self):
        payload = self.make_payload()

        with patch(
            "payments.views.verify_paystack_payment"
        ) as mock_verify:
            mock_verify.return_value = {
                "status": "success",
                "reference": self.payment.reference,
                "amount": 500000,
                "currency": "NGN",
                "id": 123456,
            }

            self.post_webhook(payload)

        self.payment.refresh_from_db()

        self.assertEqual(
            self.payment.provider_reference,
            "123456",
        )

    def test_successful_payment_creates_ledger_entry(self):
        payload = self.make_payload()

        with patch(
            "payments.views.verify_paystack_payment"
        ) as mock_verify:
            mock_verify.return_value = {
                "status": "success",
                "reference": self.payment.reference,
                "amount": 500000,
                "currency": "NGN",
            }

            self.post_webhook(payload)

        self.assertEqual(
            LedgerEntry.objects.filter(
                wallet=self.wallet,
                entry_type=LedgerEntry.EntryType.CREDIT,
                amount=5000,
            ).count(),
            1,
        )

    def test_successful_payment_creates_wallet_transaction(self):
        payload = self.make_payload()

        with patch(
            "payments.views.verify_paystack_payment"
        ) as mock_verify:
            mock_verify.return_value = {
                "status": "success",
                "reference": self.payment.reference,
                "amount": 500000,
                "currency": "NGN",
            }

            self.post_webhook(payload)

        self.assertEqual(
            Transaction.objects.filter(
                wallet=self.wallet,
                transaction_type=Transaction.TransactionType.WALLET_FUNDING,
                amount=5000,
            ).count(),
            1,
        )

    def test_duplicate_webhook_does_not_credit_wallet_twice(self):
        payload = self.make_payload()

        with patch(
            "payments.views.verify_paystack_payment"
        ) as mock_verify:
            mock_verify.return_value = {
                "status": "success",
                "reference": self.payment.reference,
                "amount": 500000,
                "currency": "NGN",
            }

            self.post_webhook(payload)
            self.post_webhook(payload)

        self.wallet.refresh_from_db()

        self.assertEqual(
            self.wallet.balance,
            6000,
        )

        self.assertEqual(
            LedgerEntry.objects.filter(
                wallet=self.wallet,
                reference=self.payment.reference,
            ).count(),
            1,
        )

    def test_amount_mismatch_does_not_credit_wallet(self):
        payload = self.make_payload()

        with patch(
            "payments.views.verify_paystack_payment"
        ) as mock_verify:
            mock_verify.return_value = {
                "status": "success",
                "reference": self.payment.reference,
                "amount": 400000,
                "currency": "NGN",
            }

            response = self.post_webhook(payload)

        self.wallet.refresh_from_db()

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertEqual(
            self.wallet.balance,
            1000,
        )

    def test_failed_payment_does_not_credit_wallet(self):
        payload = self.make_payload(
            data={
                "id": 123456,
                "status": "failed",
                "reference": self.payment.reference,
                "amount": 500000,
                "currency": "NGN",
            }
        )

        with patch(
            "payments.views.verify_paystack_payment"
        ) as mock_verify:
            mock_verify.return_value = {
                "status": "failed",
                "reference": self.payment.reference,
                "amount": 500000,
                "currency": "NGN",
            }

            response = self.post_webhook(payload)

        self.wallet.refresh_from_db()

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            self.wallet.balance,
            1000,
        )

    def test_unknown_reference_does_not_credit_wallet(self):
        payload = self.make_payload(
            data={
                "id": 123456,
                "status": "success",
                "reference": "UNKNOWN-REFERENCE",
                "amount": 500000,
                "currency": "NGN",
            }
        )

        response = self.post_webhook(payload)

        self.wallet.refresh_from_db()

        self.assertEqual(
            response.status_code,
            404,
        )

        self.assertEqual(
            self.wallet.balance,
            1000,
        )