"""
取得PaneView
method: GET
url: api/v1/cedar/get_paneview/
content-type: application/json
param: id, limit, offset

id可传入多笔，格式如: 1,2,3,4

response:
content-type: application/json
status code: 200 OK
body:
{
    paneviews: [
        {
            id: int
            name: str
            type: str
            cabinet: int
            width: int
            height: int
            paneslots: [
                {
                    id: int
                    x: int
                    y: int
                    # paneslot当前状态(ok, empty, error)，正常情况下刚创建完的paneslot状态都会是empty
                    status: str

                    # 关联的设备id, 正常情况下刚创建完，该字段应该都是null
                    device: int
                }
            ]
        }
    ]
}



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
from django.core import paginator
from rest_framework import serializers, status
from rest_framework import generics
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.request import Request
from rest_framework.response import Response

from apiv1.module.device.models import PaneView, PaneSlot


class PaneSlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaneSlot
        fields = ('id', 'row', 'col', 'status', 'device')


class GetPaneviewSerializer(serializers.ModelSerializer):
    paneslots = PaneSlotSerializer(many=True)

    class Meta:
        model = PaneView
        fields = ('id', 'name', 'type', 'cabinet', 'width', 'height', 'paneslots')


class GetPaneViewView(generics.GenericAPIView):
    def get(self, request: Request) -> Response:
        paneviews = PaneView.objects.all()
        ids = request.query_params.get('id')
        if ids:
            paneviews = paneviews.filter(id__in=ids.split(','))

        pagination = LimitOffsetPagination()
        paneviews = pagination.paginate_queryset(paneviews, request)

        serializer = GetPaneviewSerializer(instance=paneviews, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)




