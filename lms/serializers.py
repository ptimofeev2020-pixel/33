from rest_framework import serializers

from lms.models import Course, Lesson, Subscription
from lms.validators import YoutubeLinkValidator


class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = ['id', 'name', 'description', 'preview', 'video_url', 'course', 'owner']
        read_only_fields = ['owner']
        validators = [
            YoutubeLinkValidator(field='video_url'),
            YoutubeLinkValidator(field='description'),
        ]


class CourseSerializer(serializers.ModelSerializer):
    lesson_count = serializers.SerializerMethodField()
    lessons = LessonSerializer(many=True, read_only=True)
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = ['id', 'name', 'preview', 'description', 'price', 'owner', 'lesson_count', 'lessons', 'is_subscribed']
        read_only_fields = ['owner']
        validators = [YoutubeLinkValidator(field='description')]

    def get_lesson_count(self, obj) -> int:
        return obj.lessons.count()

    def get_is_subscribed(self, obj) -> bool:
        request = self.context.get('request')
        if request is None or not request.user.is_authenticated:
            return False
        return Subscription.objects.filter(user=request.user, course=obj).exists()
