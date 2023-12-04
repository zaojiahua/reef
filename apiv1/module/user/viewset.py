from django.contrib.auth.models import Group
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.request import Request
from rest_framework.response import Response

from apiv1.core.view.generic import GenericViewSet
from apiv1.module.user.models import ReefUser
from apiv1.module.user.serializer import GroupSerializer, ReefUserSerializer, TokenSerializer


class DynamicGroupViewSet(GenericViewSet):
    serializer_class = GroupSerializer
    queryset = Group.objects.all()
    return_key = 'groups'
    queryset_filter = {}
    instance_filter = {}


class DynamicTokenViewSet(GenericViewSet):
    serializer_class = TokenSerializer
    queryset = Token.objects.all()
    return_key = 'token'
    queryset_filter = {}
    instance_filter = {}


class DynamicReefUserViewSet(GenericViewSet):
    serializer_class = ReefUserSerializer
    queryset = ReefUser.objects.all()
    return_key = 'reefusers'
    queryset_filter = {}
    instance_filter = {}

    def list(self, request):
        """
        Remove password in the response
        """
        response = super(DynamicReefUserViewSet, self).list(request)
        if response.status_code == 200:
            for reefuser in response.data['reefusers']:
                if 'password' in reefuser.keys():
                    reefuser.pop('password')
        return response

    def retrieve(self, request, pk):
        """
        Remove password in the response
        """
        response = super(DynamicReefUserViewSet, self).retrieve(request, pk)
        if response.status_code == 200:
            if 'password' in response.data.keys():
                response.data.pop('password')
            return Response(response.data)
        return response

    def create(self, request: Request, *args, **kwargs):
        """
        Create Reefuser and encrypt password
        """
        response = super(DynamicReefUserViewSet, self).create(request, *args, **kwargs)
        if response.status_code == status.HTTP_201_CREATED:
            created_user = ReefUser.objects.get(
                pk=response.data.get('id')
            )
            # 对密码进行加密
            created_user.set_password(created_user.password)
            created_user.save()
            response.data.pop('password', None)
        return response

    def update(self, request, *args, **kwargs):
        """
        update encrypt password
        """
        change_password = True if request.data.get('password', None) is not None else False
        response = super(DynamicReefUserViewSet, self).update(request, *args, **kwargs)
        if change_password and (response.status_code == status.HTTP_200_OK):
            updated_user = ReefUser.objects.get(
                pk=response.data.get('id')
            )
            updated_user.set_password(request.data.get('password'))
            updated_user.save()
            # response 中不返回密码
            response.data.pop('password', None)
        return response

    def partial_update(self, request, *args, **kwargs):
        """
        update encrypt password
        """
        change_password = True if request.data.get('password', None) is not None else False
        response = super(DynamicReefUserViewSet, self).partial_update(request, *args, **kwargs)
        if change_password and (response.status_code == status.HTTP_200_OK):
            updated_user = ReefUser.objects.get(
                pk=response.data.get('id')
            )
            updated_user.set_password(request.data.get('password'))
            updated_user.save()
            response.data.pop('password', None)
        return response

    def destroy(self, request, *args, **kwargs):
        # 不支持对user的删除，可设置为不可登入状态
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

        # user: ReefUser = self.get_object()
        # if user.id == 1:  # default admin
        #     return Response({'error': 'Default admin cannot be delete!'}, status=status.HTTP_406_NOT_ACCEPTABLE)
        # return super(DynamicReefUserViewSet, self).destroy(request, *args, **kwargs)
