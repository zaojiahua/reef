import requests
from django.db import transaction
from rest_framework import serializers, generics, status
from rest_framework.response import Response

from apiv1.core.constants import POWER_PORT_STATUS_BUSY
from apiv1.module.device.models import Device, MonitorPort, PowerPort, TempPort
from reef import settings


class SetDeviceConfigSerializer(serializers.Serializer):
    auto_test = serializers.BooleanField(required=False)
    device_name = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    device_label = serializers.SlugRelatedField(slug_field='device_label', queryset=Device.objects.all())
    powerport = serializers.PrimaryKeyRelatedField(queryset=PowerPort.objects.all(), required=False, allow_null=True)
    monitor_index = serializers.PrimaryKeyRelatedField(queryset=MonitorPort.objects.all(), required=False,
                                                       allow_null=True)
    tempport = serializers.ListField(
        required=False,
    )
    custom_number = serializers.CharField(allow_blank=True)


class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = ('id', 'device_name', 'device_label', 'powerport', 'tempport', 'monitor_index', 'auto_test')


class SetDeviceConfig(generics.GenericAPIView):
    serializer_class = SetDeviceConfigSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        device = serializer.validated_data['device_label']
        try:
            ip = device.cabinet.ip_address
            res = requests.post(
                f"http://{ip}:{settings.CORAL_PORT}/pane/device_update/",
                json=convert_to_coral_format(serializer.validated_data)
            )
        except Exception as e:
            return Response(f'Connection fail or proxy server error: {str(e)}',
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if res.status_code != 200:
            return Response(f"Result from Coral({res.status_code}) {res.content}", status=res.status_code)

        with transaction.atomic():
            device.auto_test = serializer.validated_data['auto_test']
            device.device_name = serializer.validated_data['device_name']
            device.custom_number = serializer.validated_data['custom_number']
            device.save()

            if 'monitor_index' in serializer.validated_data:
                monitor_port = serializer.validated_data['monitor_index']
                device.monitor_index.clear()

                if monitor_port is not None:
                    device.monitor_index.add(serializer.validated_data['monitor_index'])

            if 'powerport' in serializer.validated_data:
                powerport = serializer.validated_data['powerport']

                # 若有powerport字段，而值為null，則清空該設備的powerport關聯
                if powerport is None:
                    # 使用Model更新數據，确保触发Signal
                    try:
                        powerport = PowerPort.objects.get(device=device)
                        powerport.device = None
                        powerport.save()
                    except PowerPort.DoesNotExist:
                        pass
                else:
                    if powerport.status == POWER_PORT_STATUS_BUSY and powerport.device_id != device.id:
                        return Response(f"PowerPort: {powerport.id} is busy")
                    # 更改之前先清空powerport关联
                    try:
                        p = PowerPort.objects.get(device=device)
                        p.device = None
                        p.save()
                    except PowerPort.DoesNotExist:
                        pass
                    powerport.device_id = device.id
                    powerport.save()

            # device : tempport = 1 : n
            temp_ports = []
            for tp in serializer.validated_data['tempport']:
                temp_port = TempPort.objects.get_or_create(
                    defaults=tp,
                    port=tp['port']
                )[0]
                temp_ports.append(temp_port)
            for tp in device.tempport.all():
                tp.device = None
                tp.save()
            for tp in temp_ports:
                tp.device = device
                tp.save()

        return Response(DeviceSerializer(instance=device).data, status=status.HTTP_200_OK)


#############################################
# Helper function                           #
#############################################
def convert_to_coral_format(src_dic) -> dict:
    ret_dic = {
        'device_label': src_dic['device_label'].device_label
    }
    if 'auto_test' in src_dic:
        ret_dic['auto_test'] = src_dic['auto_test']
    if 'device_name' in src_dic:
        ret_dic['device_name'] = src_dic['device_name']
    if 'powerport' in src_dic:
        ret_dic['powerport'] = {
            'port': src_dic['powerport'].port if src_dic['powerport'] is not None else None
        }
    if 'monitor_index' in src_dic:
        ret_dic['monitor_index'] = src_dic['monitor_index'].port if src_dic['monitor_index'] is not None else None
    if 'tempport' in src_dic:
        ret_dic['tempport'] = src_dic['tempport']

    return ret_dic

