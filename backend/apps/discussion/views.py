from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from .models import Message
from .serializers import MessageSerializer


@api_view(['GET'])
def message_list(request, session_id):
    """获取某个session的历史消息（分页）"""
    qs = Message.objects.filter(session_id=session_id).select_related('sender')
    paginator = PageNumberPagination()
    paginator.page_size = 50
    page = paginator.paginate_queryset(qs, request)
    serializer = MessageSerializer(page, many=True, context={'request': request})
    return paginator.get_paginated_response(serializer.data)


@api_view(['POST'])
def send_message(request):
    """发送消息（文字或图片）"""
    serializer = MessageSerializer(data=request.data, context={'request': request})
    serializer.is_valid(raise_exception=True)
    msg = serializer.save(sender=request.user)

    # 通过 WebSocket 广播消息
    channel_layer = get_channel_layer()
    group_name = f'chat_{msg.session_id}'
    message_data = {
        'id': msg.id,
        'sender': msg.sender.id,
        'sender_name': msg.sender.get_full_name() or msg.sender.username,
        'sender_role': msg.sender.role,
        'content': msg.content,
        'image_url': request.build_absolute_uri(msg.image.url) if msg.image else None,
        'created_at': str(msg.created_at),
    }
    async_to_sync(channel_layer.group_send)(
        group_name,
        {'type': 'chat_message', 'data': message_data}
    )

    return Response(serializer.data, status=status.HTTP_201_CREATED)
