from bson.objectid import ObjectId
from findme.mongo import mongoDb
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from utilities import enums, services
from utilities.exception import error_key, error_message
from utilities.exception.exception_handler import CustomError
from utilities.disableObject import DisableObject


class DeleteMessage(GenericAPIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        chat_tag_id = request.data['chatTagId']
        message_id = request.data['messageId']
        my_id = services.get_user_id_from_request(request)

        info_chat_tag = mongoDb.chatTag.find_one_and_update(
            {
                '_id': ObjectId(chat_tag_id)
            },
            {
                '$pull': {
                    'listMessages': {
                        '_id': ObjectId(message_id),
                        'senderId': my_id,
                    }
                },
                '$inc': {
                    'totalMessages': -1
                }
            }
        )

        # Check can delete or not and Add to Disable object
        if not info_chat_tag:
            raise CustomError()
        check_index = -1
        for index, value in enumerate(info_chat_tag['listMessages']):
            if value['_id'] == ObjectId(message_id) and value['senderId'] == my_id:
                check_index = index
                DisableObject.add_disable_post_or_message(
                    enums.disable_message, value)
                break
        if (check_index == -1):
            raise CustomError(error_message.not_have_permission_delete_message,
                              error_key.not_have_permission_delete_message)

        # Response
        return Response(None, status=status.HTTP_200_OK)
