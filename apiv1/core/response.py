from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError, APIException


def reef_400_response(custom_code=0, message='', description='', data='', **kwargs):

    ret = {
        "message": message,
        "custom_code": custom_code,
        "description": description  # 前端页面info
    }
    if isinstance(data, dict):
        ret.update(data)
    else:
        ret.update({'data_info': data})
    if kwargs:
        ret.update({'data': kwargs})
    raise ValidationError(ret)


def reef_500_response(custom_code=0, message='', description='', data='', **kwargs):

    ret = {
        "message": message,
        "custom_code": custom_code,
        "description": description  # 前端页面info
    }
    if isinstance(data, dict):
        ret.update(data)
    else:
        ret.update({'data_info': data})
    if kwargs:
        ret.update({'data': kwargs})

    raise APIException(ret)


class ReefResponse(Response):

    def __init__(self, data=None, status_code=None, *args, **kwargs):

        if data is None:
            data = {'status': 'success'}
        if status_code is None:
            status_code = status.HTTP_200_OK

        super(ReefResponse, self).__init__(data, status=status_code, *args, **kwargs)



