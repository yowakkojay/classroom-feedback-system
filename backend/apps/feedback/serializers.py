from rest_framework import serializers
from .models import Course, ClassSession, EmojiReaction


class CourseSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source='teacher.get_full_name', read_only=True)

    class Meta:
        model = Course
        fields = ['id', 'name', 'teacher', 'teacher_name', 'created_at']
        read_only_fields = ['id', 'teacher', 'created_at']


class ClassSessionSerializer(serializers.ModelSerializer):
    course_name = serializers.CharField(source='course.name', read_only=True)

    class Meta:
        model = ClassSession
        fields = [
            'id', 'course', 'course_name', 'start_time', 'end_time',
            'refresh_interval', 'is_active',
        ]
        read_only_fields = ['id']


class EmojiReactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmojiReaction
        fields = ['id', 'student', 'session', 'score', 'time_slot', 'created_at']
        read_only_fields = ['id', 'student', 'created_at']
