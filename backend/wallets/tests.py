from django.test import TestCase

from users.models import User
from wallets.models import LedgerEntry, Wallet
from wallets.services import (
    InsufficientFundsError,
    WalletInactiveError,
    WalletError,
    credit_wallet,
    debit_wallet,
)


class WalletServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="testuser@balora.com",
            phone_number="08000000001",
            password="TestPassword123!",
        )

        self.wallet = Wallet.objects.create(
            user=self.user,
        )

    def test_credit_wallet(self):
        wallet, entry = credit_wallet(
            wallet_id=self.wallet.id,
            amount=1_000_000,
            reference="TEST-CREDIT-001",
            description="Test credit",
        )

        self.assertEqual(wallet.balance, 1_000_000)
        self.assertEqual(entry.entry_type, LedgerEntry.EntryType.CREDIT)
        self.assertEqual(entry.balance_before, 0)
        self.assertEqual(entry.balance_after, 1_000_000)

    def test_debit_wallet(self):
        credit_wallet(
            wallet_id=self.wallet.id,
            amount=1_000_000,
            reference="TEST-CREDIT-002",
            description="Initial balance",
        )

        wallet, entry = debit_wallet(
            wallet_id=self.wallet.id,
            amount=300_000,
            reference="TEST-DEBIT-001",
            description="Test debit",
        )

        self.assertEqual(wallet.balance, 700_000)
        self.assertEqual(entry.entry_type, LedgerEntry.EntryType.DEBIT)
        self.assertEqual(entry.balance_before, 1_000_000)
        self.assertEqual(entry.balance_after, 700_000)

    def test_insufficient_funds(self):
        with self.assertRaises(InsufficientFundsError):
            debit_wallet(
                wallet_id=self.wallet.id,
                amount=1,
                reference="TEST-INSUFFICIENT-001",
                description="Insufficient funds",
            )

        self.wallet.refresh_from_db()

        self.assertEqual(self.wallet.balance, 0)

        self.assertFalse(
            LedgerEntry.objects.filter(
                reference="TEST-INSUFFICIENT-001"
            ).exists()
        )

    def test_duplicate_reference_does_not_credit_twice(self):
        credit_wallet(
            wallet_id=self.wallet.id,
            amount=1_000_000,
            reference="TEST-DUPLICATE-001",
            description="First credit",
        )

        credit_wallet(
            wallet_id=self.wallet.id,
            amount=1_000_000,
            reference="TEST-DUPLICATE-001",
            description="Duplicate credit",
        )

        self.wallet.refresh_from_db()

        self.assertEqual(self.wallet.balance, 1_000_000)

        self.assertEqual(
            LedgerEntry.objects.filter(
                reference="TEST-DUPLICATE-001"
            ).count(),
            1,
        )

    def test_inactive_wallet_cannot_be_credited(self):
        self.wallet.is_active = False
        self.wallet.save(update_fields=["is_active"])

        with self.assertRaises(WalletInactiveError):
            credit_wallet(
                wallet_id=self.wallet.id,
                amount=1_000_000,
                reference="TEST-INACTIVE-CREDIT-001",
                description="Inactive wallet",
            )

        self.wallet.refresh_from_db()

        self.assertEqual(self.wallet.balance, 0)

    def test_inactive_wallet_cannot_be_debited(self):
        self.wallet.is_active = False
        self.wallet.save(update_fields=["is_active"])

        with self.assertRaises(WalletInactiveError):
            debit_wallet(
                wallet_id=self.wallet.id,
                amount=1,
                reference="TEST-INACTIVE-DEBIT-001",
                description="Inactive wallet",
            )

        self.wallet.refresh_from_db()

        self.assertEqual(self.wallet.balance, 0)

    def test_reference_cannot_be_used_for_another_wallet(self):
        other_user = User.objects.create_user(
            email="otheruser@balora.com",
            phone_number="08000000002",
            password="TestPassword123!",
        )

        other_wallet = Wallet.objects.create(
            user=other_user,
        )

        credit_wallet(
            wallet_id=self.wallet.id,
            amount=1_000_000,
            reference="TEST-REFERENCE-001",
            description="Original transaction",
        )

        with self.assertRaises(WalletError):
            credit_wallet(
                wallet_id=other_wallet.id,
                amount=1_000_000,
                reference="TEST-REFERENCE-001",
                description="Reference reuse attack",
            )

        self.wallet.refresh_from_db()
        other_wallet.refresh_from_db()

        self.assertEqual(self.wallet.balance, 1_000_000)
        self.assertEqual(other_wallet.balance, 0)

    def test_ledger_balance_chain_is_consistent(self):
        credit_wallet(
            wallet_id=self.wallet.id,
            amount=1_000_000,
            reference="TEST-INTEGRITY-CREDIT",
            description="Integrity credit",
        )

        debit_wallet(
            wallet_id=self.wallet.id,
            amount=300_000,
            reference="TEST-INTEGRITY-DEBIT",
            description="Integrity debit",
        )

        entries = LedgerEntry.objects.filter(
            wallet=self.wallet
        ).order_by("created_at", "id")

        self.assertEqual(entries.count(), 2)

        first_entry = entries[0]
        second_entry = entries[1]

        self.assertEqual(
            first_entry.balance_before,
            0,
        )

        self.assertEqual(
            first_entry.balance_after,
            1_000_000,
        )

        self.assertEqual(
            second_entry.balance_before,
            first_entry.balance_after,
        )

        self.assertEqual(
            second_entry.balance_after,
            700_000,
        )

        self.wallet.refresh_from_db()

        self.assertEqual(
            self.wallet.balance,
            second_entry.balance_after,
        )