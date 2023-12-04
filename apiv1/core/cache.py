# Cache Decorator
import json
from typing import List

from django.db import models
from django.http import HttpResponse
from rest_framework.renderers import JSONRenderer
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apiv1.core.utils import serialize_response_into_str_dict
from reef.settings import redis_connect, REEF_USE_CACHE

json_render = JSONRenderer()


def cache_dcr(key_leading: str = "cache", ttl_in_second: int = 86400 * 7,
              ignore: List[str] = None):
    """
    緩存裝飾器，會以request.query_param的内容作爲緩存key
    裝飾器會忽略ignore内的query param, 將其視爲對輸出結果沒有影響的參數
    """
    if ignore is None:
        ignore = []

    def decorator(func):
        if not REEF_USE_CACHE:
            return func

        def wrapper(self: APIView, request: Request):
            # request.query_params QueryDict 类型数据在cython 编译后会报错，转为dict type
            cache_key = prepare_cache_key(key_leading, request.query_params, ignore)

            result: List = redis_connect.hmget(cache_key, ["data", "content_type", "status", "headers"])

            non_exists = len([0 for item in result if item is not None]) == 0

            if not non_exists:  # hit
                headers: List[List[str:str]] = json.loads(result.pop())
                response = HttpResponse(*result)
                for header in headers:
                    response[header[0]] = header[1]

                return response

            ret: Response = func(self, request)
            ret = self.finalize_response(request, response=ret)

            redis_connect.hmset(cache_key, serialize_response_into_str_dict(ret))
            redis_connect.expire(cache_key, ttl_in_second)

            return ret

        return wrapper

    return decorator


def prepare_cache_key(key_leading: str, param, ignore: List[str] = None):
    if ignore is None:
        ignore = []
    cache_keys = []
    for k, v in param.items():
        if k not in ignore:
            if isinstance(v, models.Model):
                item = f"{k}={v.pk}"
            elif type(v) is dict:
                if 'id' in v:
                    item = f"{k}={v['id']}"
                elif 'pk' in v:
                    item = f"{k}={v['pk']}"
                else:
                    raise TypeError('Wrong type of param value!')
            else:
                item = f"{k}={v}"
            cache_keys.append(item)

    cache_keys.sort(key=lambda tup: tup[0])
    cache_key = f'{key_leading}:{"&".join(cache_keys)}'

    return cache_key
