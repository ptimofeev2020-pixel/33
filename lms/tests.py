from django.contrib.auth.models import Group
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from lms.models import Course, Lesson, Subscription
from users.models import User


class LessonCRUDTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='owner@mail.ru', password='Pass12345!')
        self.other = User.objects.create_user(email='other@mail.ru', password='Pass12345!')
        self.moderator = User.objects.create_user(email='moder@mail.ru', password='Pass12345!')
        moderators, _ = Group.objects.get_or_create(name='moderators')
        self.moderator.groups.add(moderators)

        self.course = Course.objects.create(name='Курс', owner=self.user)
        self.lesson = Lesson.objects.create(
            name='Урок', course=self.course, owner=self.user,
            video_url='https://www.youtube.com/watch?v=abc',
        )
        self.client.force_authenticate(user=self.user)

    def test_lesson_create(self):
        data = {'name': 'Новый урок', 'course': self.course.pk, 'video_url': 'https://youtube.com/watch?v=1'}
        response = self.client.post(reverse('lms:lesson_create'), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Lesson.objects.count(), 2)
        self.assertEqual(response.data['owner'], self.user.pk)

    def test_lesson_create_with_foreign_link(self):
        data = {'name': 'Урок', 'course': self.course.pk, 'video_url': 'https://rutube.ru/video/1'}
        response = self.client.post(reverse('lms:lesson_create'), data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('video_url', response.data)

    def test_lesson_description_with_foreign_link(self):
        data = {'name': 'Урок', 'course': self.course.pk, 'description': 'смотри на https://stepik.org/1'}
        response = self.client.post(reverse('lms:lesson_create'), data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_lesson_list(self):
        response = self.client.get(reverse('lms:lesson_list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertIn('results', response.data)

    def test_lesson_retrieve(self):
        response = self.client.get(reverse('lms:lesson_retrieve', args=[self.lesson.pk]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Урок')

    def test_lesson_update(self):
        response = self.client.patch(reverse('lms:lesson_update', args=[self.lesson.pk]), {'name': 'Изменён'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.lesson.refresh_from_db()
        self.assertEqual(self.lesson.name, 'Изменён')

    def test_lesson_delete(self):
        response = self.client.delete(reverse('lms:lesson_delete', args=[self.lesson.pk]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Lesson.objects.exists())

    def test_other_user_cannot_access_lesson(self):
        self.client.force_authenticate(user=self.other)
        self.assertEqual(
            self.client.get(reverse('lms:lesson_retrieve', args=[self.lesson.pk])).status_code,
            status.HTTP_404_NOT_FOUND,
        )
        self.assertEqual(
            self.client.delete(reverse('lms:lesson_delete', args=[self.lesson.pk])).status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_moderator_can_update_but_not_create_or_delete(self):
        self.client.force_authenticate(user=self.moderator)
        response = self.client.patch(reverse('lms:lesson_update', args=[self.lesson.pk]), {'name': 'Модер'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.post(reverse('lms:lesson_create'), {'name': 'X', 'course': self.course.pk})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        response = self.client.delete(reverse('lms:lesson_delete', args=[self.lesson.pk]))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_access_denied(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(reverse('lms:lesson_list'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class SubscriptionTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='sub@mail.ru', password='Pass12345!')
        self.course = Course.objects.create(name='Курс для подписки', owner=self.user)
        self.client.force_authenticate(user=self.user)
        self.url = reverse('lms:subscription')

    def test_subscribe_and_unsubscribe(self):
        response = self.client.post(self.url, {'course_id': self.course.pk})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Подписка добавлена')
        self.assertTrue(Subscription.objects.filter(user=self.user, course=self.course).exists())

        response = self.client.post(self.url, {'course_id': self.course.pk})
        self.assertEqual(response.data['message'], 'Подписка удалена')
        self.assertFalse(Subscription.objects.filter(user=self.user, course=self.course).exists())

    def test_is_subscribed_flag(self):
        detail = reverse('lms:course-detail', args=[self.course.pk])
        self.assertFalse(self.client.get(detail).data['is_subscribed'])
        self.client.post(self.url, {'course_id': self.course.pk})
        self.assertTrue(self.client.get(detail).data['is_subscribed'])

    def test_subscribe_to_missing_course(self):
        response = self.client.post(self.url, {'course_id': 9999})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class CourseTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='c@mail.ru', password='Pass12345!')
        self.course = Course.objects.create(name='Курс', owner=self.user)
        self.client.force_authenticate(user=self.user)

    def test_course_crud(self):
        response = self.client.post(reverse('lms:course-list'), {'name': 'Новый курс'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response = self.client.get(reverse('lms:course-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        response = self.client.patch(reverse('lms:course-detail', args=[self.course.pk]), {'name': 'Изм'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.delete(reverse('lms:course-detail', args=[self.course.pk]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_pagination_page_size(self):
        for i in range(7):
            Course.objects.create(name=f'К{i}', owner=self.user)
        response = self.client.get(reverse('lms:course-list'))
        self.assertEqual(len(response.data['results']), 5)
        response = self.client.get(reverse('lms:course-list') + '?page_size=10')
        self.assertEqual(len(response.data['results']), 8)
