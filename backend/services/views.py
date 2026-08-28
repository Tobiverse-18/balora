from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Service, ServiceProduct
from .serializers import ServiceProductSerializer, ServiceSerializer


class ServiceListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        services = (
            Service.objects
            .filter(is_active=True)
            .order_by("name")
        )

        serializer = ServiceSerializer(
            services,
            many=True,
        )

        return Response(
            serializer.data,
        )


class ServiceProductListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        products = (
            ServiceProduct.objects
            .filter(
                is_active=True,
                service__is_active=True,
            )
            .select_related("service")
            .order_by("name")
        )

        service_id = request.query_params.get("service")

        if service_id:
            products = products.filter(
                service_id=service_id,
            )

        serializer = ServiceProductSerializer(
            products,
            many=True,
        )

        return Response(
            serializer.data,
        )