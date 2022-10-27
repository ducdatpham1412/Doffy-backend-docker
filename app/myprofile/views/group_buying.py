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
from authentication.models import User, User_Request


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

        retail_price = services.get_object(request_data, 'retailPrice')
        if not retail_price:
            raise CustomError()
        prices = services.sort_prices(request_data['prices'])

        info = self.get_user_name_avatar(my_id)

        insert_post = {
            'post_type': enums.post_group_buying,
            'topic': services.get_object(request_data, 'topic'),
            'content': request_data['content'],
            'images': request_data['images'],
            'location': info['location'],
            'retail_price': retail_price,
            'prices': prices,
            'total_reacts': 0,
            'total_comments': 0,
            'total_groups': 0,
            'total_personals': 0,
            'creator': my_id,
            'created': now,
            'modified': now,
            'status': status_post,
        }
        mongoDb.discovery_post.insert_one(insert_post)

        mongoDb.discovery_edit_history.insert_one({
            'post_id': str(insert_post['_id']),
            'retail_price': retail_price,
            'prices': prices,
            'created': now,
        })

        res_images = []
        for img in insert_post['images']:
            res_images.append(services.create_link_image(img))

        res = {
            'id': str(insert_post['_id']),
            'postType': enums.post_group_buying,
            'topic': insert_post['topic'],
            'content': insert_post['content'],
            'images': res_images,
            'retailPrice': retail_price,
            'prices': prices,
            'deposit': None,
            'amount': None,
            'note': None,
            'totalLikes': 0,
            'totalComments': 0,
            'totalGroups': 0,
            'totalPersonals': 0,
            'creator': my_id,
            'creatorName': info['name'],
            'creatorAvatar': info['avatar'],
            'creatorLocation': info['location'],
            'created': str(insert_post['created']),
            'isLiked': False,
            'isDraft': False,
            'status': enums.status_not_joined,
            'postStatus': enums.status_active,
            'relationship': enums.relationship_self
        }

        return Response(res, status=status.HTTP_200_OK)


