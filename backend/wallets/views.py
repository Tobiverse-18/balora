from django.shortcuts import get_object_or_404

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Transaction, Wallet
from .serializers import TransactionSerializer
from .pagination import TransactionPagination


class MyWalletView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        wallet = get_object_or_404(
            Wallet,
            user=request.user,
        )

        return Response({
            "id": wallet.id,
            "balance": wallet.balance,
            "currency": wallet.currency,
            "is_active": wallet.is_active,
        })


class MyTransactionListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        wallet = get_object_or_404(
            Wallet,
            user=request.user,
        )

        transactions = (
            Transaction.objects
            .filter(wallet=wallet)
            .order_by("-created_at")
        )

        paginator = TransactionPagination()

        page = paginator.paginate_queryset(
            transactions,
            request,
            view=self,
        )

        serializer = TransactionSerializer(
            page,
            many=True,
        )

        return paginator.get_paginated_response(
            serializer.data
        )