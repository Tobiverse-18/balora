from django.shortcuts import get_object_or_404

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Agent
from .serializers import AgentApplicationSerializer, AgentSerializer


class AgentApplicationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AgentApplicationSerializer(
            data=request.data,
            context={"request": request},
        )

        serializer.is_valid(raise_exception=True)

        agent = serializer.save()

        return Response(
            AgentSerializer(agent).data,
            status=201,
        )


class MyAgentView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        agent = get_object_or_404(
            Agent,
            user=request.user,
        )

        return Response(
            AgentSerializer(agent).data
        )