import os
from datetime import timedelta

from asgiref.sync import async_to_sync
from celery import shared_task
from celery._state import get_current_task
from celery.app.task import Task
from channels.layers import get_channel_layer
from rest_framework.response import Response

from apiv1.core.cache import prepare_cache_key
from apiv1.core.constants import TBOARD_DELETE_GROUP, TBOARD_DELETE_FAIL_GROUP, REDIS_TBOARD_DELETE, \
    REDIS_TBOARD_DELETE_FAIL, REDIS_CACHE_GET_DATA_VIEW
from apiv1.core.utils import daterange, serialize_response_into_str_dict
from apiv1.module.tboard.models import TBoard
from apiv1.module.tboard.views.get_data_view import get_data_view_result
from reef.celery import register_task_logger
from reef.settings import MEDIA_ROOT, redis_connect, redis_pool_connect

STATE_MAPPING = {'to_be_delete': 0, 'deleting': 1, 'deleted': 2}
channel_layer = get_channel_layer()


def get_hash_data_in_redis(re_key):
    res = []
    for i in redis_pool_connect.keys(re_key):
        data = redis_pool_connect.hgetall(i)
        res.append({key.decode(): val.decode() for key, val in data.items()})
    return res


def sorted_data(message, lambda_func):
    message = sorted(message, key=lambda_func, reverse=True) \
        if message else []
    return message


def _delete_tboard(tboard_id):
    tboard = TBoard.objects.get(id=tboard_id)
    for rds in tboard.rds.all():
        for rdslog in rds.rdslog.all():
            os.remove(rdslog.log_file.path)
            rdslog.delete()

        for rdsscreenshot in rds.rdsscreenshot.all():
            os.remove(rdsscreenshot.img_file.path)
            rdsscreenshot.delete()

        rds.delete()
    tboard.delete()
    return


class TBoardDeleteBaseTask(Task):
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        super(TBoardDeleteBaseTask, self).on_failure(exc, task_id, args, kwargs, einfo)
        # args: original arguments for the task
        tboard_id = args[0]

        # 删除redis tboard_delete_{id}这条数据,向删除中心发送消息，更新删除中心列表
        tboard_info = redis_connect.hgetall(f'{REDIS_TBOARD_DELETE}:{tboard_id}')
        redis_connect.delete(f'{REDIS_TBOARD_DELETE}:{tboard_id}')

        tboard_deleting_message = get_hash_data_in_redis(f'{REDIS_TBOARD_DELETE}:*')
        message = sorted_data(
            tboard_deleting_message,
            lambda e: (e.__getitem__('record_time'), STATE_MAPPING[(e.__getitem__('state'))])
        )
        async_to_sync(channel_layer.group_send)(TBOARD_DELETE_GROUP, {
            "type": "send_message",
            "message": message
        })

        # 将该tboard信息转储到redis的tboard_fail_{id}
        tboard_info.pop(b'state')
        redis_connect.hmset(f'{REDIS_TBOARD_DELETE_FAIL}:{tboard_id}', tboard_info)

        # 将错误信息记录到log
        task = get_current_task()
        self.log.error({f'{task.name}[{task_id}]': str(exc)})

        # 向删除列表发送一次消息，更新删除列表
        tboard_deleted_fail_message = get_hash_data_in_redis(f'{REDIS_TBOARD_DELETE_FAIL}:*')
        message = sorted_data(
            tboard_deleted_fail_message,
            lambda e: (e.__getitem__('record_time'))
        )
        async_to_sync(channel_layer.group_send)(TBOARD_DELETE_FAIL_GROUP, {
            "type": "send_message",
            "message": message
        })


@register_task_logger(__name__)
@shared_task(bind=True, max_retries=3, default_retry_delay=5, base=TBoardDeleteBaseTask)
def tboard_delete(self, id):
    try:
        # 更新tboard状态为正在删除
        redis_connect.hset(f'{REDIS_TBOARD_DELETE}:{id}', 'state', 'deleting')

        # 删除状态改变时，向删除中心发送消息，更新删除中心列表
        tboard_deleting_message = get_hash_data_in_redis(f'{REDIS_TBOARD_DELETE}:*')
        message = sorted_data(
            tboard_deleting_message,
            lambda e: (e.__getitem__('record_time'), STATE_MAPPING[(e.__getitem__('state'))])
        )
        async_to_sync(channel_layer.group_send)(TBOARD_DELETE_GROUP, {
            "type": "send_message",
            "message": message
        })

        # 删除tboard
        _delete_tboard(id)

        # 更新tboard状态为删除完成
        redis_connect.hset(f'{REDIS_TBOARD_DELETE}:{id}', 'state', 'deleted')

        # 删除完成，向删除中心发送消息，更新删除中心列表
        tboard_deleting_message = get_hash_data_in_redis(f'{REDIS_TBOARD_DELETE}:*')
        message = sorted_data(
            tboard_deleting_message,
            lambda e: (e.__getitem__('record_time'), STATE_MAPPING[(e.__getitem__('state'))])
        )
        async_to_sync(channel_layer.group_send)(TBOARD_DELETE_GROUP, {
            "type": "send_message",
            "message": message
        })

        # 每个tboard设置一天的过期时间
        redis_connect.expire(f'{REDIS_TBOARD_DELETE}:{id}', 86400)

    except Exception as exc:
        self.retry(exc=exc)

    return


@register_task_logger(__name__)
@shared_task(bind=True, max_retries=3, default_retry_delay=5)
def prepare_tboard_report_cache(self: Task, tboard_id):
    max_cache_page = 5

    tboard = TBoard.objects.get(pk=tboard_id)
    group_bys = ('device', 'job')

    for group_by in group_bys:
        for query_start_date in daterange(tboard.board_stamp, tboard.end_time):
            for query_end_date in daterange(query_start_date, tboard.end_time):
                """
                实际预热的筛选时间为 开始日期的00:00:00 到结束日期的23:59:59
                也就是说，如果有一个Rds在23:59:59.95开始，则这个Rds不会被列入统计
                
                这边缓存让预热的筛选精度维持在秒，是因为目前全局的时间精度只到秒。
                """
                query_end_date = query_end_date + timedelta(seconds=86399)
                page = 0
                ret = {
                    "count": float('inf')
                }
                while ret["count"] > page and page < max_cache_page:
                    param = {
                        "tboard": tboard,
                        "group_by": group_by,
                        "start_date": query_start_date,
                        "end_date": query_end_date,
                        "page": page
                    }

                    ret = get_data_view_result(**param)
                    res = Response(ret)

                    cache_key = prepare_cache_key(key_leading=REDIS_CACHE_GET_DATA_VIEW, param=param)

                    redis_connect.hmset(cache_key, serialize_response_into_str_dict(res))
                    redis_connect.expire(cache_key, 86400 * 14)

                    page += 1
