from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = [
        ('student', '学生'),
        ('teacher', '教师'),
        ('admin', '管理员'),
    ]
    role = models.CharField('角色', max_length=10, choices=ROLE_CHOICES, default='student')
    phone = models.CharField('联系方式', max_length=20, blank=True, default='')
    age = models.PositiveIntegerField('年龄', null=True, blank=True)
    gender = models.CharField('性别', max_length=2, choices=[('M', '男'), ('F', '女')], blank=True, default='')
    github_id = models.PositiveBigIntegerField('GitHub ID', null=True, blank=True, unique=True)

    class Meta:
        db_table = 'user'
        verbose_name = '用户'
        verbose_name_plural = verbose_name


class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    student_number = models.CharField('学号', max_length=30, unique=True)
    grade = models.CharField('年级', max_length=20, blank=True, default='')
    class_name = models.CharField('班级', max_length=50, blank=True, default='')
    major = models.CharField('专业', max_length=50, blank=True, default='')

    class Meta:
        db_table = 'student_profile'
        verbose_name = '学生信息'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'{self.user.get_full_name()} - {self.student_number}'


class TeacherProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher_profile')
    title = models.CharField('职称', max_length=30, blank=True, default='')

    class Meta:
        db_table = 'teacher_profile'
        verbose_name = '教师信息'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.user.get_full_name()
