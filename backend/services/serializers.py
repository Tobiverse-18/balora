from rest_framework import serializers

from .models import Service, ServiceProduct


class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = (
            "id",
            "name",
            "service_type",
            "description",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "created_at",
            "updated_at",
        )


class ServiceProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceProduct
        fields = (
            "id",
            "service",
            "name",
            "code",
            "amount",
            "description",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "created_at",
            "updated_at",
        )