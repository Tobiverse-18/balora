from rest_framework import serializers

from .models import Transaction


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = (
            "id",
            "transaction_type",
            "status",
            "amount",
            "reference",
            "description",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields