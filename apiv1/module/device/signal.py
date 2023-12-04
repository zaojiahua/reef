from django.apps import apps
from django.db import connection
from django.db import models
from django.db.models.signals import post_save, pre_save
from django.dispatch import Signal, receiver

from apiv1.core.constants import DEVICE_STATUS_BUSY, DEVICE_STATUS_IDLE
from apiv1.core.utils import ReefLogger


@receiver([pre_save, post_save], sender='apiv1.Device', dispatch_uid='device_save')
def device_handler(sender, instance=None, **kwargs):
    if instance:
        from apiv1.module.device.models import Device
        try:
            device = Device.objects.get(id=instance.id)
            status = device.status
        except Exception as e:
            status = None
        reef_logger = ReefLogger('debug')
        reef_logger.debug(
            f'\n'
            f'{"-" * 50} \n'
            f'Parameter: \n'
            f'********** device: {instance.id}\n'
            f'********** status: {status} \n'
            f'update_fields: {kwargs} \n'
        )


@receiver([pre_save, post_save], sender='apiv1.SubsidiaryDevice', dispatch_uid='subsidiary_device_save')
def subsidiary_device_handler(sender, instance=None, **kwargs):
    if instance:
        from apiv1.module.device.models import SubsidiaryDevice
        try:
            subsidiary_device = SubsidiaryDevice.objects.get(id=instance.id)
            status = subsidiary_device.status
        except Exception as e:
            status = None
        reef_logger = ReefLogger('debug')
        reef_logger.debug(
            f'\n'
            f'{"-" * 50} \n'
            f'Parameter: \n'
            f'********** subsidiary_device: {instance.id}\n'
            f'********** status: {status} \n'
            f'update_fields: {kwargs} \n'
        )


class UpdateDeviceStatus:
    """
    设备，僚机状态修改统一管理。
    """

    def __init__(self, **kwargs):
        self.filter_subsidiary_device_status = None
        self.kwargs = kwargs

    def filter_subsidiary_device(self, filter_status=None):
        """
        需要根据筛选指定状态僚机时使用，当前业务情况不到，不进行过多层逻辑拆分。
        """
        if filter_status:
            self.filter_subsidiary_device_status = filter_status

    def update_subsidiary_device(self, device, filter_status, to_status):
        """
        变更僚机状态 filter_status -> to_status
        """
        from apiv1.module.device.models import Device
        if isinstance(device, Device):
            for sub_device in device.subsidiarydevice.filter(status=filter_status):
                sub_device.status = to_status
                sub_device.save()

    def insert_tboard_update_device_status(self, device_cabinet_ips):
        """
        发起任务， 更新device，subsidiary device状态。
        """
        for k, devices in device_cabinet_ips.items():
            for device in devices:
                device.status = DEVICE_STATUS_BUSY
                device.save()
                # sub_dev idle --> busy
                self.update_subsidiary_device(device, DEVICE_STATUS_IDLE, DEVICE_STATUS_BUSY)

    def insert_tboard_fail_update_device_status(self, device_cabinet_ips):
        """
        发起任务失败， 更新device，subsidiary device状态。
        """
        for k, devices in device_cabinet_ips.items():
            for device in devices:
                device.status = DEVICE_STATUS_IDLE
                device.save()
                # sub_dev idle --> busy
                self.update_subsidiary_device(device, DEVICE_STATUS_BUSY, DEVICE_STATUS_IDLE)

    def remove_tboard_update_device_status(self, device_list):
        """
        手动停止任务， 更新device，subsidiary device状态。
        """
        for device in device_list:
            device.status = DEVICE_STATUS_IDLE
            device.save()
            self.update_subsidiary_device(device, DEVICE_STATUS_BUSY, DEVICE_STATUS_IDLE)


update_device_status = UpdateDeviceStatus()


"""
tempport status的计算
-----------------------------------------------------------------
    temp_port        关联            device  ---> busy
    temp_port       没有关联         device  ---> idle
-----------------------------------------------------------------
"""


@receiver(post_save, sender="apiv1.TempPort", dispatch_uid="temp_port_save")
def temp_port_handler(sender, instance=None, **kwargs):
    _temp_port_update_field(instance)
    return


def _temp_port_update_field(instance):
    instance.status = Status.IDLE if instance.device is None else Status.BUSY
    # TempPort.objects.filter(id=instance.id).update(status=instance.status)
    with connection.cursor() as sql:
        sql.execute(f"UPDATE apiv1_tempport SET status = '{instance.status}' WHERE id = {instance.id}")
    return


"""
powerport status的计算
-----------------------------------------------------------------
    power_port        关联            device  ---> busy
    power_port       没有关联         device  ---> idle
-----------------------------------------------------------------
"""


@receiver(post_save, sender="apiv1.PowerPort", dispatch_uid="power_port_save")
def power_port_handler(sender, instance=None, **kwargs):
    _power_port_update_field(instance)
    return


def _power_port_update_field(instance):
    instance.status = Status.IDLE if instance.device is None else Status.BUSY
    power_port_cls = apps.get_model("apiv1", "PowerPort")
    power_port_cls.objects.filter(id=instance.id).update(status=instance.status)
    return


class Status:
    IDLE = 'idle'
    BUSY = 'busy'


"""
自定义update、post_bulk_create信号，重写update、bulk_create方法
update、post_bulk_create更新数据都是直接作用数据库，update的时候调用save()方法，就可以添加自己的一些功能
bulk_create 批量创建一定数量时，每一笔都触发signal，会影响性能，所以先去除
"""

post_update = Signal(providing_args=['queryset'])
post_bulk_create = Signal()


@receiver(post_update)
def post_update_callback(sender, queryset=None, **kwargs):
    if queryset.exists() and queryset is not None:
        queryset[0].save()


@receiver(post_bulk_create)
def post_bulk_create_callback(sender, instance=None, **kwargs):
    if instance is not None:
        instance.save()


class QuerySet(models.query.QuerySet):
    def update(self, **kwargs):
        super(QuerySet, self).update(**kwargs)
        post_update.send(sender=self.model, queryset=self)

    # def bulk_create(self, objs, batch_size=None, **kwargs):
    #     super(QuerySet, self).bulk_create(objs, **kwargs)
    #     for i in objs:
    #         post_bulk_create.send(sender=i.__class__, instance=i)


class ModelManager(models.Manager):
    def get_queryset(self):
        if self.model._meta.object_name == 'TempPort':
            return QuerySet(self.model, using=self._db).filter(is_active=True)
        else:
            return QuerySet(self.model, using=self._db)


class PowerPortManager(models.Manager):

    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)


class PowerPortAllManager(models.Manager):

    def get_queryset(self):
        return super().get_queryset().all()


class TempPortAllManager(models.Manager):

    def get_queryset(self):
        return super().get_queryset().all()


