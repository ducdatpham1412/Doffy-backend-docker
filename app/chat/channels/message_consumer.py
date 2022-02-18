import json

from bson.objectid import ObjectId
from findme.mongo import mongoDb
from utilities import enums, services

from channels.generic.websocket import AsyncWebsocketConsumer


class MessageDetail(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_id = self.scope['url_route']['kwargs']['user_id']
        self.group_name = services.create_socket_message_detail(self.group_id)
        self.is_mode_exp = services.check_is_user_enjoy_mode(self.group_id)

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def handle_message(self, new_message):
        # save message to mongo
        insert_message = {
            'chatTag': new_message['chatTag'],
            'type': new_message['type'],
            'content': new_message['content'],
            'senderId': new_message['senderId'],
            'createdTime': services.get_datetime_now()
        }
        mongoDb.message.insert_one(insert_message)

        if insert_message['type'] == enums.message_image:
            for index, value in enumerate(new_message['content']):
                insert_message['content'][index] = services.create_link_image(
                    value)

        res = {
            'id': str(insert_message.pop('_id')),
            'chatTag': insert_message['chatTag'],
            'type': insert_message['type'],
            'content': insert_message['content'],
            'senderId': insert_message['senderId'],
            'senderAvatar': new_message['senderAvatar'],
            'tag': new_message['tag'],
            'createdTime': services.get_local_string_date_time(insert_message['createdTime']),
        }

        # update isLatest status of other member
        # and update time of chat tag
        list_all_user = new_message['listUser']
        list_partner_id = list_all_user.copy()
        list_partner_id.remove(res['senderId'])

        mongoDb.chatTag.find_one_and_update(
            {
                '_id': ObjectId(new_message['chatTag'])
            },
            {
                '$set': {
                    'userSeenMessage.{}.isLatest'.format(list_partner_id[0]): False,
                    'updateTime': services.get_datetime_now()
                }
            }
        )

        # filter user have the same id
        list_user_receive_message = services.filter_the_same_id(list_all_user)

        for user_id in list_user_receive_message:
            await self.channel_layer.group_send(
                services.create_socket_message_detail(user_id),
                {
                    'type': 'chat.message',
                    'data': res
                }
            )

    async def handle_message_enjoy(self, new_message):
        res = {
            'id': str(ObjectId()),
            'chatTag': new_message['chatTag'],
            'type': new_message['type'],
            'content': new_message['content'],
            'senderId': new_message['senderId'],
            'senderAvatar': new_message['senderAvatar'],
            'tag': new_message['tag'],
            'createdTime': str(services.get_datetime_now())
        }

        list_user_receive = services.filter_the_same_id(
            new_message['listUser'])

        for user_id in list_user_receive:
            await self.channel_layer.group_send(
                services.create_socket_message_detail(user_id),
                {
                    'type': 'chat.message',
                    'data': res
                }
            )

    async def receive(self, text_data=None):
        text_data_json = json.loads(text_data)
        if not self.is_mode_exp:
            await self.handle_message(text_data_json)
        else:
            await self.handle_message_enjoy(text_data_json)

    async def chat_message(self, event):
        data = event['data']
        await self.send(json.dumps(data))
