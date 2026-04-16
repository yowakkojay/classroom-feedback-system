from django.urls import path
from . import views

urlpatterns = [
    path('messages/<int:session_id>/', views.message_list, name='message-list'),
    path('send/', views.send_message, name='send-message'),
]
