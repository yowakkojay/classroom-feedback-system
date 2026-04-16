from rest_framework import serializers
from .models import User, StudentProfile, TeacherProfile


class StudentProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentProfile
        fields = ['student_number', 'grade', 'class_name', 'major']


class TeacherProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeacherProfile
        fields = ['title']


class UserSerializer(serializers.ModelSerializer):
    student_profile = StudentProfileSerializer(read_only=True)
    teacher_profile = TeacherProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'first_name', 'last_name', 'role',
            'phone', 'age', 'gender', 'is_active',
            'student_profile', 'teacher_profile',
        ]
        read_only_fields = ['id']


class UserCreateSerializer(serializers.ModelSerializer):
    """用于管理员创建用户"""
    password = serializers.CharField(write_only=True, min_length=6)
    student_number = serializers.CharField(required=False, allow_blank=True)
    grade = serializers.CharField(required=False, allow_blank=True, default='')
    class_name = serializers.CharField(required=False, allow_blank=True, default='')
    major = serializers.CharField(required=False, allow_blank=True, default='')
    title = serializers.CharField(required=False, allow_blank=True, default='')

    class Meta:
        model = User
        fields = [
            'username', 'password', 'first_name', 'last_name',
            'role', 'phone', 'age', 'gender',
            'student_number', 'grade', 'class_name', 'major', 'title',
        ]

    def validate(self, attrs):
        if attrs.get('role') == 'student' and not attrs.get('student_number'):
            raise serializers.ValidationError({'student_number': '学生必须提供学号'})
        return attrs

    def create(self, validated_data):
        student_number = validated_data.pop('student_number', None)
        grade = validated_data.pop('grade', '')
        class_name = validated_data.pop('class_name', '')
        major = validated_data.pop('major', '')
        title = validated_data.pop('title', '')
        password = validated_data.pop('password')

        user = User(**validated_data)
        user.set_password(password)
        user.save()

        if user.role == 'student' and student_number:
            StudentProfile.objects.create(
                user=user,
                student_number=student_number,
                grade=grade,
                class_name=class_name,
                major=major,
            )
        elif user.role in ('teacher', 'admin'):
            TeacherProfile.objects.create(user=user, title=title)

        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """用于管理员更新用户"""
    password = serializers.CharField(write_only=True, required=False, min_length=6)
    student_number = serializers.CharField(required=False, allow_blank=True)
    grade = serializers.CharField(required=False, allow_blank=True)
    class_name = serializers.CharField(required=False, allow_blank=True)
    major = serializers.CharField(required=False, allow_blank=True)
    title = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = [
            'username', 'password', 'first_name', 'last_name',
            'role', 'phone', 'age', 'gender',
            'student_number', 'grade', 'class_name', 'major', 'title',
        ]

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        student_fields = {
            k: validated_data.pop(k) for k in ['student_number', 'grade', 'class_name', 'major']
            if k in validated_data
        }
        title = validated_data.pop('title', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()

        if instance.role == 'student' and student_fields:
            StudentProfile.objects.update_or_create(
                user=instance, defaults=student_fields
            )
        if instance.role in ('teacher', 'admin') and title is not None:
            TeacherProfile.objects.update_or_create(
                user=instance, defaults={'title': title}
            )

        return instance


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()
