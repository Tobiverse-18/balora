from rest_framework import serializers

from .models import Storefront


class StorefrontSerializer(serializers.ModelSerializer):
    agent_code = serializers.CharField(
        source="agent.agent_code",
        read_only=True,
    )

    agent_status = serializers.CharField(
        source="agent.status",
        read_only=True,
    )

    class Meta:
        model = Storefront
        fields = (
            "id",
            "name",
            "slug",
            "is_active",
            "agent_code",
            "agent_status",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "agent_code",
            "agent_status",
            "created_at",
            "updated_at",
        )