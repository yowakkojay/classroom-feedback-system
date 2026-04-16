from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator


class Course(models.Model):
    name = models.CharField('课程名称', max_length=100)
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='courses', verbose_name='授课教师'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'course'
        verbose_name = '课程'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class ClassSession(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='sessions')
    start_time = models.DateTimeField('开始时间')
    end_time = models.DateTimeField('结束时间', null=True, blank=True)
    refresh_interval = models.PositiveIntegerField('刷新间隔(分钟)', default=5)
    is_active = models.BooleanField('进行中', default=True)

    class Meta:
        db_table = 'class_session'
        verbose_name = '上课时段'
        verbose_name_plural = verbose_name
        ordering = ['-start_time']

    def __str__(self):
        return f'{self.course.name} - {self.start_time}'


class EmojiReaction(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='reactions', verbose_name='学生'
    )
    session = models.ForeignKey(ClassSession, on_delete=models.CASCADE, related_name='reactions')
    score = models.PositiveIntegerField(
        '分数',
        validators=[MinValueValidator(1), MaxValueValidator(6)]
    )
    time_slot = models.PositiveIntegerField('时段编号', default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'emoji_reaction'
        verbose_name = '表情反馈'
        verbose_name_plural = verbose_name
        unique_together = ['student', 'session', 'time_slot']

    def __str__(self):
        return f'{self.student.username}: {self.score}'
