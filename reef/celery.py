import os

from celery import Celery
from celery.utils.log import get_task_logger

__all__ = ["celery_app"]

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "reef.settings")

celery_app = Celery("reef")

celery_app.config_from_object('django.conf:settings', namespace='CELERY')


# Instantiate a logger at the decorated func level.
def register_task_logger(module_name):
    def wrapper(func):
        func.log = get_task_logger('%s.%s' % (module_name, func.__name__))
        return func

    return wrapper


celery_app.autodiscover_tasks(
    packages=[
        'apiv1.module.device.tasks',
        'apiv1.module.job.tasks',
        'apiv1.module.rds.tasks',
        'apiv1.module.system.tasks',
        'apiv1.module.tboard.tasks',
        'apiv1.module.user.tasks',
    ],
    related_name='periodtasks')

celery_app.autodiscover_tasks(
    packages=[
        'apiv1.module.device.tasks',
        'apiv1.module.job.tasks',
        'apiv1.module.rds.tasks',
        'apiv1.module.system.tasks',
        'apiv1.module.tboard.tasks',
        'apiv1.module.user.tasks',
    ],
    related_name='tasks')
