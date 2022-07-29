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
