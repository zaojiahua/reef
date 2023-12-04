"""
从PaneView中移除Device
method: POST
url: api/v1/cedar/unlink_paneview_device/
content-type: application/json
body:
{
    device: int required
}


response:
content-type: application/json
status code: 200 OK
body:
{}


exception:
content-type: application/json
status code: 400, 404
body:
{
    # 错误状况详情
    "有问题的字段名称": [
        "问题描述1",
        "问题描述2"
        ...
    ]
}

"""
import requests
from requests import Request
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import GenericAPIView
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.response import Response
from rest_framework.serializers import Serializer

from apiv1.core import constants
from apiv1.module.device.models import Device, PaneSlot, PaneView


# noinspection PyAbstractClass
from reef import settings


class UnlinkPaneViewDeviceSerializer(Serializer):
    device = PrimaryKeyRelatedField(
        queryset=Device.objects.all(),
        required=True,
        allow_null=False,
    )

    def validate(self, attrs):
        device = attrs.get('device')
        if not PaneSlot.objects.filter(device=device).exists():
            raise ValidationError(detail=f'Device: {device.id} not link to pane')
        return attrs


class UnlinkPaneViewDeviceView(GenericAPIView):

    serializer_class = UnlinkPaneViewDeviceSerializer

    def post(self, request: Request) -> Response:
        srz = UnlinkPaneViewDeviceSerializer(data=request.data)
        srz.is_valid(raise_exception=True)

        device: Device = srz.validated_data.get('device')
        paneslot = device.paneslot

        # if paneslot.paneview.type == 'test_box':
        #     unlink_device_inform_coral(paneslot.paneview, device)

        paneslot.device = None
        paneslot.status = constants.PANESLOT_STATUS_EMPTY
        paneslot.save()

        return Response({}, status=status.HTTP_200_OK)

#########################################
#  Helper Function                      #
#########################################


def unlink_device_inform_coral(paneview: PaneView, device: Device):
    cabinet = paneview.cabinet
    try:
        res = requests.delete(
            f"http://{cabinet.ip_address}:{settings.CORAL_PORT}/pane/device_arm_camera/",
            json={'device_label':device.device_label},
            timeout=30
        )
    except Exception as e:
        raise ValidationError({'error_info': f'Connection fail or proxy server error: {str(e)}'},
                              code=status.HTTP_500_INTERNAL_SERVER_ERROR)
