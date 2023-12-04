import subprocess
import time
import platform
import requests

from django.db import OperationalError

from rest_framework import generics, serializers
from django_redis import get_redis_connection
from celery import shared_task

from apiv1.module.user.models import ReefUser
from apiv1.core.response import ReefResponse


class ServerTestSerializer(serializers.Serializer):
    pass


class ServerTestView(generics.GenericAPIView):

    serializer_class = ServerTestSerializer

    def __init__(self):
        self.daphne_ip = '127.0.0.1'
        self.daphne_port = '8002'
        super(ServerTestView, self).__init__()

    def get_queryset(self):
        pass

    def get(self, request, ip):
        self.daphne_ip = ip
        results = []
        results.append(self.pg_db_test())
        results.append(self.redis_db_test())
        results.append(self.daphne_server_rq_test())
        results.append(self.celery_server_test())
        results.append({'server time': time.strftime('%a, %d %b %Y %H:%M:%S %z %Z', time.localtime())})
        return ReefResponse(data=results)

    def redis_db_test(self):
        try:
            redis_cli = get_redis_connection('default')
            redis_cli.set('redis_connect_key', 'redis_connect_val')
            redis_cli.expire('redis_connect_key', time=2)
        except Exception as e:
            print(e)
            return {'redis_db_connect_fail': f'{e}'}
        else:
            return {'redis_db_success': 'OK'}

    def pg_db_test(self):
        try:
            ReefUser.objects.filter(username='admin')
        except OperationalError as e:
            return {'pg_db_connect_fail': f'{e}'}
        except Exception as e:
            return {'pg_db_connect_fail': f'{e}'}
        else:
            return {'pg_db_success': 'OK'}

    def daphne_server_rq_test(self):
        headers = {
            'Connection': 'Upgrade',
            'Upgrade': 'websocket',
            'Sec-WebSocket-Key': 'NVwjmQUcWCenfWu98asDmg==',
            'Sec-WebSocket-Version': '13',
        }
        url = f'http://{self.daphne_ip}:{self.daphne_port}/ws/tboard/tboard_delete/'
        try:
            res = requests.get(url=url, headers=headers, timeout=2)
        except Exception as e:
            return {'daphne_server_fail': f'{e}'}
        else:
            return {'daphne_server_success': 'OK'}

    def daphne_server_curl_test(self):
        try:
            res = subprocess.run(
                f"""curl --include --no-buffer -H "Connection: Upgrade" -H "Upgrade: websocket" -H "Sec-WebSocket-Key: NVwjmQUcWCenfWu98asDmg==" \
                 --header "Sec-WebSocket-Version: 13" http://{self.daphne_ip}:{self.daphne_port}/ws/tboard/tboard_delete/""",
                timeout=1,
                check=True,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT
            )
        except subprocess.CalledProcessError as e:
            return {'daphne_server_fail': f'return code:{e.returncode}, error msg: {e.output.splitlines()[-1:-2:-1]}'}
        except subprocess.TimeoutExpired:
            return {'daphne_server_success': 'OK'}

    def celery_server_test(self):
        res = self._celery_func_test.delay(1)
        try:
            result = res.get(timeout=3)     # propagate=False 不希望 Celery 抛出异常
            if res.state == 'SUCCESS':
                return {'celery_server_success': 'OK'}
        except Exception as e:
            return {'celery_server_fail': f'{e}, time out is celery stop. task_id: {res.id}'}
        else:
            return {'celery_server_fail': f'{result}'}

    @shared_task()
    def _celery_func_test(self):
        return 'success'

