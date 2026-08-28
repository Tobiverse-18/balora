import hashlib
import hmac
import json
import uuid

from django.conf import settings
from django.db import transaction as db_transaction
from django.shortcuts import get_object_or_404

from rest_framework import serializers
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from wallets.models import Transaction, Wallet
from wallets.services import credit_wallet

from .models import Payment
from .serializers import PaymentSerializer
from .services import verify_paystack_payment


class PaymentListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        payments = (
            Payment.objects
            .filter(user=request.user)
            .order_by("-created_at")
        )

        serializer = PaymentSerializer(
            payments,
            many=True,
        )

        return Response(serializer.data)


class PaymentDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, reference):
        payment = get_object_or_404(
            Payment,
            user=request.user,
            reference=reference,
        )

        serializer = PaymentSerializer(payment)

        return Response(serializer.data)


class PaymentInitializationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        amount = request.data.get("amount")

        if amount is None:
            raise serializers.ValidationError(
                {"amount": "Amount is required."}
            )

        try:
            amount = int(amount)
        except (TypeError, ValueError):
            raise serializers.ValidationError(
                {"amount": "Amount must be a valid number."}
            )

        if amount <= 0:
            raise serializers.ValidationError(
                {"amount": "Amount must be greater than zero."}
            )

        wallet = get_object_or_404(
            Wallet,
            user=request.user,
        )

        reference = f"BAL-PAY-{uuid.uuid4().hex[:20].upper()}"

        payment = Payment.objects.create(
            user=request.user,
            wallet=wallet,
            provider=Payment.Provider.PAYSTACK,
            reference=reference,
            amount=amount,
            status=Payment.Status.PENDING,
            description="Wallet funding",
        )

        return Response(
            {
                "id": payment.id,
                "reference": payment.reference,
                "amount": payment.amount,
                "status": payment.status,
                "provider": payment.provider,
            },
            status=201,
        )


class PaystackWebhookView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        signature = request.headers.get(
            "X-Paystack-Signature"
        )

        if not signature:
            return Response(
                {"detail": "Invalid signature."},
                status=401,
            )

        expected_signature = hmac.new(
            settings.PAYSTACK_SECRET_KEY.encode(),
            request.body,
            hashlib.sha512,
        ).hexdigest()

        if not hmac.compare_digest(
            signature,
            expected_signature,
        ):
            return Response(
                {"detail": "Invalid signature."},
                status=401,
            )

        try:
            payload = json.loads(request.body)
        except json.JSONDecodeError:
            return Response(
                {"detail": "Invalid JSON payload."},
                status=400,
            )

        event = payload.get("event")
        data = payload.get("data") or {}

        if event != "charge.success":
            return Response(
                {"detail": "Event ignored."},
                status=200,
            )

        reference = data.get("reference")

        if not reference:
            return Response(
                {"detail": "Payment reference is required."},
                status=400,
            )

        try:
            payment = Payment.objects.get(
                reference=reference,
                provider=Payment.Provider.PAYSTACK,
            )
        except Payment.DoesNotExist:
            return Response(
                {"detail": "Payment not found."},
                status=404,
            )

        verified_payment = verify_paystack_payment(
            reference
        )

        if verified_payment.get("status") != "success":
            return Response(
                {"detail": "Payment was not successful."},
                status=200,
            )

        verified_reference = verified_payment.get(
            "reference"
        )

        if verified_reference != payment.reference:
            return Response(
                {"detail": "Payment reference mismatch."},
                status=400,
            )

        verified_amount = verified_payment.get("amount")
        expected_amount = int(payment.amount * 100)

        if verified_amount != expected_amount:
            return Response(
                {"detail": "Payment amount mismatch."},
                status=400,
            )

        with db_transaction.atomic():
            payment = (
                Payment.objects
                .select_for_update()
                .get(id=payment.id)
            )

            if payment.status == Payment.Status.SUCCESS:
                return Response(
                    {"detail": "Payment already processed."},
                    status=200,
                )

            provider_reference = verified_payment.get("id")

            payment.status = Payment.Status.SUCCESS
            payment.provider_reference = (
                str(provider_reference)
                if provider_reference is not None
                else None
            )

            payment.save(
                update_fields=[
                    "status",
                    "provider_reference",
                    "updated_at",
                ]
            )

            transaction_reference = (
                f"BAL-TXN-{payment.reference}"
            )

            wallet_transaction = Transaction.objects.filter(
                reference=transaction_reference
            ).first()

            if wallet_transaction is None:
                wallet_transaction = Transaction.objects.create(
                    wallet=payment.wallet,
                    transaction_type=(
                        Transaction.TransactionType.WALLET_FUNDING
                    ),
                    status=Transaction.Status.SUCCESS,
                    amount=payment.amount,
                    reference=transaction_reference,
                    description="Wallet funding via Paystack",
                )
            else:
                wallet_transaction.status = (
                    Transaction.Status.SUCCESS
                )

                wallet_transaction.save(
                    update_fields=[
                        "status",
                        "updated_at",
                    ]
                )

            credit_wallet(
                wallet_id=payment.wallet_id,
                amount=payment.amount,
                reference=payment.reference,
                description="Wallet funding via Paystack",
            )

        return Response(
            {"detail": "Payment processed successfully."},
            status=200,
        )