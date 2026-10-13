from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail

from lms.models import Course, Subscription


@shared_task
def send_course_update_email(course_id):
    course = Course.objects.filter(pk=course_id).first()
    if course is None:
        return 0
    emails = list(
        Subscription.objects.filter(course=course).values_list('user__email', flat=True)
    )
    if not emails:
        return 0
    send_mail(
        subject=f'Обновление курса «{course.name}»',
        message=f'Материалы курса «{course.name}», на который вы подписаны, обновлены.',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=emails,
    )
    return len(emails)
