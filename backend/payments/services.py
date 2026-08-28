import requests

from django.conf import settings


PAYSTACK_INITIALIZE_URL = (
    "https://api.paystack.co/transaction/initialize"
)

PAYSTACK_VERIFY_URL = (
    "https://api.paystack.co/transaction/verify/{}"
)


def get_paystack_headers():
    return {
        "Authorization": (
            f"Bearer {settings.PAYSTACK_SECRET_KEY}"
        ),
        "Content-Type": "application/json",
    }


def initialize_paystack_payment(payment):
    amount_in_kobo = int(payment.amount * 100)

    payload = {
        "email": payment.user.email,
        "amount": amount_in_kobo,
        "reference": payment.reference,
    }

    response = requests.post(
        PAYSTACK_INITIALIZE_URL,
        json=payload,
        headers=get_paystack_headers(),
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()

    if not data.get("status"):
        raise Exception(
            data.get(
                "message",
                "Paystack payment initialization failed.",
            )
        )

    payment_data = data.get("data")

    if not payment_data:
        raise Exception(
            "Paystack returned an invalid response."
        )

    return {
        "authorization_url": payment_data[
            "authorization_url"
        ],
        "access_code": payment_data[
            "access_code"
        ],
        "reference": payment_data[
            "reference"
        ],
    }


def verify_paystack_payment(reference):
    response = requests.get(
        PAYSTACK_VERIFY_URL.format(reference),
        headers=get_paystack_headers(),
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()

    if not data.get("status"):
        raise Exception(
            data.get(
                "message",
                "Paystack payment verification failed.",
            )
        )

    payment_data = data.get("data")

    if not payment_data:
        raise Exception(
            "Paystack returned an invalid verification response."
        )

    return payment_data