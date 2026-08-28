from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from agents.models import Agent

from .models import Storefront
from .serializers import StorefrontSerializer


class MyStorefrontView(APIView):
    permission_classes = [IsAuthenticated]

    def get_agent(self, request):
        return get_object_or_404(
            Agent,
            user=request.user,
        )

    def get_storefront(self, agent):
        return get_object_or_404(
            Storefront,
            agent=agent,
        )

    def get(self, request):
        agent = self.get_agent(request)
        storefront = self.get_storefront(agent)

        serializer = StorefrontSerializer(
            storefront,
        )

        return Response(
            serializer.data,
        )

    def post(self, request):
        agent = self.get_agent(request)

        if Storefront.objects.filter(
            agent=agent
        ).exists():
            return Response(
                {
                    "detail": (
                        "You already have a storefront."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = StorefrontSerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        storefront = serializer.save(
            agent=agent,
        )

        return Response(
            StorefrontSerializer(
                storefront,
            ).data,
            status=status.HTTP_201_CREATED,
        )

    def patch(self, request):
        agent = self.get_agent(request)
        storefront = self.get_storefront(agent)

        serializer = StorefrontSerializer(
            storefront,
            data=request.data,
            partial=True,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        storefront = serializer.save()

        return Response(
            StorefrontSerializer(
                storefront,
            ).data,
        )