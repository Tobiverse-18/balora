from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path("admin/", admin.site.urls),

    path(
        "api/auth/",
        include("users.urls"),
    ),

    path(
        "api/wallet/",
        include("wallets.urls"),
    ),

    path(
        "api/agents/",
        include("agents.urls"),
    ),

    path(
        "api/storefronts/",
        include("storefronts.urls"),
    ),

    path(
        "api/services/",
        include("services.urls"),
    ),

    path(
        "api/payments/",
        include("payments.urls"),
    ),
]