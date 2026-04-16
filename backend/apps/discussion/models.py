from django.db import models
from django.conf import settings
from apps.feedback.models import ClassSession


class Message(models.Model):
    session = models.ForeignKey(
        ClassSession, on_delete=models.CASCADE,
        related_name='messages', verbose_name='上课时段'
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='messages', verbose_name='发送者'
    )
    content = models.TextField('内容', blank=True, default='')
    image = models.ImageField('图片', upload_to='chat_images/%Y/%m/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'message'
        verbose_name = '讨论消息'
        verbose_name_plural = verbose_name
        ordering = ['created_at']

    def __str__(self):
        return f'{self.sender.username}: {self.content[:30]}'
