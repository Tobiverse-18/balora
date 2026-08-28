from django.test import TestCase

from users.models import User
from wallets.models import LedgerEntry, Transaction, Wallet
from wallets.transaction_execution import (
    TransactionNotProcessableError,
    execute_wallet_debit,
)
from wallets.transaction_service import (
    create_transaction,
    mark_transaction_processing,
)


class TransactionExecutionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="executiontest@balora.com",
            phone_number="08000000031",
            password="TestPassword123!",
        )

        self.wallet = Wallet.objects.create(
            user=self.user,
            balance=10_000,
        )

    def create_processing_transaction(
        self,
        amount=3_000,
        reference="TEST-EXECUTION-001",
    ):
        transaction = create_transaction(
            wallet_id=self.wallet.id,
            transaction_type=Transaction.TransactionType.AIRTIME,
            amount=amount,
            reference=reference,
            description="Execution test",
        )

        return mark_transaction_processing(
            transaction_id=transaction.id,
        )

    def test_successful_execution_debits_wallet(self):
        transaction = self.create_processing_transaction()

        transaction, ledger_entry = execute_wallet_debit(
            transaction_id=transaction.id,
        )

        self.wallet.refresh_from_db()
        transaction.refresh_from_db()

        self.assertEqual(
            transaction.status,
            Transaction.Status.SUCCESS,
        )

        self.assertEqual(
            self.wallet.balance,
            7_000,
        )

        self.assertIsNotNone(ledger_entry)

        self.assertEqual(
            ledger_entry.entry_type,
            LedgerEntry.EntryType.DEBIT,
        )

        self.assertEqual(
            ledger_entry.amount,
            3_000,
        )

    def test_insufficient_funds_fails_transaction(self):
        transaction = self.create_processing_transaction(
            amount=20_000,
            reference="TEST-EXECUTION-002",
        )

        transaction, ledger_entry = execute_wallet_debit(
            transaction_id=transaction.id,
        )

        self.wallet.refresh_from_db()
        transaction.refresh_from_db()

        self.assertEqual(
            transaction.status,
            Transaction.Status.FAILED,
        )

        self.assertEqual(
            self.wallet.balance,
            10_000,
        )

        self.assertIsNone(ledger_entry)

        self.assertFalse(
            LedgerEntry.objects.filter(
                reference="TEST-EXECUTION-002"
            ).exists()
        )

    def test_pending_transaction_cannot_execute(self):
        transaction = create_transaction(
            wallet_id=self.wallet.id,
            transaction_type=Transaction.TransactionType.AIRTIME,
            amount=3_000,
            reference="TEST-EXECUTION-003",
            description="Pending execution test",
        )

        with self.assertRaises(TransactionNotProcessableError):
            execute_wallet_debit(
                transaction_id=transaction.id,
            )

        self.wallet.refresh_from_db()
        transaction.refresh_from_db()

        self.assertEqual(
            transaction.status,
            Transaction.Status.PENDING,
        )

        self.assertEqual(
            self.wallet.balance,
            10_000,
        )

    def test_successful_execution_creates_one_ledger_entry(self):
        transaction = self.create_processing_transaction(
            reference="TEST-EXECUTION-004",
        )

        execute_wallet_debit(
            transaction_id=transaction.id,
        )

        self.wallet.refresh_from_db()

        self.assertEqual(
            LedgerEntry.objects.filter(
                wallet=self.wallet,
                reference="TEST-EXECUTION-004",
            ).count(),
            1,
        )

        self.assertEqual(
            self.wallet.balance,
            7_000,
        )

    def test_successful_transaction_cannot_be_executed_again(self):
        transaction = self.create_processing_transaction(
            reference="TEST-DOUBLE-EXECUTION-001",
        )

        execute_wallet_debit(
            transaction_id=transaction.id,
        )

        with self.assertRaises(TransactionNotProcessableError):
            execute_wallet_debit(
                transaction_id=transaction.id,
            )

        self.wallet.refresh_from_db()

        self.assertEqual(
            self.wallet.balance,
            7_000,
        )

        self.assertEqual(
            LedgerEntry.objects.filter(
                wallet=self.wallet,
                reference="TEST-DOUBLE-EXECUTION-001",
            ).count(),
            1,
        )

    def test_failed_transaction_cannot_be_executed_again(self):
        transaction = self.create_processing_transaction(
            amount=20_000,
            reference="TEST-DOUBLE-EXECUTION-002",
        )

        execute_wallet_debit(
            transaction_id=transaction.id,
        )

        with self.assertRaises(TransactionNotProcessableError):
            execute_wallet_debit(
                transaction_id=transaction.id,
            )

        self.wallet.refresh_from_db()

        self.assertEqual(
            self.wallet.balance,
            10_000,
        )

        self.assertEqual(
            LedgerEntry.objects.filter(
                wallet=self.wallet,
                reference="TEST-DOUBLE-EXECUTION-002",
            ).count(),
            0,
        )

    def test_reversed_transaction_cannot_be_executed(self):
        transaction = self.create_processing_transaction(
            reference="TEST-DOUBLE-EXECUTION-003",
        )

        execute_wallet_debit(
            transaction_id=transaction.id,
        )

        transaction.refresh_from_db()

        transaction.status = Transaction.Status.REVERSED
        transaction.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        with self.assertRaises(TransactionNotProcessableError):
            execute_wallet_debit(
                transaction_id=transaction.id,
            )

        self.wallet.refresh_from_db()

        self.assertEqual(
            self.wallet.balance,
            7_000,
        )

        self.assertEqual(
            LedgerEntry.objects.filter(
                wallet=self.wallet,
                reference="TEST-DOUBLE-EXECUTION-003",
            ).count(),
            1,
        )