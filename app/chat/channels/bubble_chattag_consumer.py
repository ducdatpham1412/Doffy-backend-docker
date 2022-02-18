from bson.objectid import ObjectId
from channels.generic.websocket import AsyncWebsocketConsumer
import json
from utilities import services
from utilities import enums
from findme.mongo import mongoDb
import pymongo


class BubbleAndChatTag(AsyncWebsocketConsumer):
    def update_list_user_id_connecting(self, isConnect: bool):
        if isConnect:
            temp = mongoDb.userActive.find_one({'userId': self.group_id})
            if not temp:
                mongoDb.userActive.insert_one({'userId': self.group_id})
        else:
            mongoDb.userActive.delete_one({'userId': self.group_id})

    """
    CONNECT
    """
    async def connect(self):
        self.group_id = self.scope['url_route']['kwargs']['user_id']
        self.group_name = services.create_socket_bubble_chattag(self.group_id)
        self.is_mode_exp = services.check_is_user_enjoy_mode(self.group_id)

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        self.update_list_user_id_connecting(True)

        await self.accept()

    """
    DISCONNECT
    """
    async def disconnect(self, code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
        self.update_list_user_id_connecting(False)

    # ----------------------------
    """
    HANDLE EVENT
    """

    async def handle_seen_message(self, data):
        user_id = data['user']
        chattag_id = data['chatTag']

        try:
            latest_message = mongoDb.message.find({'chatTag': chattag_id, 'senderId': {'$ne': user_id}}).sort([
                ('createdTime', pymongo.DESCENDING)]).limit(1)[0]
        # index error is when user send message for themself
        # in that case seen message of themself
        except IndexError:
            latest_message = mongoDb.message.find({'chatTag': chattag_id, 'senderId': user_id}).sort([
                ('createdTime', pymongo.DESCENDING)]).limit(1)[0]

        update_chattag = mongoDb.chatTag.find_one_and_update(
            {
                '_id': ObjectId(chattag_id)
            },
            {
                '$set': {
                    'userSeenMessage.{}'.format(user_id): {
                        'latestMessage': str(latest_message['_id']),
                        'isLatest': True,
                    }
                }
            }
        )

        res = {
            'chatTagId': chattag_id,
            'data': {
                '{}'.format(user_id): {
                    'latestMessage': str(latest_message['_id']),
                    'isLatest': True
                }
            }
        }

        # filter the same ids
        # in case seen message of them self, to avoid seen message 2 times
        list_user_receive_seen = services.filter_the_same_id(
            update_chattag['listUser'])

        for user_id in list_user_receive_seen:
            await self.channel_layer.group_send(services.create_socket_bubble_chattag(user_id), {
                'type': 'chat.seen_message',
                'data': res
            })

    async def handle_seen_message_enjoy(self, data):
        user_seen = data['userSeen']
        list_user = data['listUser']
        chat_tag_id = data['chatTagId']

        list_user_receive_seen = services.filter_the_same_id(list_user)

        for user_id in list_user_receive_seen:
            await self.channel_layer.group_send(services.create_socket_bubble_chattag(user_id), {
                'type': 'chat.seen_message',
                'data': {
                    'chatTagId': chat_tag_id,
                    'userSeen': user_seen
                }
            })

    # ----------------------------
    """
    RECEIVE
    """
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        if (text_data_json['event'] == enums.socket_seen_message):
            if not self.is_mode_exp:
                await self.handle_seen_message(text_data_json['data'])
            else:
                await self.handle_seen_message_enjoy(text_data_json['data'])

    # ----------------------------
    """
    SEND
    """
    async def chat_tag(self, event):
        data = event['data']
        await self.send(json.dumps({
            'event': enums.socket_chat_tag,
            'data': data
        }))

    async def send_bubble(self, event):
        data = event['data']
        await self.send(json.dumps({
            'event': enums.socket_bubble,
            'data': data
        }))

    async def chat_delete_bubble(self, event):
        data = event['data']
        await self.send(json.dumps({
            'event': enums.socket_delete_bubble,
            'data': data
        }))

    async def chat_request_public(self, event):
        data = event['data']
        await self.send(json.dumps({
            'event': enums.socket_request_public,
            'data': data
        }))

    async def chat_agree_public(self, event):
        data = event['data']
        await self.send(json.dumps({
            'event': enums.socket_all_agree_public,
            'data': data
        }))

    async def chat_block(self, event):
        data = event['data']
        await self.send(json.dumps({
            'event': enums.socket_is_blocked,
            'data': data
        }))

    async def chat_un_block(self, event):
        data = event['data']
        await self.send(json.dumps({
            'event': enums.socket_un_blocked,
            'data': data
        }))

    async def chat_stop(self, event):
        data = event['data']
        await self.send(json.dumps({
            'event': enums.socket_stop_coversation,
            'data': data
        }))

    async def chat_open(self, event):
        data = event['data']
        await self.send(json.dumps({
            'event': enums.socket_open_conversation,
            'data': data
        }))

    async def chat_seen_message(self, event):
        data = event['data']
        await self.send(json.dumps({
            'event': enums.socket_seen_message,
            'data': data
        }))

    async def chat_change_group_name(self, event):
        data = event['data']
        await self.send(json.dumps({
            'event': enums.socket_change_group_name,
            'data': data
        }))
