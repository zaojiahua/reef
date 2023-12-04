from apiv1.core import constants
from reef import celery_app


@celery_app.task
def sync_device_paneslot_status(*args, **kwargs):
    """将device的异常状态同步至paneslot中"""
    # TODO 这边的SQL应该可以再优化
    from apiv1.models import Device
    devices = Device.objects.filter(paneslot__isnull=False)
    for device in devices:
        paneslot = device.paneslot
        if device.status == constants.DEVICE_STATUS_ERROR:
            paneslot.status = constants.PANESLOT_STATUS_ERROR
        else:
            paneslot.status = constants.PANESLOT_STATUS_OK
        paneslot.save()
