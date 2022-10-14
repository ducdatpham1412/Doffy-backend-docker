from bson.objectid import ObjectId
from findme.mongo import mongoDb
from myprofile import models
from myprofile import serializers
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from utilities import enums, services
from utilities.exception import error_key, error_message
from utilities.exception.exception_handler import CustomError
from authentication.models import User
from operator import itemgetter


class CreateGroupBuying(GenericAPIView):
    permission_classes = [IsAuthenticated]

    def check_is_account_shop(self, user_id):
        try:
            User.objects.get(
                id=user_id, is_active=enums.status_active, account_type=enums.account_shop)
        except User.DoesNotExist:
            raise CustomError()

    def get_user_name_avatar(self, user_id):
        query = models.Profile.objects.get(user=user_id)
        data_profile = serializers.ProfileSerializer(query).data
        return {
            'name': data_profile['name'],
            'avatar': data_profile['avatar'],
            'location': query.location
        }

    def post(self, request):
        my_id = services.get_user_id_from_request(request)
        self.check_is_account_shop(user_id=my_id)
        request_data = request.data
        now = services.get_datetime_now()

        is_draft = services.get_object(request_data, 'isDraft')
        if is_draft == None:
            raise CustomError()
        status_post = enums.status_draft if is_draft else enums.status_active

        try:
            sort_prices = sorted(
                request_data['prices'], key=itemgetter('number_people'))
            prices = []
            for item_price in sort_prices:
                prices.append({
                    'number_people': item_price['number_people'],
                    'value': item_price['value']
                })
        except KeyError:
            raise CustomError()

        start_date = services.format_utc_time(request_data['startDate'])
        end_date = services.format_utc_time(request_data['endDate'])
        deadline_date = services.format_utc_time(request_data['deadlineDate'])
        if not start_date or not end_date or not deadline_date:
            raise CustomError()

        info = self.get_user_name_avatar(my_id)

        insert_post = {
            'post_type': enums.post_group_buying,
            'topic': services.get_object(request_data, 'topic'),
            'content': request_data['content'],
            'images': request_data['images'],
            'location': info['location'],
            'prices': prices,
            'start_date': start_date,
            'end_date': end_date,
            'deadline_date': deadline_date,
            'total_reacts': 0,
            'total_comments': 0,
            'total_joins': 0,
            'creator': my_id,
            'created': now,
            'modified': now,
            'status': status_post,
        }
        mongoDb.discovery_post.insert_one(insert_post)

        res_images = []
        for img in insert_post['images']:
            res_images.append(services.create_link_image(img))

        res = {
            'id': str(insert_post['_id']),
            'topic': insert_post['topic'],
            'content': insert_post['content'],
            'images': res_images,
            'prices': prices,
            'startDate': request_data['startDate'],
            'endDate': request_data['endDate'],
            'totalLikes': 0,
            'totalComments': 0,
            'totalJoins': 0,
            'creator': my_id,
            'creatorName': info['name'],
            'creatorAvatar': info['avatar'],
            'creatorLocation': info['location'],
            'created': str(insert_post['created']),
            'relationship': enums.relationship_self
        }

        return Response(res, status=status.HTTP_200_OK)


class EditGroupBuying(GenericAPIView):
    permission_classed = [IsAuthenticated, ]

    def put(self, request, post_id):
        my_id = services.get_user_id_from_request(request)
        request_data = request.data

        content = services.get_object(request_data, 'content', default='')

        post = mongoDb.discovery_post.find_one_and_update(
            {
                '_id': ObjectId(post_id),
                'post_type': enums.post_group_buying,
                'creator': my_id,
                'status': {
                    '$in': [enums.status_active, enums.status_draft],
                }
            },
            {
                '$set': {
                    'content': content,
                    'modified': services.get_datetime_now()
                }
            }
        )

        if not post:
            raise CustomError(error_message.post_not_existed,
                              error_key.post_not_existed)

        return Response(None, status=status.HTTP_200_OK)


class DeleteGroupBuying(GenericAPIView):
    permission_classed = [IsAuthenticated, ]

    def put(self, request, post_id):
        my_id = services.get_user_id_from_request(request)

        post = mongoDb.discovery_post.find_one_and_update(
            {
                '_id': ObjectId(post_id),
                'post_type': enums.post_group_buying,
                'creator': my_id,
                'status': enums.status_active
            },
            {
                '$set': {
                    'status': enums.status_not_active,
                }
            }
        )

        if not post:
            raise CustomError(error_message.post_not_existed,
                              error_key.post_not_existed)

        return Response(None, status=status.HTTP_200_OK)


