from datetime import timedelta

from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from lms.models import Course, Lesson, Subscription
from lms.services import notify_course_updated
from lms.tasks import send_course_update_email
from users.models import User
from users.tasks import block_inactive_users


@override_settings(CELERY_TASK_ALWAYS_EAGER=True, EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class CourseUpdateEmailTestCase(APITestCase):
    def setUp(self):
        from config.celery import app
        app.conf.task_always_eager = True
        self.owner = User.objects.create_user(email='owner@mail.ru', password='Pass12345!')
        self.subscriber = User.objects.create_user(email='sub@mail.ru', password='Pass12345!')
        self.course = Course.objects.create(name='Курс', owner=self.owner)
        self.lesson = Lesson.objects.create(name='Урок', course=self.course, owner=self.owner)
        Subscription.objects.create(user=self.subscriber, course=self.course)
        self.client.force_authenticate(user=self.owner)

    def test_task_sends_email_to_subscribers(self):
        sent = send_course_update_email(self.course.pk)
        self.assertEqual(sent, 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['sub@mail.ru'])

    def test_course_update_triggers_email(self):
        response = self.client.patch(reverse('lms:course-detail', args=[self.course.pk]), {'name': 'Новое'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)

    def test_lesson_update_triggers_email(self):
        response = self.client.patch(reverse('lms:lesson_update', args=[self.lesson.pk]), {'name': 'Новый урок'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)

    def test_no_email_if_updated_less_than_4_hours_ago(self):
        self.course.updated_at = timezone.now() - timedelta(hours=1)
        self.course.save()
        self.assertFalse(notify_course_updated(self.course))
        self.assertEqual(len(mail.outbox), 0)

    def test_email_if_updated_more_than_4_hours_ago(self):
        self.course.updated_at = timezone.now() - timedelta(hours=5)
        self.course.save()
        self.assertTrue(notify_course_updated(self.course))
        self.assertEqual(len(mail.outbox), 1)

    def test_failed_update_does_not_send(self):
        response = self.client.patch(
            reverse('lms:lesson_update', args=[self.lesson.pk]), {'video_url': 'https://rutube.ru/1'}
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(len(mail.outbox), 0)


class BlockInactiveUsersTestCase(TestCase):
    def test_blocks_users_inactive_more_than_month(self):
        old = User.objects.create_user(email='old@mail.ru', password='Pass12345!')
        old.last_login = timezone.now() - timedelta(days=40)
        old.save()
        fresh = User.objects.create_user(email='fresh@mail.ru', password='Pass12345!')
        fresh.last_login = timezone.now() - timedelta(days=5)
        fresh.save()
        never = User.objects.create_user(email='never@mail.ru', password='Pass12345!')

        blocked = block_inactive_users()

        self.assertEqual(blocked, 1)
        old.refresh_from_db(); fresh.refresh_from_db(); never.refresh_from_db()
        self.assertFalse(old.is_active)
        self.assertTrue(fresh.is_active)
        self.assertTrue(never.is_active)

    def test_beat_schedule_and_timezone(self):
        from django.conf import settings
        self.assertIn('block-inactive-users', settings.CELERY_BEAT_SCHEDULE)
        self.assertEqual(settings.CELERY_TIMEZONE, settings.TIME_ZONE)
