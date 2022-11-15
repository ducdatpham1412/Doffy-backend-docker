from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from findme.mongo import mongoDb
from utilities.enums import status_active, status_temporarily_closed, status_requesting_delete
from pymongo import DESCENDING
from myprofile.models import Profile
from utilities import services, enums
from authentication.models import User_Request


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
                'status': {
                    '$in': [status_active, status_temporarily_closed, status_requesting_delete]
                },
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
                temp = services.get_index(post['images'], 0)
                temp = services.create_link_image(temp) if temp else ''
                images.append(temp)

            res.append({
                'location': location,
                'total_posts': total_posts,
                'images': images
            })

        return res

    """
    Get top group bookings
    """

    def get_info_creator(self, user_id: int):
        try:
            profile = Profile.objects.get(user=user_id)
            return {
                'name': profile.name,
                'avatar': services.create_link_image(profile.avatar) if profile.avatar else '',
                'location': profile.location,
            }
        except Profile.DoesNotExist:
            return {
                'name': '',
                'avatar': '',
                'location': '',
            }

    def check_liked_and_status_joined(self, user_id: int, post_id: str):
        if (user_id == None):
            return {
                'is_liked': True,
                'join': {
                    'deposit': None,
                    'amount': None,
                    'note': None,
                    'status': enums.status_not_joined,
                }
            }

        check_liked = mongoDb.reaction.find_one({
            'type': enums.react_post,
            'reacted_id': post_id,
            'creator': user_id,
            'status': enums.status_active,
        })
        is_liked = bool(check_liked)

        status_joined = enums.status_not_joined
        deposit = None
        amount = None
        note = None
        check_joining = mongoDb.join_personal.find_one({
            'post_id': post_id,
            'creator': user_id,
            'status': enums.status_joined_not_bought,
        })
        if check_joining:
            status_joined = enums.status_joined_not_bought,
            deposit = check_joining['money']
            amount = check_joining['amount']
            note = check_joining['note']

        return {
            'is_liked': is_liked,
            'join': {
                'deposit': deposit,
                'amount': amount,
                'note': note,
                'status': status_joined,
            }
        }

    def get_top_group_bookings(self, my_id: int):
        list_posts = mongoDb.discovery_post.aggregate([
            {
                '$match': {
                    'post_type': enums.post_group_buying,
                    'status': enums.status_active,
                }
            },
            {
                '$sort': {
                    'created': DESCENDING,
                    'total_reacts': DESCENDING,
                    'total_groups': DESCENDING,
                }
            },
            {
                '$limit': 10,
            }
        ])

        """
        This is for update all joining and joined
        Choose this api because it's called one time in app cycle
        """
        if my_id:
            now = services.get_datetime_now()
            list_joined_not_bought = mongoDb.join_personal.find({
                'creator': my_id,
                'status': enums.status_joined_not_bought,
            })
            for joined in list_joined_not_bought:
                if joined['time_will_buy'] < now:
                    mongoDb.join_personal.update_one(
                        {
                            '_id': joined['_id'],
                        },
                        {
                            '$set': {
                                'status': enums.status_joined_bought
                            }
                        }
                    )
        """
        ------------------------
        """

        res = []
        for post in list_posts:
            link_images = []
            for image in post['images']:
                temp = services.create_link_image(image)
                link_images.append(temp)

            info_creator = self.get_info_creator(user_id=post['creator'])

            check_liked_joined = self.check_liked_and_status_joined(
                user_id=my_id, post_id=str(post['_id']))
            is_liked = check_liked_joined['is_liked']
            join = check_liked_joined['join']

            relationship = enums.relationship_self if post[
                'creator'] == my_id else enums.relationship_not_know

            request_update_price = None
            if post['creator'] == my_id:
                try:
                    user_request = User_Request.objects.get(creator=my_id, post_id=str(
                        post['_id']), type=enums.request_update_price, status=enums.status_active)
                    data = services.str_to_dict(user_request.data)
                    request_update_price = {
                        'retailPrice': data['retail_price'],
                        'prices': data['prices']
                    }
                except:
                    pass

            temp = {
                'id': str(post['_id']),
                'postType': enums.post_group_buying,
                'topic': post['topic'],
                'content': post['content'],
                'images': link_images,
                'retailPrice': post['retail_price'],
                'prices': post['prices'],
                'deposit': join['deposit'],
                'amount': join['amount'],
                'note': join['note'],
                'totalLikes': post['total_reacts'],
                'totalComments': post['total_comments'],
                'totalGroups': post['total_groups'],
                'totalPersonals': post['total_personals'],
                'creator': post['creator'],
                'creatorName': info_creator['name'],
                'creatorAvatar': info_creator['avatar'],
                'creatorLocation': info_creator['location'],
                'created': str(post['created']),
                'isLiked': is_liked,
                'status': join['status'],
                'postStatus': post['status'],
                'relationship': relationship,
                'requestUpdatePrice': request_update_price,
            }

            res.append(temp)

        return res

    def get(self, request):
        my_id = services.get_user_id_from_request(request)

        mongo_resource = mongoDb.resource.find()
        image_background = mongo_resource[0]['image_background']
        gradient = mongo_resource[1]['gradient']
        list_banners = mongo_resource[3]['list_banners']
        list_prices = mongo_resource[4]['list_prices']
        list_purchases = mongo_resource[5]['list_purchases']
        hot_locations = self.get_hot_locations()
        top_group_bookings = self.get_top_group_bookings(my_id=my_id)

        res = {
            'imageBackground': image_background,
            'gradients': gradient,
            'banners': list_banners,
            'hotLocations': hot_locations,
            'listPrices': list_prices,
            'listPurchases': list_purchases,
            'topGroupBookings': top_group_bookings,
        }

        return Response(res, status=status.HTTP_200_OK)
