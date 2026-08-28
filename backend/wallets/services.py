from django.db import transaction as db_transaction
from django.db.models import F

from .models import LedgerEntry, Transaction, Wallet


class WalletError(Exception):
    """Base exception for wallet-related errors."""


class WalletInactiveError(WalletError):
    """Raised when a wallet is inactive."""


class InsufficientFundsError(WalletError):
    """Raised when a wallet does not have enough funds."""


@db_transaction.atomic
def credit_wallet(*, wallet_id, amount, reference, description=""):
    if amount <= 0:
        raise ValueError("Amount must be greater than zero.")

    wallet = (
        Wallet.objects
        .select_for_update()
        .get(id=wallet_id)
    )

    if not wallet.is_active:
        raise WalletInactiveError("Wallet is inactive.")

    existing_entry = LedgerEntry.objects.filter(
        reference=reference
    ).first()

    if existing_entry:
        if existing_entry.wallet_id != wallet.id:
            raise WalletError(
                "Reference already belongs to another wallet."
            )

        return wallet, existing_entry

    balance_before = wallet.balance
    balance_after = balance_before + amount

    wallet.balance = balance_after
    wallet.save(update_fields=["balance", "updated_at"])

    ledger_entry = LedgerEntry.objects.create(
        wallet=wallet,
        entry_type=LedgerEntry.EntryType.CREDIT,
        amount=amount,
        balance_before=balance_before,
        balance_after=balance_after,
        reference=reference,
        description=description,
    )

    return wallet, ledger_entry


@db_transaction.atomic
def debit_wallet(*, wallet_id, amount, reference, description=""):
    if amount <= 0:
        raise ValueError("Amount must be greater than zero.")

    wallet = (
        Wallet.objects
        .select_for_update()
        .get(id=wallet_id)
    )

    if not wallet.is_active:
        raise WalletInactiveError("Wallet is inactive.")

    existing_entry = LedgerEntry.objects.filter(
        reference=reference
    ).first()

    if existing_entry:
        if existing_entry.wallet_id != wallet.id:
            raise WalletError(
                "Reference already belongs to another wallet."
            )

        return wallet, existing_entry

    if wallet.balance < amount:
        raise InsufficientFundsError(
            "Insufficient wallet balance."
        )

    balance_before = wallet.balance
    balance_after = balance_before - amount

    wallet.balance = balance_after
    wallet.save(update_fields=["balance", "updated_at"])

    ledger_entry = LedgerEntry.objects.create(
        wallet=wallet,
        entry_type=LedgerEntry.EntryType.DEBIT,
        amount=amount,
        balance_before=balance_before,
        balance_after=balance_after,
        reference=reference,
        description=description,
    )

    return wallet, ledger_entry