class EditGroupBuying(GenericAPIView):
    permission_classed = [IsAuthenticated, ]

    def disable_request_delete_gb(self, user_id, post_id):
        try:
            data = str({
                'post_id': post_id
            })
            user_request = User_Request.objects.get(
                creator=user_id, data=data, status=enums.status_active)
            user_request.status = enums.status_not_active
            user_request.save()
        except User_Request.DoesNotExist:
            pass

    def add_request_update_price(self, user_id, post_id, retail_price, prices):
        update_price = {
            'retail_price': retail_price,
            'prices': prices,
        }
        update_price = str(update_price)

        # check had request before
        try:
            User_Request.objects.get(
                type=enums.request_update_price, post_id=post_id, creator=user_id, status=enums.status_active)
            raise CustomError()
        except User_Request.DoesNotExist:
            pass

        user = User.objects.get(id=user_id)
        now = services.get_datetime_now()
        new_request = User_Request(type=enums.request_update_price,
                                   created=now, expired=now, post_id=post_id, data=update_price, creator=user)
        new_request.save()

    def reject_update_price(self, user_id, post_id):
        try:
            user_request = User_Request.objects.get(
                type=enums.request_update_price, creator=user_id, post_id=post_id)
            user_request.status = enums.status_not_active
            user_request.save()
        except User_Request.DoesNotExist:
            raise CustomError()

    def put(self, request, post_id):
        my_id = services.get_user_id_from_request(request)
        request_data = request.data

        post = mongoDb.discovery_post.find_one({
            '_id': ObjectId(post_id),
            'post_type': enums.post_group_buying,
            'creator': my_id,
            'status': {
                '$ne': enums.status_not_active
            }
        })

        # Post deleted or not existed
        if not post:
            raise CustomError()

        # Update status follow each status
        if post['status'] == enums.status_active:
            topic = services.get_object(request_data, 'topic')
            content = services.get_object(request_data, 'content')
            post_status = services.get_object(request_data, 'status')

            update_object = {}
            if topic != None:
                update_object['topic'] = topic
            if content != None:
                update_object['content'] = content
            if post_status == enums.status_temporarily_closed:
                update_object['status'] = enums.status_temporarily_closed
            update_object['modified'] = services.get_datetime_now()

            mongoDb.discovery_post.update_one(
                {
                    '_id': ObjectId(post_id),
                },
                {
                    '$set': update_object,
                }
            )

            retail_price = services.get_object(request_data, 'retail_price')
            prices = services.get_object(request_data, 'prices')
            reject_request_update_price = services.get_object(
                request_data, 'reject_request_update_price')
            if retail_price and prices:
                self.add_request_update_price(
                    user_id=my_id, post_id=post_id, retail_price=retail_price, prices=services.sort_prices(prices))
            elif reject_request_update_price == True:
                self.reject_update_price(user_id=my_id, post_id=post_id)

        elif post['status'] == enums.status_temporarily_closed:
            topic = services.get_object(request_data, 'topic')
            content = services.get_object(request_data, 'content')
            post_status = services.get_object(request_data, 'status')

            update_object = {}
            if topic != None:
                update_object['topic'] = topic
            if content != None:
                update_object['content'] = content
            if post_status == enums.status_active:
                update_object['status'] = enums.status_active
            update_object['modified'] = services.get_datetime_now()

            mongoDb.discovery_post.update_one(
                {
                    '_id': ObjectId(post_id)
                },
                {
                    '$set': update_object,
                }
            )

            retail_price = services.get_object(request_data, 'retail_price')
            prices = services.get_object(request_data, 'prices')
            reject_request_update_price = services.get_object(
                request_data, 'reject_request_update_price')
            if retail_price and prices:
                self.add_request_update_price(
                    user_id=my_id, post_id=post_id, retail_price=retail_price, prices=services.sort_prices(prices))
            elif reject_request_update_price == True:
                self.reject_update_price(user_id=my_id, post_id=post_id)

        elif post['status'] == enums.status_requesting_delete:
            post_status = services.get_object(request_data, 'status')
            if post_status == enums.status_active:
                mongoDb.discovery_post.update_one(
                    {
                        '_id': ObjectId(post_id)
                    },
                    {
                        '$set': {
                            'status': enums.status_active,
                        }
                    }
                )

        elif post['status'] == enums.status_draft:
            topic = services.get_object(request_data, 'topic')
            content = services.get_object(request_data, 'content')
            post_status = services.get_object(request_data, 'status')
            retail_price = services.get_object(request_data, 'retail_price')
            prices = services.get_object(request_data, 'prices')

            update_object = {}
            if topic != None:
                update_object['topic'] = topic
            if content != None:
                update_object['content'] = content
            if post_status == enums.status_active:
                update_object['status'] = enums.status_active
            if retail_price != None:
                update_object['retail_price'] = retail_price
            if prices != None:
                update_object['prices'] = services.sort_prices(prices=prices)

            mongoDb.discovery_post.update_one(
                {
                    '_id': ObjectId(post_id)
                },
                {
                    '$set': update_object
                }
            )

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
                'status': {
                    '$in': [enums.status_active, enums.status_temporarily_closed]
                }
            },
            {
                '$set': {
                    'status': enums.status_requesting_delete,
                }
            }
        )
        if not post:
            raise CustomError(error_message.post_not_existed,
                              error_key.post_not_existed)

        user = User.objects.get(id=my_id)
        now = services.get_datetime_now()
        data = str({
            'post_id': post_id,
        })

        # Check had request delete before
        try:
            User_Request.objects.get(
                creator=my_id, type=enums.request_delete_gb, data=data, status=enums.status_active)
            raise CustomError()
        except User_Request.DoesNotExist:
            pass

        user_request = User_Request(creator=user, type=enums.request_delete_gb,
                                    created=now, expired=now, data=data)
        user_request.save()

        return Response(None, status=status.HTTP_200_OK)


