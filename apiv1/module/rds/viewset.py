import os

from django.db import transaction
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle

from apiv1.module.rds.models import Rds, RdsLog, RdsScreenShot
from apiv1.module.rds.serializer import RdsSerializer, RdsLogSerializer, RdsScreenShotSerializer
from apiv1.core.view.generic import GenericViewSet


class DynamicRdsViewSet(GenericViewSet):

    throttle_classes = (AnonRateThrottle,)
    serializer_class = RdsSerializer
    queryset = Rds.objects.all()
    return_key = 'rdss'
    queryset_filter = {}

    # swagger parameter
    rds_id_list = openapi.Parameter('rds_id_list', openapi.IN_QUERY, description="rds_id_list",
                                    type=openapi.TYPE_STRING)

    @transaction.atomic
    @swagger_auto_schema(manual_parameters=[rds_id_list])
    @action(methods=['DELETE'], detail=False, url_name='bulk_delete_rds')
    def bulk_delete_rds(self, request):
        rds_id_list = request.query_params.get('rds_id_list', None)
        if rds_id_list is None:
            return Response({'error': 'missing argument: rds_id_list'}, status=status.HTTP_400_BAD_REQUEST)
        elif rds_id_list == 'end_time':     # rds_id_list is end_time, delete end_time=None data
            Rds.objects.filter(end_time=None).delete()
        else:
            try:
                rds_id_list = rds_id_list.split(',')        # 处理参数为列表
                Rds.objects.filter(id__in=rds_id_list).delete()
            except Exception as e:
                return Response({'error': f'delete fail: {e}'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status.HTTP_204_NO_CONTENT)


class DynamicRdsLogViewSet(GenericViewSet):
    serializer_class = RdsLogSerializer
    queryset = RdsLog.objects.all()
    return_key = 'rdslogs'
    queryset_filter = {}
    instance_filter = {}


class DynamicRdsScreenShotViewSet(GenericViewSet):
    serializer_class = RdsScreenShotSerializer
    queryset = RdsScreenShot.objects.all()
    return_key = 'rdsscreenshots'
    queryset_filter = {}
    instance_filter = {}

    @transaction.atomic
    def bulk_delete(self, request: Request):
        if 'id' not in request.query_params:        # 必须添加id参数
            return Response('Url params "id" is required!\n'
                            'use "id=1,2,3,4"', status=status.HTTP_400_BAD_REQUEST)
        ids = request.query_params['id'].split(',')     # 分割参数
        rds_screen_shot_queryset = RdsScreenShot.objects.filter(id__in=ids)
        for rds_screen_shot in rds_screen_shot_queryset:
            os.remove(rds_screen_shot.img_file.path)
            os.remove(rds_screen_shot.thumbs_file.path)
            rds_screen_shot.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)

    @classmethod
    def as_view(cls, actions=None, **initkwargs):
        view = super(DynamicRdsScreenShotViewSet, cls).as_view(actions, **initkwargs)
        if not initkwargs['detail']:  # Define the view is viewset's detail view or list view
            view.actions['delete'] = 'bulk_delete'
        return view