class JoinGroupBuying(GenericAPIView):
    permission_classes = [IsAuthenticated, ]

    def check_paid(self, user_id, post_id):
        try:
            models.PurchaseHistory.objects.get(user=user_id, post_id=post_id)
        except models.PurchaseHistory.DoesNotExist:
            raise CustomError()

    def put(self, request, post_id):
        my_id = services.get_user_id_from_request(request)

        # Check joined
        check_joined = mongoDb.join_group_buying.find_one({
            'post_id': post_id,
            'creator': my_id,
            'status': {
                '$in': [enums.status_joined_not_bought, enums.status_joined_bought]
            },
        })
        if check_joined:
            raise CustomError(error_message.have_joined_group_buying,
                              error_key.have_joined_group_buying)

        # Check have paid
        self.check_paid(user_id=my_id, post_id=post_id)

        now = services.get_datetime_now()
        post = mongoDb.discovery_post.find_one_and_update(
            {
                '_id': ObjectId(post_id),
                'post_type': enums.post_group_buying,
                'status': enums.status_active,
            },
            {
                '$inc': {
                    'total_joins': 1,
                }
            })
        if not post:
            raise CustomError()
        if post['end_date'] < now:
            mongoDb.discovery_post.update_one(
                {
                    '_id': ObjectId(post_id),
                    'post_type': enums.post_group_buying,
                    'status': enums.status_active,
                },
                {
                    '$inc': {
                        'total_joins': -1,
                    }
                })
            raise CustomError(error_message.group_buying_out_of_date,
                              error_key.group_buying_out_of_date)

        mongoDb.join_group_buying.insert_one({
            'post_id': post_id,
            'creator': my_id,
            'created': now,
            'status': enums.status_joined_not_bought,
        })

        return Response(None, status=status.HTTP_200_OK)


class LeaveGroupBuying(GenericAPIView):
    permission_classes = [IsAuthenticated, ]

    def put(self, request, post_id):
        my_id = services.get_user_id_from_request(request)
        check_joined = mongoDb.join_group_buying.find_one({
            'post_id': post_id,
            'creator': my_id,
            'status': {
                '$in': [enums.status_joined_not_bought, enums.status_joined_bought]
            },
        })
        if not check_joined:
            raise CustomError(error_message.not_joined_group_buying,
                              error_key.not_joined_group_buying)
        if check_joined['status'] == enums.status_joined_bought:
            raise CustomError(error_message.bought_group_buying,
                              error_key.bought_group_buying)

        now = services.get_datetime_now()
        post = mongoDb.discovery_post.find_one_and_update(
            {
                '_id': ObjectId(post_id),
                'post_type': enums.post_group_buying,
                'status': enums.status_active,
            }, {
                '$inc': {
                    'total_joins': -1
                }
            })
        if not post:
            raise CustomError()
        if post['end_date'] < now:
            mongoDb.discovery_post.update_one(
                {
                    '_id': ObjectId(post_id),
                    'post_type': enums.post_group_buying,
                    'status': enums.status_active,
                },
                {
                    '$inc': {
                        'total_joins': 1,
                    }
                })
            raise CustomError(error_message.group_buying_out_of_date,
                              error_key.group_buying_out_of_date)

        mongoDb.join_group_buying.update_one(
            {
                'post_id': post_id,
                'creator': my_id,
                'status': {
                    '$in': [enums.status_joined_not_bought, enums.status_joined_bought]
                },
            },
            {
                '$set': {
                    'status': enums.status_joined_deleted
                }
            }
        )

        return Response(None, status=status.HTTP_200_OK)


class ConfirmUserBoughtGroupBuying(GenericAPIView):
    permission_classes = [IsAuthenticated, ]

    def put(self, request):
        my_id = services.get_user_id_from_request(request)
        post_id = request.data['post_id']
        user_id = request.data['user_id']

        post = mongoDb.discovery_post.find_one({
            '_id': ObjectId(post_id),
            'post_type': enums.post_group_buying,
            'creator': my_id,
            'status': enums.status_active,
        })
        if not post:
            raise CustomError()

        update_joined = mongoDb.join_group_buying.find_one_and_update(
            {
                'post_id': post_id,
                'creator': user_id,
                'status': enums.status_joined_not_bought
            },
            {
                '$set': {
                    'status': enums.status_joined_bought
                }
            }
        )
        if not update_joined:
            raise CustomError(error_message.not_joined_group_buying,
                              error_key.not_joined_group_buying)

        return Response(None, status=status.HTTP_200_OK)
