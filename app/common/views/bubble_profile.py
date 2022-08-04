from findme.mongo import mongoDb
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from utilities import enums, services
from setting.models import Information
from bson.objectid import ObjectId
from myprofile.models import Profile
from utilities.exception.exception_handler import CustomError
from utilities.exception import error_message, error_key


class GetListBubbleProfile(GenericAPIView):
    permission_classes = [IsAuthenticated, ]

    def get(self, request):
        my_id = services.get_user_id_from_request(request)
        take = int(request.query_params['take'])
        page_index = int(request.query_params['pageIndex'])

        analysis = mongoDb.analysis.find_one({
            'type': 'priority'
        })

        total = analysis['totalPosts']
        start = (take * (page_index-1)) % total
        end = start + take

        all_post = [*analysis['one'], *analysis['two'],
                    *analysis['three'], *analysis['four']]

        if take >= total:
            list_post_id = all_post
        elif end < total:
            list_post_id = all_post[start:end]
        else:
            list_post_id = [*all_post[start:total], *all_post[0:(end % total)]]

        list_user_i_know = services.get_list_user_id_i_know(my_id)

        res = []
        for profile_post_id in list_post_id:
            post = mongoDb.profilePost.find_one({
                '_id': ObjectId(profile_post_id)
            })

            if not post:
                continue

            link_images = []
            for image in post['images']:
                temp = services.create_link_image(image) if image else ''
                link_images.append(temp)

            is_liked = False
            for people in post['peopleLike']:
                if people['id'] == my_id:
                    is_liked = True
                    break

            information = Information.objects.get(user=post['creatorId'])
            profile = Profile.objects.get(user=post['creatorId'])

            is_my_post = post['creatorId'] == my_id

            relationship = enums.relationship_self if is_my_post else enums.relationship_not_know

            had_know_other = True if is_my_post else services.check_had_i_know(
                list_user_id=list_user_i_know, partner_id=post['creatorId'])
            creator_name = profile.name if had_know_other else profile.anonymous_name
            creator_avatar = services.create_link_image(
                profile.avatar) if had_know_other else None

            res.append({
                'id': str(post['_id']),
                'content': post['content'],
                'images': link_images,
                'totalLikes': post['totalLikes'],
                'totalComments': post['totalComments'],
                'hadKnowEachOther': had_know_other,
                'creatorId': post['creatorId'],
                'creatorName': creator_name,
                'creatorAvatar': creator_avatar,
                'gender': information.gender,
                'createdTime': str(post['createdTime']),
                'color': post['color'],
                'name': post['name'],
                'isLiked': is_liked,
                'relationship': relationship
            })

        return Response(res, status=status.HTTP_200_OK)


class GetListBubbleProfileOfUserEnjoy(GenericAPIView):
    def get(self, request):
        take = int(request.query_params['take'])
        page_index = int(request.query_params['pageIndex'])

        analysis = mongoDb.analysis.find_one()

        total = analysis['totalPosts']
        start = (take * (page_index-1)) % total
        end = start + take

        all_post = [*analysis['one'], *analysis['two'],
                    *analysis['three'], *analysis['four']]

        if take >= total:
            list_post_id = all_post
        elif end < total:
            list_post_id = all_post[start:end]
        else:
            list_post_id = [*all_post[start:total], *all_post[0:(end % total)]]

        res = []
        for profile_post_id in list_post_id:
            post = mongoDb.profilePost.find_one({
                '_id': ObjectId(profile_post_id)
            })

            if not post:
                continue

            link_images = []
            for image in post['images']:
                link_images.append(services.create_link_image(image))

            is_liked = True

            information = Information.objects.get(user=post['creatorId'])
            profile = Profile.objects.get(user=post['creatorId'])

            relationship = enums.relationship_not_know

            res.append({
                'id': str(post['_id']),
                'content': post['content'],
                'images': link_images,
                'totalLikes': post['totalLikes'],
                'totalComments': post['totalComments'],
                'hadKnowEachOther': False,
                'creatorId': post['creatorId'],
                'creatorName': profile.anonymous_name,
                'creatorAvatar': None,
                'gender': information.gender,
                'createdTime': str(post['createdTime']),
                'color': post['color'],
                'name': post['name'],
                'isLiked': is_liked,
                'relationship': relationship
            })

        return Response(res, status=status.HTTP_200_OK)


class GetDetailBubbleProfile(GenericAPIView):
    permission_classes = [IsAuthenticated, ]

    def get(self, request, bubble_id):
        my_id = services.get_user_id_from_request(request)

        post = mongoDb.profilePost.find_one({
            '_id': ObjectId(bubble_id)
        })
        if not post:
            raise CustomError(error_message.post_not_existed,
                              error_key.post_not_existed)

        link_images = []
        for image in post['images']:
            link_images.append(services.create_link_image(image))

        is_liked = False
        for people in post['peopleLike']:
            if people['id'] == my_id:
                is_liked = True
                break

        information = Information.objects.get(user=post['creatorId'])
        profile = Profile.objects.get(user=post['creatorId'])

        is_my_post = post['creatorId'] == my_id

        relationship = enums.relationship_self if is_my_post else enums.relationship_not_know

        list_user_i_know = services.get_list_user_id_i_know(my_id)
        had_know_other = True if is_my_post else services.check_had_i_know(
            list_user_id=list_user_i_know, partner_id=post['creatorId'])

        creator_name = profile.name if had_know_other else profile.anonymous_name
        creator_avatar = services.create_link_image(
            profile.avatar) if had_know_other else None

        res = {
            'id': str(post['_id']),
            'content': post['content'],
            'images': link_images,
            'totalLikes': post['totalLikes'],
            'totalComments': post['totalComments'],
            'hadKnowEachOther': had_know_other,
            'creatorId': post['creatorId'],
            'creatorName': creator_name,
            'creatorAvatar': creator_avatar,
            'gender': information.gender,
            'createdTime': str(post['createdTime']),
            'color': post['color'],
            'name': post['name'],
            'isLiked': is_liked,
            'relationship': relationship
        }

        return Response(res, status=status.HTTP_200_OK)


class GetDetailBubbleProfileEnjoy(GenericAPIView):
    def get(self, request, bubble_id):
        post = mongoDb.profilePost.find_one({
            '_id': ObjectId(bubble_id)
        })
        if not post:
            raise CustomError(error_message.post_not_existed,
                              error_key.post_not_existed)

        link_images = []
        for image in post['images']:
            link_images.append(services.create_link_image(image))

        is_liked = True

        information = Information.objects.get(user=post['creatorId'])
        profile = Profile.objects.get(user=post['creatorId'])

        relationship = enums.relationship_not_know

        res = {
            'id': str(post['_id']),
            'content': post['content'],
            'images': link_images,
            'totalLikes': post['totalLikes'],
            'totalComments': post['totalComments'],
            'hadKnowEachOther': False,
            'creatorId': post['creatorId'],
            'creatorName': profile.anonymous_name,
            'creatorAvatar': None,
            'gender': information.gender,
            'createdTime': str(post['createdTime']),
            'color': post['color'],
            'name': post['name'],
            'isLiked': is_liked,
            'relationship': relationship
        }

        return Response(res, status=status.HTTP_200_OK)
