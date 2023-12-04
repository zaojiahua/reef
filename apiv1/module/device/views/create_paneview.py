import re
from typing import Tuple, List

from django.db import transaction
from rest_framework import generics, status
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.validators import UniqueValidator

from apiv1.core import constants
from apiv1.module.device.models import PaneView, PaneSlot
from apiv1.module.system.models import Cabinet

"""
添加PaneView
method: POST
url: api/v1/cedar/create_paneview/
content-type: application/json
param: None
body:
{
    # PaneView的名称 
    # 在matrix的模式下，名称只能使用大小写英文字母，数字和下划线。名称后方需加上@行x列，如：Pane001@5x4
    name: str
    # PaneView类型(matrix or map)
    type: str
    # 机柜编号，理论上用户交互应该要能提供，但目前的设计里没有，这里先固定传值10000就好
    cabinet: int
    # PaneView的宽高，matrix模式下代表像素，map模式下代表col和row的数量
    width: int (optional in type=matrix, required in type=map)
    height: int (optional in type=matrix, required in type=map)
    # 指定回传的内容详尽等级
    # 0: 只回传id
    # 1: 回传level 0的内容以及name, type, cabinet, width, height
    # 2: 回传level 1的内容以及其paneslot
    ret_level: int: (optional default=0)
}

response:
content-type: application/json
status code: 201 Created
body:
{
    id: int
    name: str
    type: str
    cabient: int
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

PANEVIEW_NAME_PATTERN = re.compile("^[a-zA-Z0-9_]+@[0-9]+[xX][0-9]+$")
MAX_COL = 9
MAX_ROW = 9


########################################################################
# Validator                                                            #
########################################################################
def name_validator(name: str):
    # Valid format: Pane001@7x9
    match = re.match(PANEVIEW_NAME_PATTERN, name)
    if match is None:
        raise ValidationError("名称格式不正确，正确的格式如: Pane_001@3x4，@前的名称只能使用英文大小写数字和下划线")
    col, row = _get_size(name)
    if col > MAX_COL or row > MAX_ROW:
        raise ValidationError("PaneView size cannot greater than 7x9")


def type_validator(attrs):
    tp = attrs['type']
    if tp == constants.PANEVIEW_TYPE_MAP:
        if 'width' not in attrs or 'height' not in attrs:
            raise ValidationError("In map type, width and height is required!")
    return attrs


########################################################################
# Request Serializer                                                   #
########################################################################
class CreatePaneViewSerializer(serializers.Serializer):
    name = serializers.CharField(validators=[
        name_validator,
        UniqueValidator(queryset=PaneView.objects.all())
    ])
    type = serializers.ChoiceField(choices=(
        constants.PANEVIEW_TYPE_MAP,
        constants.PANEVIEW_TYPE_MATRIX)
    )
    cabinet = serializers.PrimaryKeyRelatedField(queryset=Cabinet.objects.all())
    width = serializers.IntegerField(required=False)
    height = serializers.IntegerField(required=False)
    ret_level = serializers.ChoiceField(choices=(0, 1, 2), required=False, default=0)

    def validate(self, attrs):
        return type_validator(attrs)


########################################################################
# Response Serializer                                                  #
########################################################################
class Level0ResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaneView
        fields = ['id']


class Level1ResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaneView
        fields = ['id', 'name', 'type', 'cabinet', 'width', 'height']


class Level2ResponseSerializer(serializers.ModelSerializer):
    cabinet = serializers.PrimaryKeyRelatedField(queryset=Cabinet.objects.all())

    class Meta:
        model = PaneView
        depth = 1
        fields = ['id', 'name', 'type', 'cabinet', 'width', 'height', 'paneslots']


########################################################################
# View                                                                 #
########################################################################
class CreatePaneViewView(generics.GenericAPIView):
    serializer_class = CreatePaneViewSerializer

    def post(self, request: Request) -> Response:
        req_serializer: CreatePaneViewSerializer = self.get_serializer(data=request.data)
        req_serializer.is_valid(raise_exception=True)
        data = req_serializer.validated_data

        rows, cols = _get_size(data['name'])
        cols = cols if 'width' not in data else data['width']
        rows = rows if 'height' not in data else data['height']
        ret_level = int(data['ret_level'])

        with transaction.atomic():
            paneview = PaneView.objects.create(
                name=data['name'],
                type=data['type'],
                cabinet=data['cabinet'],
                width=cols,
                height=rows
            )

            slots = [PaneSlot(
                paneview=paneview,
                row=row,
                col=col
            ) for row in range(rows) for col in range(cols)]
            PaneSlot.objects.bulk_create(slots, batch_size=100)
        response_serializer = _get_response_serializer(ret_level, paneview)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


########################################################################
# Helper function                                                      #
########################################################################
def _get_size(name: str) -> Tuple[int, int]:
    name_root, size = name.split('@')
    rows, cols = size.lower().split('x')
    return int(rows), int(cols)


def _get_response_serializer(ret_level: int, paneview: PaneView):
    if ret_level == 0:
        return Level0ResponseSerializer(instance=paneview)
    elif ret_level == 1:
        return Level1ResponseSerializer(instance=paneview)
    elif ret_level == 2:
        return Level2ResponseSerializer(instance=paneview)
