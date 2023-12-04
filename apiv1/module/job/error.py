from rest_framework import status
from rest_framework.exceptions import APIException, _get_error_details


class ValidationError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Invalid input.'
    default_code = 'invalid'

    def __init__(self, detail, code=None, extra=None):
        if detail is None:
            detail = self.default_detail
        if code is None:
            code = self.default_code

        data = {"error": detail}
        if extra is not None:
            if isinstance(extra, dict):
                data.update(extra)

        self.detail = _get_error_details(data, code)

    def __str__(self):
        return self.detail
