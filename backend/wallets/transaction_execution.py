from django.db import transaction as db_transaction

from .models import Transaction
from .services import (
    InsufficientFundsError,
    WalletError,
    debit_wallet,
)


class TransactionExecutionError(Exception):
    """Base exception for transaction execution errors."""


class TransactionNotProcessableError(TransactionExecutionError):
    """Raised when a transaction cannot be processed."""


@db_transaction.atomic
def execute_wallet_debit(*, transaction_id):
    """
    Execute a processing transaction by debiting the user's wallet.

    A transaction can only be executed while it is in PROCESSING state.

    The transaction row is locked before execution so that concurrent
    requests cannot safely execute the same transaction twice.

    Wallet debit, ledger creation, and transaction success/failure are
    performed inside the same database transaction.
    """

    financial_transaction = (
        Transaction.objects
        .select_for_update()
        .select_related("wallet")
        .get(id=transaction_id)
    )

    if financial_transaction.status != Transaction.Status.PROCESSING:
        raise TransactionNotProcessableError(
            "Only processing transactions can be executed."
        )

    wallet = financial_transaction.wallet

    try:
        wallet, ledger_entry = debit_wallet(
            wallet_id=wallet.id,
            amount=financial_transaction.amount,
            reference=financial_transaction.reference,
            description=financial_transaction.description,
        )

    except (InsufficientFundsError, WalletError):
        financial_transaction.status = Transaction.Status.FAILED

        financial_transaction.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        return financial_transaction, None

    financial_transaction.status = Transaction.Status.SUCCESS

    financial_transaction.save(
        update_fields=[
            "status",
            "updated_at",
        ]
    )

    return financial_transaction, ledger_entry