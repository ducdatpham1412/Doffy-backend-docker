from django.db.utils import Error
from rest_framework import status
from rest_framework.exceptions import APIException, ErrorDetail
from rest_framework.response import Response
from rest_framework.views import exception_handler
from utilities.exception import error_key, error_message


err_token = {
    'blacklisted': 'Token is blacklisted',
    'invalid': 'Token is invalid or expired',
    'not_valid': 'Given token not valid for any token type'
}


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    def get_error_message():
        try:
            message = exc.detail['detail']
            return message
        except TypeError:
            return ''
        except KeyError:
            return ''

    if response is not None:
        message = get_error_message()

        # token expired
        if (message == err_token['not_valid']):
            err = {
                'success': False,
                'errorMessage': ErrorDetail(string=error_message.token_expired),
                'errorKey': error_key.token_expired,
                'status': response.status_code,
            }
        # token blacklisted
        elif (message == err_token['blacklisted']):
            err = {
                'success': False,
                'errorMessage': ErrorDetail(string=error_message.token_blacklisted),
                'errorKey': error_key.token_blacklisted,
                'status': response.status_code,
            }
        elif (message == err_token['invalid']):
            err = {
                'success': False,
                'errorMessage': ErrorDetail(string=error_message.token_blacklisted),
                'errorKey': error_key.token_blacklisted,
                'status': response.status_code,
            }

        else:
            err = {
                'success': False,
                'errorMessage': exc.detail,
                'errorKey': exc.get_codes(),
                'status': response.status_code,
            }

        return Response(err, status=response.status_code)

    return response


class CustomError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = error_message.init_err
    default_code = error_key.init_err

    def __init__(self, detail=None, code=None):
        super().__init__(detail=detail, code=code)
