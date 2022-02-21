from datetime import datetime
from findme.mongo import mongoDb
from . import enums
from utilities.exception.exception_handler import CustomError, error_message, error_key


class TypeRequestDeleteAccount:
    userId: int
    createdTime: datetime
    deleteTime: datetime


class DisableObject:
    @staticmethod
    def get_disable_object(type: str):
        result = mongoDb.disableObject.find_one({
            'type': type,
        })
        return result

    @staticmethod
    def add_disable_user(type: str, value: any):
        try:
            check = DisableObject.get_disable_object(type)
            check['list'].index(value)
            raise CustomError(error_message.you_have_lock_your_account,
                              error_key.you_have_lock_your_account)
        except ValueError:
            pass

        mongoDb.disableObject.find_one_and_update(
            {
                'type': type
            },
            {
                '$push': {
                    'list': value
                }
            }
        )

    @staticmethod
    def add_disable_post_or_message(type: str, value: object):
        mongoDb.disableObject.find_one_and_update(
            {
                'type': type
            },
            {
                '$push': {
                    'list': value
                }
            }
        )

    @staticmethod
    def add_request_delete_account(value: TypeRequestDeleteAccount):
        check = DisableObject.get_disable_object(
            enums.disable_request_delete_account)
        for request in check['list']:
            if (request['userId'] == value['userId'] and request['isActive'] == True):
                raise CustomError(
                    error_message.you_have_lock_your_account, error_key.you_have_lock_your_account)

        mongoDb.disableObject.find_one_and_update(
            {
                'type': enums.disable_request_delete_account
            },
            {
                '$push': {
                    'list': value
                }
            }
        )

    @staticmethod
    def disable_request_delete_account(user_id):
        list_request = DisableObject.get_disable_object(
            enums.disable_request_delete_account)['list']

        for index, value in enumerate(list_request):
            if (value['userId'] == user_id and value['isActive'] == True):
                list_request[index] = {
                    **value,
                    'isActive': False
                }
                break

        mongoDb.disableObject.find_one_and_update(
            {
                'type': enums.disable_request_delete_account
            },
            {
                '$set': {
                    'list': list_request
                }
            }
        )

    @staticmethod
    def remove_disable_user(type: str, value: any):
        mongoDb.disableObject.find_one_and_update(
            {
                'type': type
            },
            {
                '$pull': {
                    'list': value
                }
            }
        )
