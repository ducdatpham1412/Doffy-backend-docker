from utilities.exception.exception_handler import CustomError
from findme.mongo import mongoDb
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from utilities import services
from utilities.renderers import PagingRenderer
import pymongo
from utilities import enums
from myprofile.models import Profile
from bson.objectid import ObjectId


class GestListNotification(GenericAPIView):
    permission_classes = [IsAuthenticated, ]
    renderer_classes = [PagingRenderer, ]

    def get_creator_info(self, user_id):
        try:
            profile = Profile.objects.get(user=user_id)
            return {
                'creator': user_id,
                'creatorName': profile.name,
                'creatorAvatar': services.create_link_image(profile.avatar)
            }
        except Profile.DoesNotExist:
            return None

    def get_image_of_post(self, post_id):
        post = mongoDb.discovery_post.find_one({
            '_id': ObjectId(post_id)
        })
        check = services.get_object(post, 'images', default=[''])[0]
        return services.create_link_image(check) if check else ''

    def get(self, request):
        my_id = services.get_user_id_from_request(request)
        take = int(request.query_params['take'])
        page_index = int(request.query_params['pageIndex'])

        total_items = mongoDb.notification.count({
            'user_id': my_id,
            'status': {
                '$in': [enums.status_notification_read, enums.status_notification_not_read]
            }
        })

        list_notifications = mongoDb.notification.find({
            'user_id': my_id,
            'status': {
                '$in': [enums.status_notification_read, enums.status_notification_not_read]
            }
        }).sort([('created', pymongo.DESCENDING)]).limit(take).skip((page_index-1) * take)
        list_notifications = list(list_notifications)

        res_notifications = []
        for notification in list_notifications:
            creator_info = self.get_creator_info(
                user_id=notification['creator'])
            if not creator_info:
                continue
            post_info = {}
            if services.get_object(notification, 'post_id'):
                post_info['image'] = self.get_image_of_post(
                    notification['post_id'])
                post_info['postId'] = notification['post_id']

            temp = {
                'id': str(notification['_id']),
                'type': notification['type'],
                **post_info,
                **creator_info,
                'created': str(notification['created']),
                'isRead': notification['status'] == enums.status_notification_read
            }

            res_notifications.append(temp)

        res = {
            'take': take,
            'pageIndex': page_index,
            'totalItems': total_items,
            'data': res_notifications,
        }

        return Response(res, status=status.HTTP_200_OK)


class ReadNotification(GenericAPIView):
    permission_classes = [IsAuthenticated, ]

    def put(self, request, notification_id):
        my_id = services.get_user_id_from_request(request)

        notification = mongoDb.notification.find_one_and_update(
            {
                '_id': ObjectId(notification_id),
                'user_id': my_id,
                'status': enums.status_notification_not_read
            },
            {
                '$set': {
                    'status': enums.status_notification_read,
                }
            }
        )
        if not notification:
            raise CustomError()

        return Response(None, status=status.HTTP_200_OK)
