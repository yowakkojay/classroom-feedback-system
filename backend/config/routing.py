from django.urls import path

from apps.feedback.consumers import FeedbackConsumer
from apps.discussion.consumers import ChatConsumer

websocket_urlpatterns = [
    path('ws/feedback/<int:session_id>/', FeedbackConsumer.as_asgi()),
    path('ws/chat/<int:session_id>/', ChatConsumer.as_asgi()),
]
