import logging
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

from apiv1.module.resource.models import SIMCard

logger = logging.getLogger('backend')


# 解绑触发pre_save
@receiver(pre_save, sender='apiv1.SIMCard', dispatch_uid="sim_card_save")
def unbind_update_device_simcard_resource(sender, instance=None, **kwargs):
    if instance.device:
        unbind_device_simcard_resource(instance)
    if instance.subsidiary_device:
        pass


# 绑定触发 post_save
@receiver(post_save, sender='apiv1.SIMCard')
def bind_update_device_simcard_resource(sender, instance=None, **kwargs):
    if instance.device:
        bind_device_simcard_resource(instance)
    if instance.subsidiary_device:
        pass


def bind_device_simcard_resource(obj: SIMCard):
    try:
        device = obj.device
        matching_rule_data = obj.device.matching_rule
        if not matching_rule_data.get('device', None):
            matching_rule_data['device'] = {}
        matching_rule_data['device'][f'simcard_{obj.order}'] = {
            "operator": obj.operator,
            "volte": obj.is_volte
        }
        device.matching_rule = matching_rule_data
        device.save()
    except Exception as e:
        logger.error(
            f'bind simcard, update {device.device_label} matching_rule fail.'
            f'question: {e}'
        )


def bind_subsidiary_device_simcard_resource(obj: SIMCard):
    try:
        subsidiary_device = obj.subsidiary_device

    except Exception as e:
        pass


def unbind_device_simcard_resource(obj: SIMCard):
    device = obj.device
    matching_rule_data = obj.device.matching_rule
    try:
        if matching_rule_data.get('device', None):
            matching_rule_data['device'].pop(f'simcard_{obj.order}')
    except Exception as e:
        logger.error(f'device: {device.device_label},'
                     f'update matching_rule, unbind sim_card {obj.id} fail')