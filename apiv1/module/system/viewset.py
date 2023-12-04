from apiv1.module.system.models import Cabinet, System, WoodenBox
from apiv1.module.system.serializer import CabinetSerializer, SystemSerializer, WoodenBoxSerializer
from apiv1.core.view.generic import GenericViewSet


class DynamicCabinetViewSet(GenericViewSet):
    """
    机柜
    """
    serializer_class = CabinetSerializer
    queryset = Cabinet.objects.all()
    return_key = 'cabinets'
    queryset_filter = {}
    instance_filter = {}


class DynamicSystemViewSet(GenericViewSet):
    """
    系统
    """
    serializer_class = SystemSerializer
    queryset = System.objects.all()
    return_key = 'systems'
    queryset_filter = {}
    instance_filter = {}


class DynamicWoodenBoxViewSet(GenericViewSet):
    """
    木盒
    """
    serializer_class = WoodenBoxSerializer
    queryset = WoodenBox.objects.all()
    return_key = 'woodenbox'
    queryset_filter = {}
    instance_filter = {}




