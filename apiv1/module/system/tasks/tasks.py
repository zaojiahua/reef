import datetime
import pathlib
import subprocess

from asgiref.sync import async_to_sync
from celery import shared_task, Task
from celery.utils.log import get_task_logger

from apiv1.core.constants import REDIS_LOG_DELETE, LOG_DELETE_GROUP
from apiv1.core.utils import ReefLogger
from apiv1.module.tboard.tasks.tasks import channel_layer
from reef.celery import register_task_logger, celery_app
from reef.settings import MEDIA_ROOT, redis_pool_connect

logger = get_task_logger(__name__)


class DeleteLogBaseTask(Task):

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error(f"\n exc: {exc}\n task id: {task_id}\n args: {args}\n einfo:{einfo}")
        # 任务异常，删除redis记录
        try:
            async_to_sync(channel_layer.group_send)(LOG_DELETE_GROUP, {
                "type": "send_message",
                "message": {"status": "FAIL", "task_id": task_id, "args": args, "except": f"{exc}"}
            })
        except Exception as e:
            reef_logger = ReefLogger('file')
            reef_logger.error(
                f'on_failure func error, celery task except:\n'
                f'error info: {e}'
            )

        redis_pool_connect.delete(f"{REDIS_LOG_DELETE}:{task_id}")


@register_task_logger(__name__)
@shared_task(bind=True, base=DeleteLogBaseTask)
def delete_log(self, start_date, days):
    p = pathlib.Path(MEDIA_ROOT)
    rds_log_path = p / 'rds_logs'
    screen_shot_path = p / 'screen_shot'
    start_date = datetime.datetime.strptime(start_date, "%Y_%m_%d")

    # 模拟耗时
    # import time
    # time.sleep(35)

    # clean screen shot
    screen_shot_ret = clean_log(start_date, days, screen_shot_path)
    # clean rds log
    rds_log_ret = clean_log(start_date, days, rds_log_path)

    screen_shot_ret.extend(rds_log_ret)

    return screen_shot_ret


@register_task_logger(__name__)
@shared_task(bind=True)
def send_message(self, ret):
    # task success callback
    async_to_sync(channel_layer.group_send)(LOG_DELETE_GROUP, {
        "type": "send_message",
        "message": {"status": "SUCCESS", "success_ret": ret}
    })


def clean_log(start_date, days, log_path):
    ret = []
    if not log_path.exists():
        # log 目录不存在
        return ret
    empty_path = log_path / 'empty'
    if not empty_path.exists():
        empty_path.mkdir()
    # 只删除1天
    if days == 0:
        days += 1
    for i in range(days):
        start_date_str = datetime.datetime.strftime(start_date, '%Y_%m_%d')
        date_path = log_path / start_date_str
        if date_path.exists():
            cmd = 'find %s -maxdepth 1 -type d -name "%s"' \
                  ' | xargs -I {} rsync --delete-before -av %s {}' % (log_path, start_date_str, f"{empty_path}/")
            complete_process = subprocess.run(
                cmd,
                shell=True
            )
            ret.append({start_date_str: complete_process.returncode, "cmd": cmd})
        start_date = start_date + datetime.timedelta(days=1)
    return ret