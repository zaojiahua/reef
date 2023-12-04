from celery import shared_task

from apiv1.core.constants import DEVICE_STATUS_IDLE, DEVICE_STATUS_OCCUPIED
from apiv1.module.device.models import Device
from reef.celery import register_task_logger


@register_task_logger(__name__)
@shared_task(bind=True)
def set_device_status(self, device_id):
    """
    延时任务：
        被job editor占用{DELAYED_TASK_TIME}时间后，释放设备
    """
    try:
        device = Device.objects.get(id=device_id)
        if device.status in [DEVICE_STATUS_OCCUPIED]:
            device.occupy_type = ""
            device.status = DEVICE_STATUS_IDLE
        device.save()
    except:
        raise ("Get device instance fail!")
