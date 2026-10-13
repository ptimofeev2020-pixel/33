from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from users.models import User


class UserTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='u@mail.ru', password='Pass12345!', last_name='Иванов')
        self.other = User.objects.create_user(email='o@mail.ru', password='Pass12345!')

    def test_register(self):
        response = self.client.post(reverse('users:register'), {'email': 'new@mail.ru', 'password': 'Pass12345!'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotIn('password', response.data)

    def test_register_duplicate_email(self):
        response = self.client.post(reverse('users:register'), {'email': 'u@mail.ru', 'password': 'Pass12345!'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_returns_tokens(self):
        response = self.client.post(reverse('users:login'), {'email': 'u@mail.ru', 'password': 'Pass12345!'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_own_profile_full(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse('users:user-detail', args=[self.user.pk]))
        self.assertIn('payments', response.data)
        self.assertIn('last_name', response.data)

    def test_other_profile_public_only(self):
        self.client.force_authenticate(user=self.other)
        response = self.client.get(reverse('users:user-detail', args=[self.user.pk]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn('payments', response.data)
        self.assertNotIn('last_name', response.data)
        self.assertNotIn('password', response.data)

    def test_edit_only_own_profile(self):
        self.client.force_authenticate(user=self.other)
        response = self.client.patch(reverse('users:user-detail', args=[self.user.pk]), {'city': 'X'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        response = self.client.patch(reverse('users:user-detail', args=[self.other.pk]), {'city': 'Казань'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_payments_list(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse('users:payment_list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)


from decimal import Decimal
from unittest.mock import patch

from lms.models import Course
from users.models import Payment
from users.services import StripeServiceError, convert_rub_to_kopecks


class StripePaymentTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='pay@mail.ru', password='Pass12345!')
        self.course = Course.objects.create(name='Платный курс', price='1500.50', owner=self.user)
        self.client.force_authenticate(user=self.user)

    def test_convert_to_kopecks(self):
        self.assertEqual(convert_rub_to_kopecks('1500.50'), 150050)

    @patch('users.views.create_stripe_session', return_value=('cs_test_1', 'https://checkout.stripe.com/pay/cs_test_1'))
    @patch('users.views.create_stripe_price', return_value='price_1')
    @patch('users.views.create_stripe_product', return_value='prod_1')
    def test_create_payment(self, mock_product, mock_price, mock_session):
        response = self.client.post(reverse('users:payment_create'), {'course_id': self.course.pk})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['link'], 'https://checkout.stripe.com/pay/cs_test_1')
        mock_price.assert_called_once_with('prod_1', Decimal('1500.50'))
        payment = Payment.objects.get()
        self.assertEqual(payment.user, self.user)
        self.assertEqual(payment.paid_course, self.course)
        self.assertEqual(payment.session_id, 'cs_test_1')
        self.assertEqual(payment.stripe_price_id, 'price_1')

    @patch('users.views.create_stripe_product', side_effect=StripeServiceError('Ошибка Stripe'))
    def test_create_payment_stripe_error(self, mock_product):
        response = self.client.post(reverse('users:payment_create'), {'course_id': self.course.pk})
        self.assertEqual(response.status_code, status.HTTP_502_BAD_GATEWAY)
        self.assertFalse(Payment.objects.exists())

    def test_create_payment_free_course(self):
        free = Course.objects.create(name='Бесплатный', owner=self.user)
        response = self.client.post(reverse('users:payment_create'), {'course_id': free.pk})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('users.views.retrieve_stripe_session', return_value=('complete', 'paid'))
    def test_payment_status(self, mock_retrieve):
        payment = Payment.objects.create(
            user=self.user, paid_course=self.course, amount=self.course.price, session_id='cs_test_1', status='open',
        )
        response = self.client.get(reverse('users:payment_status', args=[payment.pk]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payment.refresh_from_db()
        self.assertEqual(payment.status, 'paid')


class DocsTestCase(APITestCase):
    def test_docs_available(self):
        for name in ('schema', 'swagger-ui', 'redoc'):
            self.assertEqual(self.client.get(reverse(name)).status_code, status.HTTP_200_OK)
