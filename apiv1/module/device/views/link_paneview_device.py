"""
添加Device到Paneview中
method: POST
url: api/v1/cedar/link_paneview_device/
content-type: application/json
body:
{
    paneslot: int optional
    device: int required

    # 若没有传入paneslot，则会根据paneview去自动筛选出空闲的paneslot配对
    paneview: int optional

    # ret_level: 回传数据的等级，数字越低，回传的数据越精简，反之越详细
    ret_level: int optional
}


response:
content-type: application/json
status code: 200 OK
body:

if ret_level = 0
{
    paneslot: int
    device: int
}

if ret_level = 1
{
    paneslot_id: int
    paneview: int
    row: int
    col: int
    status: str
    device: int
}

if ret_level = 2
{
    paneview_id: int
    name: str
    type: str
    cabinet: int
    width: int
    height: int
    paneslots: [
        {
            id: int
            paneview: int
            row: int
            col: int
            status: str
            device: int
        }
    ]
}


exception:
content-type: application/json
status code: 400, 404, 409
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
from django.db import transaction
from rest_framework import serializers, status
from rest_framework.exceptions import ValidationError, NotFound
from rest_framework.generics import GenericAPIView
from rest_framework.request import Request
from rest_framework.response import Response

from apiv1.core import constants
from apiv1.core.request import sync_info_to_coral
from apiv1.module.device.models import PaneSlot, Device, PaneView


# noinspection PyAbstractClass
from reef import settings


class LinkPaneViewDeviceSerializer(serializers.Serializer):
    paneslot = serializers.PrimaryKeyRelatedField(
        queryset=PaneSlot.objects.all(),
        required=False,
        allow_null=False,
        default=None
    )
    paneview = serializers.PrimaryKeyRelatedField(
        queryset=PaneView.objects.all(),
        required=False,
        allow_null=False,
        default=None
    )
    device = serializers.PrimaryKeyRelatedField(
        queryset=Device.objects.all(),
        required=True,
        allow_null=False
    )
    ret_level = serializers.IntegerField(
        min_value=0,
        max_value=2,
        required=False,
        default=0
    )

    @staticmethod
    def validate_paneslot(paneslot: PaneSlot):
        if paneslot:
            if paneslot.device is not None or paneslot.status != constants.PANESLOT_STATUS_EMPTY:
                raise ValidationError(detail=f"The paneslot: {paneslot.id} in used", code=409)
        return paneslot

    @staticmethod
    def validate_device(device: Device) -> Device:
        if PaneSlot.objects.filter(device=device).exists():
            raise ValidationError(detail=f"The device already linked to another paneslot", code=409)
        return device

    def validate(self, attrs):
        if 'paneslot' not in attrs or attrs['paneslot'] is None:
            if 'paneview' not in attrs or attrs['paneview'] is None:
                raise ValidationError(detail=f"paneview cannot be None if paneslot is not provided!", code=400)
        return attrs


# noinspection PyAbstractClass
class RetLevel0Serializer(serializers.Serializer):
    paneslot = serializers.PrimaryKeyRelatedField(read_only=True)
    device = serializers.PrimaryKeyRelatedField(read_only=True)


class RetLevel1Serializer(serializers.ModelSerializer):
    """
    {
        paneslot_id: int
        paneview: int
        row: int
        col: int
        status: str
        device: int
    }
    """
    paneslot_id = serializers.IntegerField(source='id', read_only=True)

    class Meta:
        model = PaneSlot
        fields = ('paneslot_id', 'paneview', 'row', 'col', 'status', 'device')


class RetLevel2Serializer(serializers.ModelSerializer):
    """
    {
        paneview_id: int
        name: str
        type: str
        cabinet: int
        width: int
        height: int
        paneslots: [
            {
                id: int
                paneview: int
                row: int
                col: int
                status: str
                device: int
            }
        ]
    }
    """

    class Meta:
        model = PaneView
        fields = ('paneview_id', 'name', 'type', 'cabinet', 'width', 'height', 'paneslots')

    class PaneSlotSerializer(serializers.ModelSerializer):
        class Meta:
            model = PaneSlot
            fields = ('id', 'paneview', 'row', 'col', 'status', 'device')

    paneslots = PaneSlotSerializer(many=True)
    paneview_id = serializers.IntegerField(source='id')


class LinkPaneViewDeviceView(GenericAPIView):

    serializer_class = LinkPaneViewDeviceSerializer

    def post(self, request: Request) -> Response:
        with transaction.atomic():
            serializer = LinkPaneViewDeviceSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            paneslot: PaneSlot = serializer.validated_data.get('paneslot')
            device: Device = serializer.validated_data.get('device')
            ret_level: int = serializer.validated_data.get('ret_level')
            paneview = serializer.validated_data.get('paneview')

            if paneslot is None:
                for ps in paneview.paneslots.all():
                    if ps.status == constants.PANESLOT_STATUS_EMPTY:
                        paneslot = ps
                        break
                else:
                    raise NotFound(detail=f"The paneview has no idle slot!")
        # link device and paneview type is test_box inform coral
        # if paneview.type == 'test_box':
        #     link_device_inform_coral(paneview, device)

            paneslot.device = device
            paneslot.status = constants.PANESLOT_STATUS_OK
            paneslot.save()

        ret_data = None
        if ret_level == 0:
            ret_data = {
                "paneslot": paneslot.id,
                "device": device.id
            }
        elif ret_level == 1:
            ret_data = RetLevel1Serializer(instance=paneslot).data
        elif ret_level == 2:
            ret_data = RetLevel2Serializer(instance=paneslot.paneview).data

        # 通知coral获取device info
        sync_info_to_coral({"resource_name": "device"}, {"execute_space": "绑定PaneView"})

        return Response(ret_data, status=status.HTTP_200_OK)


#######################################################################
# Debug function                                                     #
#######################################################################
def unlink_all_device():
    """
    CAUTION TO USE IT!!
    Unlink all device in all paneview
    """
    PaneSlot.objects.update(
        status=constants.PANESLOT_STATUS_EMPTY,
        device=None
    )


def link_device_inform_coral(paneview: PaneView, device: Device):
    cabinet = paneview.cabinet
    try:
        res = requests.post(
            f"http://{cabinet.ip_address}:{settings.CORAL_PORT}/pane/device_arm_camera/",
            json={'arm_id': paneview.robot_arm, 'camera_id': paneview.camera, 'device_label':device.device_label},
            timeout=30
        )
    except Exception as e:
        raise ValidationError({'error_info': f'Connection fail or proxy server error: {str(e)}'},
                              code=status.HTTP_500_INTERNAL_SERVER_ERROR)


