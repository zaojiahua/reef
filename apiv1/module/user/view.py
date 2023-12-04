from django.contrib.auth.models import Group
from django.contrib.auth import authenticate
from rest_framework import generics, status, serializers
from rest_framework.authtoken.models import Token
from rest_framework.request import Request
from rest_framework.response import Response

from apiv1.module.user.models import ReefUser
from apiv1.module.system.view import logger
from apiv1.module.user.serializer import LoginSerializer, UserSerializer


class GetUserPermissionsView(generics.GenericAPIView):
    """
    取得当前用户的权限信息
    """

    def get(self, request: Request):
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        permissions = request.user.get_all_permissions()
        return Response(permissions, status=status.HTTP_200_OK)


class LoginView(generics.GenericAPIView):
    """
    返回token信息
    """
    serializer_class = LoginSerializer

    def post(self, request):
        # 参数校验
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # 若找不到使用者，则返回404
        if not ReefUser.objects.filter(username=serializer.validated_data['username']).exists():
            return Response(status=status.HTTP_404_NOT_FOUND)

        # 如果用户is_active=false,返回400
        if not ReefUser.objects.get(username=serializer.validated_data['username']).is_active:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        # 用户名密码校验,若验证失败(密码错误)，则返回401
        user = authenticate(username=serializer.validated_data["username"],
                            password=serializer.validated_data["password"])
        if user is None:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        # 不存在则创建
        token, created = Token.objects.get_or_create(user=user)

        return Response({
            "id": user.id,
            "username": user.username,
            "last_name": user.last_name,
            "token": token.key
        }, status=status.HTTP_200_OK)


class UserLoginView(generics.GenericAPIView):
    """
    Cypress的登入API
    """
    serializer_class = UserSerializer

    def post(self, request):
        user_serializer = UserSerializer(data=request.data)

        if not user_serializer.is_valid():
            logger.error(f'Error: {user_serializer.errors}')
            return Response(user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # 若找不到使用者，则返回404
        if not ReefUser.objects.filter(
                username=user_serializer.validated_data['username']
        ).exists():
            return Response(status=status.HTTP_404_NOT_FOUND)

        # 用户名密码校验
        user: ReefUser = authenticate(
            **user_serializer.validated_data
        )

        # 若验证失败(密码错误)，则返回401
        if user is None:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        class UserModelSerializer(serializers.ModelSerializer):
            groups = serializers.SlugRelatedField(
                queryset=Group.objects.all(),
                slug_field='name',
                many=True
            )

            token = serializers.SerializerMethodField()

            def get_token(self, obj):
                token, _ = Token.objects.get_or_create(user=obj)
                return token.key

            class Meta:
                model = ReefUser
                exclude = ('password',)
                read_only_fields = ('token',)

        return Response(UserModelSerializer(user).data, status=status.HTTP_200_OK)
