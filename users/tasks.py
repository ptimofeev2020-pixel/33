from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from users.models import User


@shared_task
def block_inactive_users():
    month_ago = timezone.now() - timedelta(days=30)
    return User.objects.filter(
        is_active=True,
        is_superuser=False,
        last_login__lt=month_ago,
    ).update(is_active=False)
