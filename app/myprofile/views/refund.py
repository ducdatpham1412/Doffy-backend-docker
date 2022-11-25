from bson.objectid import ObjectId
from findme.mongo import mongoDb
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from utilities import enums, services
from utilities.exception.exception_handler import CustomError
from pymongo import DESCENDING


class Refund(GenericAPIView):
    permission_classes = [IsAuthenticated, ]

    def put(self, request, join_id):
        my_id = services.get_user_id_from_request(request)
        now = services.get_datetime_now()

        join_personal = mongoDb.join_personal.find_one({
            '_id': ObjectId(join_id),
            'status': enums.status_joined_not_bought,
        })
        if not join_personal:
            raise CustomError()
        if join_personal['time_will_buy'] < now:
            mongoDb.join_personal.update_one(
                {
                    '_id': ObjectId(join_id)
                },
                {
                    'status': enums.status_joined_bought,
                }
            )
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

        if join_personal['join_group_id'] == None:
            mongoDb.join_personal.update_one(
                {
                    '_id': ObjectId(join_id)
                },
                {
                    '$set': {
                        'status': enums.status_joined_deleted
                    }
                }
            )

        else:
            join_group = mongoDb.join_group.find_one({
                '_id': ObjectId(join_personal['join_group_id']),
                'post_id': str(post['_id']),
            })
            if not join_group:
                raise CustomError()

            list_personals = mongoDb.join_personal.aggregate([
                {
                    '$match': {
                        'join_group_id': str(join_group['_id']),
                        'status': enums.status_joined_not_bought,
                    }
                },
                {
                    '$sort': {
                        'created': DESCENDING,
                    }
                }
            ])
            list_personals = list(list_personals)
            if str(list_personals[len(list_personals) - 1]['_id']) != join_id:
                raise CustomError()

            mongoDb.join_personal.update_one(
                {
                    '_id': ObjectId(join_id)
                },
                {
                    '$set': {
                        'status': enums.status_joined_deleted
                    }
                }
            )

        # Call function notification, mail to buyer and cash back to buyer

        return Response(None, status=status.HTTP_200_OK)
