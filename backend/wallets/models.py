from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class Wallet(models.Model):
    class Currency(models.TextChoices):
        NGN = "NGN", "Nigerian Naira"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="wallet",
    )

    balance = models.BigIntegerField(
        default=0,
        validators=[MinValueValidator(0)],
    )

    currency = models.CharField(
        max_length=3,
        choices=Currency.choices,
        default=Currency.NGN,
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} - {self.currency}"


class LedgerEntry(models.Model):
    class EntryType(models.TextChoices):
        CREDIT = "CREDIT", "Credit"
        DEBIT = "DEBIT", "Debit"

    wallet = models.ForeignKey(
        Wallet,
        on_delete=models.PROTECT,
        related_name="ledger_entries",
    )

    entry_type = models.CharField(
        max_length=10,
        choices=EntryType.choices,
    )

    amount = models.BigIntegerField(
        validators=[MinValueValidator(1)],
    )

    balance_before = models.BigIntegerField(
        validators=[MinValueValidator(0)],
    )

    balance_after = models.BigIntegerField(
        validators=[MinValueValidator(0)],
    )

    reference = models.CharField(
        max_length=100,
        unique=True,
    )

    description = models.CharField(
        max_length=255,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    def __str__(self):
        return f"{self.wallet.user.email} - {self.entry_type} - {self.amount}"

class Transaction(models.Model):
    class TransactionType(models.TextChoices):
        WALLET_FUNDING = "WALLET_FUNDING", "Wallet Funding"
        AIRTIME = "AIRTIME", "Airtime"
        DATA = "DATA", "Data"
        CABLE = "CABLE", "Cable TV"
        ELECTRICITY = "ELECTRICITY", "Electricity"
        TRANSFER = "TRANSFER", "Transfer"
        REFUND = "REFUND", "Refund"
        COMMISSION = "COMMISSION", "Commission"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        PROCESSING = "PROCESSING", "Processing"
        SUCCESS = "SUCCESS", "Success"
        FAILED = "FAILED", "Failed"
        REVERSED = "REVERSED", "Reversed"

    wallet = models.ForeignKey(
        Wallet,
        on_delete=models.PROTECT,
        related_name="transactions",
    )

    transaction_type = models.CharField(
        max_length=20,
        choices=TransactionType.choices,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    amount = models.BigIntegerField(
        validators=[MinValueValidator(1)],
    )

    reference = models.CharField(
        max_length=100,
        unique=True,
    )

    description = models.CharField(
        max_length=255,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return f"{self.reference} - {self.transaction_type} - {self.status}"