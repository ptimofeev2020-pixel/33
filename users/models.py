from django.contrib.auth.models import AbstractUser
from django.db import models

from users.managers import UserManager


class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True, verbose_name='Email')
    phone = models.CharField(max_length=35, blank=True, null=True, verbose_name='Телефон')
    city = models.CharField(max_length=100, blank=True, null=True, verbose_name='Город')
    avatar = models.ImageField(upload_to='users/avatars/', blank=True, null=True, verbose_name='Аватар')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.email


class Payment(models.Model):
    METHOD_CASH = 'cash'
    METHOD_TRANSFER = 'transfer'
    METHOD_CHOICES = [
        (METHOD_CASH, 'Наличные'),
        (METHOD_TRANSFER, 'Перевод на счёт'),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='payments', verbose_name='Пользователь'
    )
    payment_date = models.DateTimeField(auto_now_add=True, verbose_name='Дата оплаты')
    paid_course = models.ForeignKey(
        'lms.Course', on_delete=models.SET_NULL, blank=True, null=True,
        related_name='payments', verbose_name='Оплаченный курс',
    )
    paid_lesson = models.ForeignKey(
        'lms.Lesson', on_delete=models.SET_NULL, blank=True, null=True,
        related_name='payments', verbose_name='Оплаченный урок',
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Сумма оплаты')
    payment_method = models.CharField(
        max_length=20, choices=METHOD_CHOICES, default=METHOD_TRANSFER, verbose_name='Способ оплаты'
    )
    stripe_product_id = models.CharField(max_length=255, blank=True, null=True, verbose_name='ID продукта Stripe')
    stripe_price_id = models.CharField(max_length=255, blank=True, null=True, verbose_name='ID цены Stripe')
    session_id = models.CharField(max_length=255, blank=True, null=True, verbose_name='ID сессии Stripe')
    link = models.URLField(max_length=1000, blank=True, null=True, verbose_name='Ссылка на оплату')
    status = models.CharField(max_length=50, blank=True, null=True, verbose_name='Статус оплаты')

    class Meta:
        verbose_name = 'Платёж'
        verbose_name_plural = 'Платежи'

    def __str__(self):
        return f'Платёж {self.amount} от {self.user}'
