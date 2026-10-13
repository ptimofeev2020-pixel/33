from datetime import timedelta

from django.utils import timezone

from lms.tasks import send_course_update_email

NOTIFY_INTERVAL = timedelta(hours=4)


def notify_course_updated(course):
    now = timezone.now()
    should_notify = course.updated_at is None or now - course.updated_at > NOTIFY_INTERVAL
    course.updated_at = now
    course.save(update_fields=['updated_at'])
    if should_notify:
        send_course_update_email.delay(course.pk)
    return should_notify
