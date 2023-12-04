from apiv1.core.constants import DEVICE_STATUS_IDLE, DEVICE_STATUS_BUSY
from apiv1.core.view.generic import GenericViewSet
from apiv1.module.resource.models import SIMCard, Account, APPGather
from apiv1.module.resource.serializer import SIMCardSerializer, AccountSerializer, APPGatherSerializer, \
    FilterDeviceSIMCardSerializer
from apiv1.core.response import reef_400_response

from rest_framework import status
from rest_framework.response import Response


class SIMCardViewSet(GenericViewSet):

    serializer_class = SIMCardSerializer
    queryset = SIMCard.objects.all()
    return_key = 'SIMCard'
    queryset_filter = {}
    instance_filter = {}

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.device or instance.subsidiary_device:
            return reef_400_response(message='source exist bind relation. Please unbind')
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def update(self, request, *args, **kwargs):
        status = request.data.get('status', None)
        # 绑定simcard 校验device status
        if status and status == DEVICE_STATUS_BUSY:
            self.serializer_class = FilterDeviceSIMCardSerializer
        return super(SIMCardViewSet, self).update(request, *args, **kwargs)


class AccountViewSet(GenericViewSet):

    serializer_class = AccountSerializer
    queryset = Account.objects.all()
    return_key = 'Account'
    queryset_filter = {}
    instance_filter = {}

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.device.all() or instance.subsidiary_device.all():
            return reef_400_response(message='source exist bind relation. Please unbind')
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class APPGatherViewSet(GenericViewSet):

    serializer_class = APPGatherSerializer
    queryset = APPGather.objects.all()
    return_key = 'APPGather'
    queryset_filter = {}
    instance_filter = {}

    def perform_destroy(self, instance):
        if instance.account.all().exists():
            raise reef_400_response(description='APP存在关联账号，请先删除关联账号后在进行删除操作')
        else:
            instance.delete()

    def perform_update(self, serializer):
        super(APPGatherViewSet, self).perform_update(serializer)
        instance = self.get_object()
        Account.objects.filter(app=instance).update(**{'app_name': instance.name})

