from rest_framework import serializers

from .models import Agent


class AgentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Agent
        fields = (
            "id",
            "business_name",
            "agent_code",
            "status",
            "commission_rate",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "agent_code",
            "status",
            "commission_rate",
            "created_at",
            "updated_at",
        )


class AgentApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Agent
        fields = (
            "business_name",
        )

    def validate_business_name(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Business name is required."
            )

        return value

    def create(self, validated_data):
        user = self.context["request"].user

        if hasattr(user, "agent"):
            raise serializers.ValidationError(
                "You already have an agent profile."
            )

        return Agent.objects.create(
            user=user,
            business_name=validated_data["business_name"],
            agent_code=f"BAL-{user.id:06d}",
        )