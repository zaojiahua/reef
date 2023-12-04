import os

from django.utils import timezone

from reef import celery_app
from reef.settings import JOB_EXPORT_ZIP_ROOT, redis_connect


@celery_app.task
def delete_expired_job_export_zip(*args, **kwargs):
    """
    job 导入导出的压缩包存在media的job_export目录下
    该定时任务会在每天7点30，定时删除一天之前的所有压缩包
    """
    all_zip = os.listdir(JOB_EXPORT_ZIP_ROOT)
    yesterday = (timezone.now()-timezone.timedelta(hours=23, minutes=59, seconds=59)).strftime('%Y%m%d%H%M%S%f')
    point_zip = f"job-export-{yesterday}-0.zip"
    for zip in all_zip:
        if os.path.isdir(zip):
            continue
        if zip < point_zip:
            os.remove(os.path.join(JOB_EXPORT_ZIP_ROOT, zip))
    return
