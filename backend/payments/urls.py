from django.urls import path

from .views import (
    PaystackWebhookView,
    PaymentDetailView,
    PaymentInitializationView,
    PaymentListView,
)


urlpatterns = [
    path(
        "",
        PaymentListView.as_view(),
        name="payment-list",
    ),
    path(
        "initialize/",
        PaymentInitializationView.as_view(),
        name="payment-initialize",
    ),
    path(
        "webhook/",
        PaystackWebhookView.as_view(),
        name="payment-webhook",
    ),
    path(
        "<str:reference>/",
        PaymentDetailView.as_view(),
        name="payment-detail",
    ),
]