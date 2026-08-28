from django.urls import path

from .views import MyTransactionListView, MyWalletView


urlpatterns = [
    path("me/", MyWalletView.as_view(), name="my-wallet"),
    path(
        "transactions/",
        MyTransactionListView.as_view(),
        name="my-transactions",
    ),
]