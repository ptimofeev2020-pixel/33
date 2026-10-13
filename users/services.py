from decimal import Decimal

import stripe
from django.conf import settings

stripe.api_key = settings.STRIPE_API_KEY


class StripeServiceError(Exception):
    pass


def convert_rub_to_kopecks(amount):
    return int(Decimal(amount) * 100)


def create_stripe_product(name):
    try:
        product = stripe.Product.create(name=name)
    except stripe.error.StripeError as error:
        raise StripeServiceError(f'Не удалось создать продукт в Stripe: {error.user_message or error}')
    return product.get('id')


def create_stripe_price(product_id, amount):
    try:
        price = stripe.Price.create(
            currency='rub',
            unit_amount=convert_rub_to_kopecks(amount),
            product=product_id,
        )
    except stripe.error.StripeError as error:
        raise StripeServiceError(f'Не удалось создать цену в Stripe: {error.user_message or error}')
    return price.get('id')


def create_stripe_session(price_id):
    try:
        session = stripe.checkout.Session.create(
            success_url=settings.PAYMENT_SUCCESS_URL,
            cancel_url=settings.PAYMENT_CANCEL_URL,
            line_items=[{'price': price_id, 'quantity': 1}],
            mode='payment',
        )
    except stripe.error.StripeError as error:
        raise StripeServiceError(f'Не удалось создать сессию оплаты в Stripe: {error.user_message or error}')
    return session.get('id'), session.get('url')


def retrieve_stripe_session(session_id):
    try:
        session = stripe.checkout.Session.retrieve(session_id)
    except stripe.error.StripeError as error:
        raise StripeServiceError(f'Не удалось получить сессию Stripe: {error.user_message or error}')
    return session.get('status'), session.get('payment_status')
