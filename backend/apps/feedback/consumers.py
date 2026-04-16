import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.db.models import Count, Avg, Variance


class FeedbackConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.group_name = f'feedback_{self.session_id}'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        if data.get('type') == 'request_stats':
            stats = await self.get_statistics(data.get('time_slot'))
            await self.send(text_data=json.dumps({
                'type': 'statistics',
                'data': stats,
            }))

    async def statistics_update(self, event):
        """当有新的表情反馈时推送统计更新"""
        await self.send(text_data=json.dumps({
            'type': 'statistics',
            'data': event['data'],
        }))

    @database_sync_to_async
    def get_statistics(self, time_slot=None):
        from .models import EmojiReaction
        qs = EmojiReaction.objects.filter(session_id=self.session_id)
        if time_slot is not None:
            qs = qs.filter(time_slot=time_slot)

        total = qs.count()
        if total == 0:
            return {
                'total_students': 0,
                'distribution': {str(i): 0 for i in range(1, 7)},
                'average': 0,
                'variance': 0,
            }

        agg = qs.aggregate(avg=Avg('score'), var=Variance('score'))
        distribution = dict(
            qs.values('score').annotate(count=Count('id')).values_list('score', 'count')
        )
        return {
            'total_students': total,
            'distribution': {str(i): distribution.get(i, 0) for i in range(1, 7)},
            'average': round(agg['avg'] or 0, 2),
            'variance': round(agg['var'] or 0, 2),
        }
