from django.urls import path

from .views import (
    ServiceListView,
    ServiceProductListView,
)


urlpatterns = [
    path(
        "",
        ServiceListView.as_view(),
        name="service-list",
    ),
    path(
        "products/",
        ServiceProductListView.as_view(),
        name="service-product-list",
    ),
]