class JoinGroupBuying(GenericAPIView):
    permission_classes = [IsAuthenticated, ]

    def put(self, request, post_id):
        my_id = services.get_user_id_from_request(request)

        post = mongoDb.discovery_post.find_one({
            '_id': ObjectId(post_id),
            'post_type': enums.post_group_buying,
            'status': enums.status_active,
        })
        if not post:
            raise CustomError(error_message.post_not_existed,
                              error_key.post_not_existed)

        # check user had added phone
        user = User.objects.get(id=my_id)
        if not user.phone:
            raise CustomError()

        now = services.get_datetime_now()

        # Check joined
        check_joined = mongoDb.join_personal.find_one({
            'post_id': post_id,
            'creator': my_id,
            'status': enums.status_joined_not_bought,
        })
        if check_joined:
            if check_joined['time_will_buy'] > now:
                raise CustomError(error_message.have_joined_group_buying,
                                  error_key.have_joined_group_buying)
            else:
                mongoDb.join_personal.update_one(
                    {
                        '_id': check_joined['_id'],
                    },
                    {
                        '$set': {
                            'status': enums.status_joined_bought,
                        }
                    }
                )

        res = {
            'groupId': None,
            'joinId': ''
        }

        # Find group to join, if not found group or group's enough, create new one
        request_data = request.data
        money = request_data['money']
        amount = request_data['amount']
        time_will_buy = request_data['time_will_buy']
        time_will_buy = services.format_utc_time(time_will_buy)
        note = request_data['note']
        is_retail = request_data['is_retail']

        if is_retail:
            join_personal = {
                'post_id': post_id,
                'join_group_id': None,
                'money': money,
                'amount': amount,
                'time_will_buy': time_will_buy,
                'note': note,
                'creator': my_id,
                'created': now,
                'status': enums.status_joined_not_bought,
            }
            mongoDb.join_personal.insert_one(join_personal)
            res['joinId'] = str(join_personal['_id'])
        else:
            prices = post['prices']
            max_number_people = prices[len(prices) - 1]['number_people']

            check_join_group = mongoDb.join_group.find_one({
                'post_id': post_id,
                'total_members': {
                    '$lt': max_number_people,
                }
            })

            if not check_join_group:
                join_group = mongoDb.join_group.insert_one({
                    'post_id': post_id,
                    'total_members': amount,
                    'created': now,
                })
                join_personal = mongoDb.join_personal.insert_one({
                    'post_id': post_id,
                    'join_group_id': str(join_group['_id']),
                    'money': money,
                    'amount': amount,
                    'time_will_buy': time_will_buy,
                    'note': note,
                    'creator': my_id,
                    'created': now,
                    'status': enums.status_joined_not_bought,
                })
                res['groupId'] = str(join_group['_id'])
                res['joinId'] = str(join_personal['_id'])
            else:
                join_personal = mongoDb.join_personal.insert_one({
                    'post_id': post_id,
                    'join_group_id': str(check_join_group['_id']),
                    'money': money,
                    'amount': amount,
                    'time_will_buy': time_will_buy,
                    'note': note,
                    'creator': my_id,
                    'created': now,
                    'status': enums.status_joined_not_bought,
                })
                mongoDb.join_group.find_one_and_update(
                    {
                        '_id': check_join_group['_id']
                    },
                    {
                        '$inc': {
                            'total_members': amount,
                        }
                    }
                )
                res['groupId'] = str(check_join_group['_id'])
                res['joinId'] = str(join_personal['_id'])

        update_object = {
            '$inc': {}
        }
        if is_retail:
            update_object['$inc'] = {
                'total_personals': amount
            }
        else:
            update_object['$inc'] = {
                'total_groups': 1
            }
        mongoDb.discovery_post.find_one_and_update(
            {
                '_id': ObjectId(post_id),
            },
            {
                '$inc': update_object,
            })

        return Response(res, status=status.HTTP_200_OK)


class ConfirmUserBoughtGroupBuying(GenericAPIView):
    permission_classes = [IsAuthenticated, ]

    def put(self, request, join_id):
        my_id = services.get_user_id_from_request(request)

        join_personal = mongoDb.join_personal.find_one({
            '_id': ObjectId(join_id),
            'status': enums.status_joined_not_bought,
        })
        if not join_personal:
            raise CustomError()

        post = mongoDb.discovery_post.find_one({
            '_id': ObjectId(join_personal['post_id']),
            'post_type': enums.post_group_buying,
            'creator': my_id,
            'status': {
                '$in': [enums.status_active, enums.status_requesting_delete, enums.status_temporarily_closed]
            },
        })
        if not post:
            raise CustomError()

        mongoDb.join_personal.update_one(
            {
                '_id': ObjectId(join_id),
                'status': enums.status_joined_not_bought
            },
            {
                '$set': {
                    'status': enums.status_joined_bought
                }
            }
        )

        return Response(None, status=status.HTTP_200_OK)
