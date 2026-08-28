from unittest.mock import patch

from django.test import TestCase

from payments.models import Payment
from payments.services import initialize_paystack_payment
from users.models import User
from wallets.models import Wallet


class PaystackPaymentServiceTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email="paystackservice@balora.com",
            phone_number="08000000141",
            password="TestPassword123!",
        )

        self.wallet = Wallet.objects.create(
            user=self.user,
            balance=10_000,
        )

        self.payment = Payment.objects.create(
            user=self.user,
            wallet=self.wallet,
            provider=Payment.Provider.PAYSTACK,
            reference="BAL-PAY-SERVICE-001",
            amount=5_000,
            status=Payment.Status.PENDING,
            description="Wallet funding",
        )

    @patch("payments.services.requests.post")
    def test_paystack_initialization_returns_authorization_url(
        self,
        mock_post,
    ):
        mock_response = mock_post.return_value

        mock_response.raise_for_status.return_value = None

        mock_response.json.return_value = {
            "status": True,
            "message": "Authorization URL created",
            "data": {
                "authorization_url": (
                    "https://checkout.paystack.com/test123"
                ),
                "access_code": "test_access_code",
                "reference": self.payment.reference,
            },
        }

        result = initialize_paystack_payment(
            self.payment,
        )

        self.assertEqual(
            result["authorization_url"],
            "https://checkout.paystack.com/test123",
        )

        self.assertEqual(
            result["access_code"],
            "test_access_code",
        )

        self.assertEqual(
            result["reference"],
            self.payment.reference,
        )

        mock_post.assert_called_once()

    @patch("payments.services.requests.post")
    def test_paystack_request_contains_correct_amount(
        self,
        mock_post,
    ):
        mock_response = mock_post.return_value

        mock_response.raise_for_status.return_value = None

        mock_response.json.return_value = {
            "status": True,
            "message": "Authorization URL created",
            "data": {
                "authorization_url": (
                    "https://checkout.paystack.com/test123"
                ),
                "access_code": "test_access_code",
                "reference": self.payment.reference,
            },
        }

        initialize_paystack_payment(
            self.payment,
        )

        _, kwargs = mock_post.call_args

        self.assertEqual(
            kwargs["json"]["amount"],
            500_000,
        )

    @patch("payments.services.requests.post")
    def test_paystack_request_contains_payment_reference(
        self,
        mock_post,
    ):
        mock_response = mock_post.return_value

        mock_response.raise_for_status.return_value = None

        mock_response.json.return_value = {
            "status": True,
            "message": "Authorization URL created",
            "data": {
                "authorization_url": (
                    "https://checkout.paystack.com/test123"
                ),
                "access_code": "test_access_code",
                "reference": self.payment.reference,
            },
        }

        initialize_paystack_payment(
            self.payment,
        )

        _, kwargs = mock_post.call_args

        self.assertEqual(
            kwargs["json"]["reference"],
            self.payment.reference,
        )

    @patch("payments.services.requests.post")
    def test_paystack_request_contains_customer_email(
        self,
        mock_post,
    ):
        mock_response = mock_post.return_value

        mock_response.raise_for_status.return_value = None

        mock_response.json.return_value = {
            "status": True,
            "message": "Authorization URL created",
            "data": {
                "authorization_url": (
                    "https://checkout.paystack.com/test123"
                ),
                "access_code": "test_access_code",
                "reference": self.payment.reference,
            },
        }

        initialize_paystack_payment(
            self.payment,
        )

        _, kwargs = mock_post.call_args

        self.assertEqual(
            kwargs["json"]["email"],
            self.user.email,
        )

    @patch("payments.services.requests.post")
    def test_paystack_amount_is_in_kobo(
        self,
        mock_post,
    ):
        mock_response = mock_post.return_value

        mock_response.raise_for_status.return_value = None

        mock_response.json.return_value = {
            "status": True,
            "message": "Authorization URL created",
            "data": {
                "authorization_url": (
                    "https://checkout.paystack.com/test123"
                ),
                "access_code": "test_access_code",
                "reference": self.payment.reference,
            },
        }

        self.payment.amount = 12_345
        self.payment.save()

        initialize_paystack_payment(
            self.payment,
        )

        _, kwargs = mock_post.call_args

        self.assertEqual(
            kwargs["json"]["amount"],
            1_234_500,
        )

    @patch("payments.services.requests.post")
    def test_paystack_failure_raises_error(
        self,
        mock_post,
    ):
        mock_response = mock_post.return_value

        mock_response.raise_for_status.side_effect = Exception(
            "Paystack connection failed"
        )

        with self.assertRaises(Exception):
            initialize_paystack_payment(
                self.payment,
            )

    @patch("payments.services.requests.post")
    def test_unsuccessful_paystack_response_raises_error(
        self,
        mock_post,
    ):
        mock_response = mock_post.return_value

        mock_response.raise_for_status.return_value = None

        mock_response.json.return_value = {
            "status": False,
            "message": "Unable to initialize transaction",
            "data": None,
        }

        with self.assertRaises(Exception):
            initialize_paystack_payment(
                self.payment,
            )

    @patch("payments.services.requests.post")
    def test_paystack_headers_include_secret_key(
        self,
        mock_post,
    ):
        mock_response = mock_post.return_value

        mock_response.raise_for_status.return_value = None

        mock_response.json.return_value = {
            "status": True,
            "message": "Authorization URL created",
            "data": {
                "authorization_url": (
                    "https://checkout.paystack.com/test123"
                ),
                "access_code": "test_access_code",
                "reference": self.payment.reference,
            },
        }

        with patch(
            "payments.services.settings.PAYSTACK_SECRET_KEY",
            "sk_test_balora",
        ):
            initialize_paystack_payment(
                self.payment,
            )

        _, kwargs = mock_post.call_args

        self.assertEqual(
            kwargs["headers"]["Authorization"],
            "Bearer sk_test_balora",
        )

    @patch("payments.services.requests.post")
    def test_paystack_endpoint_is_correct(
        self,
        mock_post,
    ):
        mock_response = mock_post.return_value

        mock_response.raise_for_status.return_value = None

        mock_response.json.return_value = {
            "status": True,
            "message": "Authorization URL created",
            "data": {
                "authorization_url": (
                    "https://checkout.paystack.com/test123"
                ),
                "access_code": "test_access_code",
                "reference": self.payment.reference,
            },
        }

        with patch(
            "payments.services.settings.PAYSTACK_SECRET_KEY",
            "sk_test_balora",
        ):
            initialize_paystack_payment(
                self.payment,
            )

        args, _ = mock_post.call_args

        self.assertEqual(
            args[0],
            "https://api.paystack.co/transaction/initialize",
        )