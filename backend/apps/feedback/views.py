import math
from io import BytesIO

from django.db.models import Count, Avg, Variance
from django.http import HttpResponse
from django.utils import timezone
from openpyxl import Workbook
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.users.permissions import IsTeacherOrAdmin, IsTeacher
from .models import Course, ClassSession, EmojiReaction
from .serializers import CourseSerializer, ClassSessionSerializer, EmojiReactionSerializer


class CourseViewSet(viewsets.ModelViewSet):
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'teacher':
            return Course.objects.filter(teacher=user)
        return Course.objects.all()

    def perform_create(self, serializer):
        serializer.save(teacher=self.request.user)


class ClassSessionViewSet(viewsets.ModelViewSet):
    serializer_class = ClassSessionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = ClassSession.objects.select_related('course')
        course_id = self.request.query_params.get('course_id')
        if course_id:
            qs = qs.filter(course_id=course_id)
        user = self.request.user
        if user.role == 'teacher':
            qs = qs.filter(course__teacher=user)
        return qs

    @action(detail=True, methods=['post'])
    def end(self, request, pk=None):
        """结束上课时段"""
        session = self.get_object()
        session.is_active = False
        session.end_time = timezone.now()
        session.save()
        return Response(ClassSessionSerializer(session).data)


@api_view(['POST'])
def submit_reaction(request):
    """学生提交表情反馈"""
    session_id = request.data.get('session_id')
    score = request.data.get('score')
    time_slot = request.data.get('time_slot', 0)

    if not session_id or score is None:
        return Response({'detail': '缺少参数'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        session = ClassSession.objects.get(id=session_id, is_active=True)
    except ClassSession.DoesNotExist:
        return Response({'detail': '上课时段不存在或已结束'}, status=status.HTTP_404_NOT_FOUND)

    reaction, created = EmojiReaction.objects.update_or_create(
        student=request.user,
        session=session,
        time_slot=time_slot,
        defaults={'score': score},
    )
    return Response(EmojiReactionSerializer(reaction).data)


@api_view(['GET'])
def session_statistics(request, session_id):
    """获取某个时段的统计数据"""
    time_slot = request.query_params.get('time_slot')
    qs = EmojiReaction.objects.filter(session_id=session_id)
    if time_slot is not None:
        qs = qs.filter(time_slot=time_slot)

    total = qs.count()
    if total == 0:
        return Response({
            'total_students': 0,
            'distribution': {str(i): 0 for i in range(1, 7)},
            'average': 0,
            'variance': 0,
        })

    agg = qs.aggregate(avg=Avg('score'), var=Variance('score'))
    distribution = dict(
        qs.values('score').annotate(count=Count('id')).values_list('score', 'count')
    )
    dist_full = {str(i): distribution.get(i, 0) for i in range(1, 7)}

    return Response({
        'total_students': total,
        'distribution': dist_full,
        'average': round(agg['avg'] or 0, 2),
        'variance': round(agg['var'] or 0, 2),
    })


@api_view(['GET'])
def session_statistics_by_slots(request, session_id):
    """获取某个session所有时段的统计数据（用于图表展示）"""
    slots = (
        EmojiReaction.objects.filter(session_id=session_id)
        .values('time_slot')
        .annotate(
            total=Count('id'),
            avg=Avg('score'),
            var=Variance('score'),
        )
        .order_by('time_slot')
    )

    result = []
    for slot in slots:
        dist_qs = (
            EmojiReaction.objects.filter(session_id=session_id, time_slot=slot['time_slot'])
            .values('score')
            .annotate(count=Count('id'))
        )
        dist = {str(i): 0 for i in range(1, 7)}
        for row in dist_qs:
            dist[str(row['score'])] = row['count']

        result.append({
            'time_slot': slot['time_slot'],
            'total_students': slot['total'],
            'average': round(slot['avg'] or 0, 2),
            'variance': round(slot['var'] or 0, 2),
            'distribution': dist,
        })

    return Response(result)


@api_view(['GET'])
def history_query(request):
    """历史查询：按课程名称和时间范围"""
    course_name = request.query_params.get('course_name', '')
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')

    qs = ClassSession.objects.select_related('course').all()
    if course_name:
        qs = qs.filter(course__name__icontains=course_name)
    if start_date:
        qs = qs.filter(start_time__date__gte=start_date)
    if end_date:
        qs = qs.filter(start_time__date__lte=end_date)

    results = []
    for session in qs:
        reactions = EmojiReaction.objects.filter(session=session)
        total = reactions.count()
        agg = reactions.aggregate(avg=Avg('score'), var=Variance('score'))
        results.append({
            'session': ClassSessionSerializer(session).data,
            'total_students': total,
            'average': round(agg['avg'] or 0, 2),
            'variance': round(agg['var'] or 0, 2),
        })

    return Response(results)


@api_view(['GET'])
def export_excel(request, session_id):
    """导出某个session的统计数据为Excel"""
    session = ClassSession.objects.select_related('course').get(id=session_id)
    reactions = EmojiReaction.objects.filter(session=session).select_related('student')

    wb = Workbook()
    ws = wb.active
    ws.title = '表情反馈统计'

    # 基本信息
    ws.append(['课程名称', session.course.name])
    ws.append(['开始时间', str(session.start_time)])
    ws.append(['结束时间', str(session.end_time or '进行中')])
    ws.append([])

    # 统计概览
    total = reactions.count()
    agg = reactions.aggregate(avg=Avg('score'), var=Variance('score'))
    ws.append(['统计概览'])
    ws.append(['参与人数', total])
    ws.append(['平均分', round(agg['avg'] or 0, 2)])
    ws.append(['方差', round(agg['var'] or 0, 2)])
    ws.append([])

    # 各分数段人数
    ws.append(['分数段分布'])
    ws.append(['分数', '人数'])
    dist = dict(
        reactions.values('score').annotate(count=Count('id')).values_list('score', 'count')
    )
    for i in range(1, 7):
        ws.append([i, dist.get(i, 0)])
    ws.append([])

    # 明细
    ws.append(['学生', '分数', '时段', '提交时间'])
    for r in reactions.order_by('time_slot', 'created_at'):
        ws.append([
            r.student.username,
            r.score,
            r.time_slot,
            str(r.created_at),
        ])

    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    response = HttpResponse(
        buffer.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = f'attachment; filename="session_{session_id}.xlsx"'
    return response
