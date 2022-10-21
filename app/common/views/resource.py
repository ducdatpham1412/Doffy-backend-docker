from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from findme.mongo import mongoDb
from utilities.enums import status_active
from pymongo import DESCENDING
from utilities.services import get_index, create_link_image


class GetResource(GenericAPIView):
    def get_hot_locations(self):
        list_locations = ['Ha Giang', 'Ha Noi', 'Son La']

        res = []

        for location in list_locations:
            condition = {
                '$text': {
                    '$search': "\"{}\"".format(location),
                    '$caseSensitive': False,
                },
                'status': status_active,
            }

            total_posts = mongoDb.discovery_post.count(condition)

            four_posts = mongoDb.discovery_post.aggregate([
                {
                    '$match': condition,
                },
                {
                    '$sort': {
                        'created': DESCENDING
                    }
                },
                {
                    '$limit': 4
                }
            ])
            images = []
            for post in four_posts:
                temp = get_index(post['images'], 0)
                temp = create_link_image(temp) if temp else ''
                images.append(temp)

            res.append({
                'location': location,
                'total_posts': total_posts,
                'images': images
            })

        return res

    def get(self, request):
        mongo_resource = mongoDb.resource.find()
        image_background = mongo_resource[0]['image_background']
        gradient = mongo_resource[1]['gradient']
        list_banners = mongo_resource[3]['list_banners']
        list_prices = mongo_resource[4]['list_prices']
        hot_locations = self.get_hot_locations()

        res = {
            'imageBackground': image_background,
            'gradients': gradient,
            'banners': list_banners,
            'hotLocations': hot_locations,
            'listPrices': list_prices,
        }

        return Response(res, status=status.HTTP_200_OK)
