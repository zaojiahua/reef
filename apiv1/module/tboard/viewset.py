from apiv1.module.tboard.models import TBoard, TBoardStatisticsResult
from apiv1.module.tboard.serializer import TBoardSerializer, TBoardStatisticsResultSerializer
from apiv1.core.view.generic import GenericViewSet


class DynamicTBoardViewSet(GenericViewSet):
    """
    TBoard通用接口，无特殊处理逻辑
    """
    serializer_class = TBoardSerializer
    queryset = TBoard.objects.all()
    return_key = 'tboards'
    queryset_filter = {}
    instance_filter = {}


class TBoardStatisticsResultViewSet(GenericViewSet):
    """
    通用接口
    """
    serializer_class = TBoardStatisticsResultSerializer
    queryset = TBoardStatisticsResult.objects.all()
    return_key = 'tboardstatisticsresult'
    queryset_filter = {}
    instance_filter = {}
