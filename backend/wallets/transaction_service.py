from django.db import transaction as db_transaction

from .models import Transaction, Wallet


class TransactionError(Exception):
    """Base exception for transaction-related errors."""


class InvalidTransactionStateError(TransactionError):
    """Raised when a transaction cannot perform the requested transition."""


class TransactionReferenceExistsError(TransactionError):
    """Raised when a transaction reference already exists."""


def create_transaction(
    *,
    wallet_id,
    transaction_type,
    amount,
    reference,
    description="",
):
    if amount <= 0:
        raise ValueError("Amount must be greater than zero.")

    with db_transaction.atomic():
        wallet = Wallet.objects.get(id=wallet_id)

        existing_transaction = Transaction.objects.filter(
            reference=reference
        ).first()

        if existing_transaction:
            if existing_transaction.wallet_id != wallet.id:
                raise TransactionReferenceExistsError(
                    "Transaction reference already belongs to another wallet."
                )

            return existing_transaction

        return Transaction.objects.create(
            wallet=wallet,
            transaction_type=transaction_type,
            status=Transaction.Status.PENDING,
            amount=amount,
            reference=reference,
            description=description,
        )


@db_transaction.atomic
def mark_transaction_processing(*, transaction_id):
    transaction = (
        Transaction.objects
        .select_for_update()
        .get(id=transaction_id)
    )

    if transaction.status != Transaction.Status.PENDING:
        raise InvalidTransactionStateError(
            "Only pending transactions can be moved to processing."
        )

    transaction.status = Transaction.Status.PROCESSING

    transaction.save(
        update_fields=[
            "status",
            "updated_at",
        ]
    )

    return transaction


@db_transaction.atomic
def mark_transaction_success(*, transaction_id):
    transaction = (
        Transaction.objects
        .select_for_update()
        .get(id=transaction_id)
    )

    if transaction.status != Transaction.Status.PROCESSING:
        raise InvalidTransactionStateError(
            "Only processing transactions can be marked as successful."
        )

    transaction.status = Transaction.Status.SUCCESS

    transaction.save(
        update_fields=[
            "status",
            "updated_at",
        ]
    )

    return transaction


@db_transaction.atomic
def mark_transaction_failed(*, transaction_id):
    transaction = (
        Transaction.objects
        .select_for_update()
        .get(id=transaction_id)
    )

    if transaction.status != Transaction.Status.PROCESSING:
        raise InvalidTransactionStateError(
            "Only processing transactions can be marked as failed."
        )

    transaction.status = Transaction.Status.FAILED

    transaction.save(
        update_fields=[
            "status",
            "updated_at",
        ]
    )

    return transaction


@db_transaction.atomic
def mark_transaction_reversed(*, transaction_id):
    transaction = (
        Transaction.objects
        .select_for_update()
        .get(id=transaction_id)
    )

    if transaction.status != Transaction.Status.SUCCESS:
        raise InvalidTransactionStateError(
            "Only successful transactions can be reversed."
        )

    transaction.status = Transaction.Status.REVERSED

    transaction.save(
        update_fields=[
            "status",
            "updated_at",
        ]
    )

    return transaction