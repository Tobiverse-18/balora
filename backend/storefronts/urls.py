from django.urls import path

from .views import (
    MyStorefrontView,
)


urlpatterns = [
    path(
        "me/",
        MyStorefrontView.as_view(),
        name="my-storefront",
    ),
]