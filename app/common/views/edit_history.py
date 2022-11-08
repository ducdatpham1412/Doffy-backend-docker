from findme.mongo import mongoDb
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
import pymongo
from utilities.renderers import PagingRenderer


class GetListEditHistory(GenericAPIView):
    permission_classes = [AllowAny, ]
    renderer_classes = [PagingRenderer, ]

    def get(self, request, post_id):
        take = int(request.query_params['take'])
        page_index = int(request.query_params['pageIndex'])

        list_edit_history = mongoDb.discovery_edit_history.aggregate([
            {
                '$match': {
                    'post_id': post_id,
                }
            },
            {
                '$sort': {
                    'created': pymongo.DESCENDING,
                }
            },
            {
                '$limit': take,
            },
            {
                '$skip': (page_index - 1) * take
            },
        ])

        total_items = mongoDb.discovery_edit_history.count({
            'post_id': post_id,
        })

        list_res = []
        for history in list_edit_history:
            temp = {
                'id': str(history['_id']),
                'retailPrice': history['retail_price'],
                'prices': history['prices'],
                'created': str(history['created'])
            }
            list_res.append(temp)

        res = {
            'take': take,
            'pageIndex': page_index,
            'totalItems': total_items,
            'data': list_res
        }

        return Response(res, status=status.HTTP_200_OK)
