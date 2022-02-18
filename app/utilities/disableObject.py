from datetime import datetime
from findme.mongo import mongoDb
from . import enums
from utilities.exception.exception_handler import CustomError, error_message, error_key


class TypeRequestDeleteAccount:
    userId: int
    createdTime: datetime
    deleteTime: datetime


class DisableObject:
    # user = __all[0][enums.disable_user]
    # follow = __all[1][enums.disable_follow]
    # profilePost = __all[2][enums.disable_profile_post]
    # message = __all[3][enums.disable_message]
    # requestDeleteAccount = __all[4][enums.disable_request_delete_account]

    @staticmethod
    def get_disable_object(type: str):
        result = mongoDb.disableObject.find_one({
            'type': type,
        })
        return result

    @staticmethod
    def add_disable_object(type: str, value: int or str):
        try:
            check = DisableObject.get_disable_object(type)
            check[type].index(value)
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
                    type: value
                }
            }
        )

        # check[type].append(value)
        # if type == enums.disable_user:
        #     DisableObject.user = check[type]
        # elif type == enums.disable_follow:
        #     DisableObject.follow = check[type]
        # elif type == enums.disable_profile_post:
        #     DisableObject.profilePost = check[type]
        # elif type == enums.disable_message:
        #     DisableObject.message = check[type]

    @staticmethod
    def add_request_delete_account(value: TypeRequestDeleteAccount):
        check = DisableObject.get_disable_object(
            enums.disable_request_delete_account)
        for request in check[enums.disable_request_delete_account]:
            if (request['userId'] == value['userId'] and request['isActive'] == True):
                raise CustomError(
                    error_message.you_have_lock_your_account, error_key.you_have_lock_your_account)

        mongoDb.disableObject.find_one_and_update(
            {
                'type': enums.disable_request_delete_account
            },
            {
                '$push': {
                    enums.disable_request_delete_account: value
                }
            }
        )

    @staticmethod
    def disable_request_delete_account(user_id):
        list_request = DisableObject.get_disable_object(
            enums.disable_request_delete_account)[enums.disable_request_delete_account]

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
                    enums.disable_request_delete_account: list_request
                }
            }
        )

    @staticmethod
    def remove_disable_object(type: str, value: any):
        mongoDb.disableObject.find_one_and_update(
            {
                'type': type
            },
            {
                '$pull': {
                    type: value
                }
            }
        )
        # result = list(filter(lambda val: val != value, check[type]))
        # if type == enums.disable_user:
        #     DisableObject.user = result
        # elif type == enums.disable_follow:
        #     DisableObject.follow = result
        # elif type == enums.disable_profile_post:
        #     DisableObject.profilePost = result
        # elif type == enums.disable_message:
        #     DisableObject.message = result
