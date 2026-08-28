from rest_framework import serializers

from .models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = (
            "id",
            "provider",
            "reference",
            "amount",
            "status",
            "provider_reference",
            "description",
            "created_at",
            "updated_at",
            "completed_at",
        )

        read_only_fields = fields