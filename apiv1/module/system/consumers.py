import json

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from channels.layers import get_channel_layer

from apiv1.core.constants import LOG_DELETE_GROUP, REDIS_LOG_DELETE
from apiv1.core.utils import ReefLogger
from apiv1.core.view.server_test import ServerTestView
from apiv1.module.tboard.tasks.tasks import get_hash_data_in_redis, sorted_data, STATE_MAPPING
from reef import celery_app
from reef.settings import redis_pool_connect


class LogDeleteConsumer(WebsocketConsumer):
    def connect(self):
        channel_layer = get_channel_layer()

        # Join group
        async_to_sync(self.channel_layer.group_add)(
            LOG_DELETE_GROUP,
            self.channel_name
        )
        self.accept()

        # judge celery service status
        result = ServerTestView().celery_server_test()
        if result.get('celery_server_success', None) is None:
            async_to_sync(channel_layer.group_send)(LOG_DELETE_GROUP, {
                "type": "send_message",
                "message": {"status": "EXCEPTION", "description": f"celery service exception: {result}"}
            })
            return

        # 建立连接后，查询有没有正在删除的任务
        try:
            tboard_deleting_message = get_hash_data_in_redis(f'{REDIS_LOG_DELETE}:*')
            send_message = {"status": "SUCCESS"}
            if tboard_deleting_message:
                # 获取最近的一条 异步删除log数据
                message = sorted_data(
                    tboard_deleting_message,
                    lambda e: e.__getitem__('task_time')
                )
                first_res = message[0]
                task_id = first_res.get('task_id')
                res = celery_app.AsyncResult(task_id)
                send_message = {"status": res.state, "task_id": task_id}
            async_to_sync(channel_layer.group_send)(LOG_DELETE_GROUP, {
                "type": "send_message",
                "message": send_message
            })
        except Exception as e:
            # print(f"websocekt connect fail:{e}")
            reef_logger = ReefLogger('file')
            reef_logger.error(
                f'connect func error:\n'
                f'error info: {e}'
            )

    def disconnect(self, close_code):
        # Leave group
        async_to_sync(self.channel_layer.group_discard)(
            LOG_DELETE_GROUP,
            self.channel_name
        )

    def receive(self, text_data):
        pass

    def send_message(self, event):
        self.send(text_data=json.dumps({
            "message": event["message"]
        }))