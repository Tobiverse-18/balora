from django.test import TestCase

from users.models import User
from wallets.models import Transaction, Wallet
from wallets.transaction_service import (
    InvalidTransactionStateError,
    TransactionReferenceExistsError,
    create_transaction,
    mark_transaction_failed,
    mark_transaction_processing,
    mark_transaction_reversed,
    mark_transaction_success,
)


class TransactionServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="transactiontest@balora.com",
            phone_number="08000000021",
            password="TestPassword123!",
        )

        self.wallet = Wallet.objects.create(
            user=self.user,
        )

    def create_test_transaction(
        self,
        reference="TEST-TRANSACTION-001",
    ):
        return create_transaction(
            wallet_id=self.wallet.id,
            transaction_type=Transaction.TransactionType.AIRTIME,
            amount=1_000,
            reference=reference,
            description="Transaction service test",
        )

    def test_transaction_starts_as_pending(self):
        transaction = self.create_test_transaction()

        self.assertEqual(
            transaction.status,
            Transaction.Status.PENDING,
        )

    def test_pending_can_move_to_processing(self):
        transaction = self.create_test_transaction()

        transaction = mark_transaction_processing(
            transaction_id=transaction.id,
        )

        self.assertEqual(
            transaction.status,
            Transaction.Status.PROCESSING,
        )

    def test_processing_can_move_to_success(self):
        transaction = self.create_test_transaction()

        mark_transaction_processing(
            transaction_id=transaction.id,
        )

        transaction = mark_transaction_success(
            transaction_id=transaction.id,
        )

        self.assertEqual(
            transaction.status,
            Transaction.Status.SUCCESS,
        )

    def test_processing_can_move_to_failed(self):
        transaction = self.create_test_transaction()

        mark_transaction_processing(
            transaction_id=transaction.id,
        )

        transaction = mark_transaction_failed(
            transaction_id=transaction.id,
        )

        self.assertEqual(
            transaction.status,
            Transaction.Status.FAILED,
        )

    def test_success_can_move_to_reversed(self):
        transaction = self.create_test_transaction()

        mark_transaction_processing(
            transaction_id=transaction.id,
        )

        mark_transaction_success(
            transaction_id=transaction.id,
        )

        transaction = mark_transaction_reversed(
            transaction_id=transaction.id,
        )

        self.assertEqual(
            transaction.status,
            Transaction.Status.REVERSED,
        )

    def test_pending_cannot_move_directly_to_success(self):
        transaction = self.create_test_transaction()

        with self.assertRaises(InvalidTransactionStateError):
            mark_transaction_success(
                transaction_id=transaction.id,
            )

    def test_pending_cannot_move_directly_to_failed(self):
        transaction = self.create_test_transaction()

        with self.assertRaises(InvalidTransactionStateError):
            mark_transaction_failed(
                transaction_id=transaction.id,
            )

    def test_failed_cannot_move_to_success(self):
        transaction = self.create_test_transaction()

        mark_transaction_processing(
            transaction_id=transaction.id,
        )

        mark_transaction_failed(
            transaction_id=transaction.id,
        )

        with self.assertRaises(InvalidTransactionStateError):
            mark_transaction_success(
                transaction_id=transaction.id,
            )

    def test_failed_cannot_move_to_reversed(self):
        transaction = self.create_test_transaction()

        mark_transaction_processing(
            transaction_id=transaction.id,
        )

        mark_transaction_failed(
            transaction_id=transaction.id,
        )

        with self.assertRaises(InvalidTransactionStateError):
            mark_transaction_reversed(
                transaction_id=transaction.id,
            )

    def test_reversed_cannot_move_to_success(self):
        transaction = self.create_test_transaction()

        mark_transaction_processing(
            transaction_id=transaction.id,
        )

        mark_transaction_success(
            transaction_id=transaction.id,
        )

        mark_transaction_reversed(
            transaction_id=transaction.id,
        )

        with self.assertRaises(InvalidTransactionStateError):
            mark_transaction_success(
                transaction_id=transaction.id,
            )

    def test_duplicate_reference_returns_existing_transaction(self):
        first = self.create_test_transaction(
            reference="TEST-DUPLICATE-TX-001",
        )

        second = self.create_test_transaction(
            reference="TEST-DUPLICATE-TX-001",
        )

        self.assertEqual(
            first.id,
            second.id,
        )

        self.assertEqual(
            Transaction.objects.filter(
                reference="TEST-DUPLICATE-TX-001"
            ).count(),
            1,
        )

    def test_reference_cannot_be_reused_by_another_wallet(self):
        other_user = User.objects.create_user(
            email="transactionother@balora.com",
            phone_number="08000000022",
            password="TestPassword123!",
        )

        other_wallet = Wallet.objects.create(
            user=other_user,
        )

        create_transaction(
            wallet_id=self.wallet.id,
            transaction_type=Transaction.TransactionType.AIRTIME,
            amount=1_000,
            reference="TEST-REFERENCE-ATTACK-001",
            description="Original transaction",
        )

        with self.assertRaises(TransactionReferenceExistsError):
            create_transaction(
                wallet_id=other_wallet.id,
                transaction_type=Transaction.TransactionType.AIRTIME,
                amount=1_000,
                reference="TEST-REFERENCE-ATTACK-001",
                description="Reference attack",
            )