from rest_framework.exceptions import APIException

class Exception403(APIException):
    status_code = 403


class Exception404(APIException):
    status_code = 404
