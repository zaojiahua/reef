import json

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from channels.layers import get_channel_layer

from apiv1.core.constants import TBOARD_DELETE_GROUP, TBOARD_DELETE_FAIL_GROUP, REDIS_TBOARD_DELETE, \
    REDIS_TBOARD_DELETE_FAIL
from apiv1.module.tboard.tasks.tasks import get_hash_data_in_redis, sorted_data, STATE_MAPPING


class TBoardDeleteConsumer(WebsocketConsumer):
    def connect(self):
        channel_layer = get_channel_layer()

        # Join group
        async_to_sync(self.channel_layer.group_add)(
            TBOARD_DELETE_GROUP,
            self.channel_name
        )
        self.accept()

        # 在每次连接进来之后都会从redis里取出所有tboard_delete的信息，发送一次消息
        tboard_deleting_message = get_hash_data_in_redis(f'{REDIS_TBOARD_DELETE}:*')
        message = sorted_data(
            tboard_deleting_message,
            lambda e: (e.__getitem__('record_time'), STATE_MAPPING[(e.__getitem__('state'))])
        )
        async_to_sync(channel_layer.group_send)(TBOARD_DELETE_GROUP, {
            "type": "send_message",
            "message": message
        })

    def disconnect(self, close_code):
        # Leave group
        async_to_sync(self.channel_layer.group_discard)(
            TBOARD_DELETE_GROUP,
            self.channel_name
        )

    def receive(self, text_data):
        pass

    def send_message(self, event):
        self.send(text_data=json.dumps({
            "message": event["message"]
        }))


class TBoardDeleteFailConsumer(WebsocketConsumer):
    def connect(self):
        channel_layer = get_channel_layer()

        # Join group
        async_to_sync(self.channel_layer.group_add)(
            TBOARD_DELETE_FAIL_GROUP,
            self.channel_name
        )
        self.accept()

        # 在每次连接进来之后都会从redis里取出所有tboard_deleted_fail的信息，发送一次消息
        tboard_deleted_fail_message = get_hash_data_in_redis(f'{REDIS_TBOARD_DELETE_FAIL}:*')
        message = sorted_data(
            tboard_deleted_fail_message,
            lambda e: (e.__getitem__('record_time'))
        )
        async_to_sync(channel_layer.group_send)(TBOARD_DELETE_FAIL_GROUP, {
            "type": "send_message",
            "message": message
        })

    def disconnect(self, close_code):
        # Leave group
        async_to_sync(self.channel_layer.group_discard)(
            TBOARD_DELETE_FAIL_GROUP,
            self.channel_name
        )

    def receive(self, text_data):
        pass

    def send_message(self, event):
        self.send(text_data=json.dumps({
            "message": event["message"]
        }))
