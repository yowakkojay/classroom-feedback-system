from django.contrib.auth import authenticate
import requests as http_requests
from django.conf import settings
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User
from .serializers import (
    UserSerializer, UserCreateSerializer, UserUpdateSerializer, LoginSerializer
)
from .permissions import IsAdmin


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """密码登录，返回JWT token"""
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    user = authenticate(
        username=serializer.validated_data['username'],
        password=serializer.validated_data['password'],
    )
    if not user:
        return Response({'detail': '用户名或密码错误'}, status=status.HTTP_401_UNAUTHORIZED)

    refresh = RefreshToken.for_user(user)
    return Response({
        'access': str(refresh.access_token),
        'refresh': str(refresh),
        'user': UserSerializer(user).data,
    })


@api_view(['GET'])
def me_view(request):
    """获取当前登录用户信息"""
    return Response(UserSerializer(request.user).data)


class UserViewSet(viewsets.ModelViewSet):
    """管理员用户管理 CRUD"""
    queryset = User.objects.all().order_by('id')
    permission_classes = [IsAdmin]

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        if self.action in ('update', 'partial_update'):
            return UserUpdateSerializer
        return UserSerializer

    def get_queryset(self):
        from django.db.models import Q
        qs = super().get_queryset()
        role = self.request.query_params.get('role')
        keyword = self.request.query_params.get('keyword')
        if role:
            qs = qs.filter(role=role)
        if keyword:
            qs = qs.filter(
                Q(username__icontains=keyword) | Q(first_name__icontains=keyword)
            )
        return qs

    @action(detail=False, methods=['get'])
    def search(self, request):
        """搜索用户: ?keyword=xxx&role=xxx"""
        keyword = request.query_params.get('keyword', '')
        qs = self.get_queryset()
        if keyword:
            from django.db.models import Q
            qs = qs.filter(
                Q(username__icontains=keyword) |
                Q(first_name__icontains=keyword) |
                Q(last_name__icontains=keyword) |
                Q(phone__icontains=keyword)
            )
        page = self.paginate_queryset(qs)
        if page is not None:
            return self.get_paginated_response(UserSerializer(page, many=True).data)
        return Response(UserSerializer(qs, many=True).data)


@api_view(['POST'])
@permission_classes([AllowAny])
def github_login(request):
    """GitHub OAuth 登录：仅关联已有账号，不自动创建"""
    code = request.data.get('code')
    if not code:
        return Response({'detail': '缺少授权码'}, status=status.HTTP_400_BAD_REQUEST)

    # 1) 用 code 换 GitHub access_token
    try:
        token_resp = http_requests.post(
            'https://github.com/login/oauth/access_token',
            data={
                'client_id': settings.GITHUB_CLIENT_ID,
                'client_secret': settings.GITHUB_CLIENT_SECRET,
                'code': code,
            },
            headers={'Accept': 'application/json'},
            proxies=settings.PROXIES,
            timeout=15,
        )
    except http_requests.exceptions.RequestException:
        return Response(
            {'detail': '无法连接 GitHub，请检查网络或代理设置后重试'},
            status=status.HTTP_502_BAD_GATEWAY,
        )

    gh_token = token_resp.json().get('access_token')
    if not gh_token:
        return Response({'detail': 'GitHub 授权失败'}, status=status.HTTP_400_BAD_REQUEST)

    gh_headers = {'Authorization': f'token {gh_token}'}

    # 2) 获取 GitHub 用户信息
    try:
        user_resp = http_requests.get(
            'https://api.github.com/user', headers=gh_headers,
            proxies=settings.PROXIES, timeout=15,
        )
    except http_requests.exceptions.RequestException:
        return Response(
            {'detail': '无法获取 GitHub 用户信息，请检查网络'},
            status=status.HTTP_502_BAD_GATEWAY,
        )

    gh_user = user_resp.json()
    github_id = gh_user.get('id')
    if not github_id:
        return Response({'detail': 'GitHub 返回数据异常'}, status=status.HTTP_400_BAD_REQUEST)

    login = gh_user.get('login', '')
    name = gh_user.get('name') or login
    email = gh_user.get('email')

    # 3) 若邮箱为空（GitHub 默认私密），通过 /user/emails 获取主邮箱
    if not email:
        try:
            emails_resp = http_requests.get(
                'https://api.github.com/user/emails', headers=gh_headers,
                proxies=settings.PROXIES, timeout=15,
            )
            for entry in emails_resp.json():
                if entry.get('primary'):
                    email = entry.get('email')
                    break
        except http_requests.exceptions.RequestException:
            pass  # 邮箱获取失败不影响主流程

    # 4) 尝试通过 github_id 或 email 查找已关联用户
    user = None
    try:
        user = User.objects.get(github_id=github_id)
    except User.DoesNotExist:
        if email:
            try:
                user = User.objects.get(email=email)
                user.github_id = github_id
                user.save()
            except User.DoesNotExist:
                pass

    if user:
        # 已关联，直接签发 JWT
        refresh = RefreshToken.for_user(user)
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserSerializer(user).data,
        })

    # 未关联，返回 GitHub 信息，前端展示绑定表单
    return Response({
        'need_bind': True,
        'github_id': github_id,
        'github_name': name,
        'email': email or '',
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def github_bind(request):
    """将 GitHub 账号绑定到已有系统用户（用户名+密码验证）"""
    github_id = request.data.get('github_id')
    username = request.data.get('username')
    password = request.data.get('password')

    if not all([github_id, username, password]):
        return Response({'detail': '参数不完整'}, status=status.HTTP_400_BAD_REQUEST)

    user = authenticate(username=username, password=password)
    if not user:
        return Response({'detail': '用户名或密码错误'}, status=status.HTTP_401_UNAUTHORIZED)

    # 检查该 github_id 是否已被其他账号绑定
    if User.objects.filter(github_id=github_id).exclude(pk=user.pk).exists():
        return Response({'detail': '该 GitHub 账号已被其他用户绑定'}, status=status.HTTP_400_BAD_REQUEST)

    user.github_id = github_id
    user.save()

    refresh = RefreshToken.for_user(user)
    return Response({
        'access': str(refresh.access_token),
        'refresh': str(refresh),
        'user': UserSerializer(user).data,
    })
