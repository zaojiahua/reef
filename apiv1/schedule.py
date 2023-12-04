from celery.schedules import crontab

from reef.celery import celery_app

celery_app.conf.beat_schedule = {
    'delete_expired_job_export_zip': {
        'task': 'apiv1.module.job.tasks.periodtasks.delete_expired_job_export_zip',
        'schedule': crontab(hour=7, minute=30)
    },

}


# 'sync_device_paneslot_status': {
#         'task': 'apiv1.module.device.tasks.periodtasks.sync_device_paneslot_status',
#         'schedule': 30
#     }


