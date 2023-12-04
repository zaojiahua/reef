"""
移除PaneView
method: DELETE
url: api/v1/cedar/remove_paneview/
content-type: application/json
param: None
body:
{
    id: int required
}

response:
content-type: application/json
status code: 200 OK
body:
{}

exception:
content-type: application/json
status code: 400, 403, 404
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
from collections import OrderedDict

from rest_framework import status
from rest_framework.fields import IntegerField
from rest_framework.generics import GenericAPIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import Serializer

from apiv1.core.exception import Exception403, Exception404
from apiv1.module.device.models import PaneSlot, PaneView


class RemovePaneViewSerializer(Serializer):
    id = IntegerField()

    def validate_id(self, val):
        if not PaneView.objects.filter(id=val).exists():
            raise Exception404(
                detail=f'Cannot find paneview {val}'
            )

        return val

    def validate(self, attrs: OrderedDict):
        paneslots = PaneSlot.objects.filter(paneview=attrs['id'])
        for ps in paneslots:  # type: PaneSlot
            if ps.device is not None:
                raise Exception403(
                    detail=f'PaneSlot {ps.id} in the PaneView related to device {ps.device.id}'
                )
        return attrs


class RemovePaneViewView(GenericAPIView):
    def delete(self, request: Request) -> Response:
        srz = RemovePaneViewSerializer(data=request.data)
        srz.is_valid(raise_exception=True)
        paneview = PaneView.objects.get(id=srz.validated_data['id'])
        paneview.delete()
        return Response({}, status=status.HTTP_200_OK)
