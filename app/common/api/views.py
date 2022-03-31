from distutils.command.build_ext import build_ext
from locale import resetlocale
from authentication.models import User
from common import models
from common.api import serializers
from common.forms import ImageForm
from findme.mongo import mongoDb
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from utilities import enums, services
from utilities.exception.exception_handler import CustomError
from setting.models import Information
from bson.objectid import ObjectId
from utilities.exception import error_message, error_key
from myprofile.models import Profile


class GetPassport(GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        id = services.get_user_id_from_request(request)
        user = User.objects.get(id=id)
        passport = serializers.GetPassportSerializer(user).data

        return Response(passport, status=status.HTTP_200_OK)


class UploadImage(GenericAPIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_quality(self, request):
        try:
            temp = int(request.query_params['quality'])
            return temp
        except KeyError:
            return 150

    def post(self, request):
        id = services.get_user_id_from_request(request)
        quality = self.get_quality(request)

        res = []
        form = ImageForm(request.POST, request.data)
        if form.is_valid():
            list_image = form.files.getlist('image')

            for image in list_image:
                time_stamp = services.get_datetime_now().timestamp()
                name = int(float(time_stamp) * 1000)
                image.name = '{0}{1}.jpeg'.format(id, name)

                resize_image = services.handle_resize_image(image, quality)
                models.Images.objects.create(image=resize_image)
                # serializer = serializers.ImageSerializer(temp)
                res.append(image.name)

        return Response(res, status=status.HTTP_200_OK)


class GetResource(GenericAPIView):
    # permission_classes = [IsAuthenticated]

    def get_list_hobbies(self):
        query = models.Hobby.objects.all()
        list_hobbiles = serializers.HobbySerializer(query, many=True).data
        return list_hobbiles

    def get(self, request):
        mongo_resource = mongoDb.resource.find()
        image_background = mongo_resource[0]['imageBackground']
        gradient = mongo_resource[1]['gradient']

        res = {
            'listHobbies': self.get_list_hobbies(),
            'imageBackground': image_background,
            'gradient': gradient
        }

        return Response(res, status=status.HTTP_200_OK)


class UpdateMyBubbles(GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get_user(self, id):
        try:
            return User.objects.get(id=id)
        except:
            raise CustomError()

    def save_to_data(self, user_id, update_data):
        try:
            my_bubbles = models.MyBubbles.objects.get(user=user_id)
            my_bubbles.listHobbies = update_data['listHobbies']
            my_bubbles.listDescriptions = update_data['listDescriptions']
            my_bubbles.save()

        except models.MyBubbles.DoesNotExist:
            user = self.get_user(user_id)
            models.MyBubbles.objects.create(user=user, **update_data)

    def put(self, request):
        id = services.get_user_id_from_request(request)

        update_data = {
            'listHobbies': [],
            'listDescriptions': [],
        }

        for bubble in request.data:
            update_data['listHobbies'].append(bubble['idHobby'])
            update_data['listDescriptions'].append(bubble['description'])

        self.save_to_data(id, update_data)
        # print(request.data)

        return Response(None, status=status.HTTP_200_OK)


class ReportUser(GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, user_id):
        my_id = services.get_user_id_from_request(request)
        reason = request.data['reason']
        description = request.data['description']
        list_images = request.data['listImages']

        insert_report_user = {
            'reason': reason,
            'description': description,
            'listImages': list_images,
            'reportedUserId': user_id,
            'creatorId': my_id,
            'createdTime': services.get_datetime_now()
        }
        mongoDb.reportUser.insert_one(insert_report_user)

        return Response(None, status=status.HTTP_200_OK)


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


class GetListComment(GenericAPIView):
    permission_classes = [IsAuthenticated, ]
    list_user_i_know = []

    def check_i_have_know(self, user_id):
        for id in self.list_user_i_know:
            if id == user_id:
                return True
        return False

    def get_avatar_name(self, user_id: int, had_know: bool):
        profile = Profile.objects.get(user=user_id)

        if had_know:
            return {
                'name': profile.name,
                'avatar': services.create_link_image(profile.avatar)
            }

        information = Information.objects.get(user=user_id)
        return {
            'name': profile.anonymous_name,
            'avatar': services.choose_private_avatar(information.gender)
        }

    def get(self, request, bubble_id):
        my_id = services.get_user_id_from_request(request)
        self.list_user_i_know = services.get_list_user_id_i_know(my_id)

        post = mongoDb.profilePost.find_one({
            '_id': ObjectId(bubble_id)
        })

        id_name_avatar_object = {}

        for user_comment in post['listUsersComment']:
            check_i_had_know = self.check_i_have_know(user_comment)

            if user_comment == my_id:
                avatar_name = self.get_avatar_name(my_id, True)
            else:
                avatar_name = self.get_avatar_name(
                    user_comment, check_i_had_know)

            id_name_avatar_object['{}'.format(user_comment)] = {
                'id': user_comment if check_i_had_know else None,
                'name': avatar_name['name'],
                'avatar': avatar_name['avatar'],
            }

        res = []
        for comment in post['listComments']:
            is_liked = services.check_include(
                list=comment['peopleLike'], value=my_id)
            id_name_avatar = id_name_avatar_object['{}'.format(
                comment['creatorId'])]

            list_replies = []
            for comment_reply in comment['listCommentsReply']:
                id_name_avatar_reply = id_name_avatar_object['{}'.format(
                    comment_reply['creatorId'])]
                is_liked_reply = services.check_include(
                    list=comment_reply['peopleLike'], value=my_id)

                list_replies.append({
                    'id': comment_reply['id'],
                    'content': comment_reply['content'],
                    'numberLikes': len(comment_reply['peopleLike']),
                    'isLiked': is_liked_reply,
                    'creatorId': id_name_avatar_reply['id'],
                    'creatorName': id_name_avatar_reply['name'],
                    'creatorAvatar': id_name_avatar_reply['avatar'],
                    'createdTime': services.get_local_string_date_time(comment_reply['createdTime']),
                })

            res.append({
                'id': comment['id'],
                'content': comment['content'],
                'numberLikes': len(comment['peopleLike']),
                'isLiked': is_liked,
                'creatorId': id_name_avatar['id'],
                'creatorName': id_name_avatar['name'],
                'creatorAvatar': id_name_avatar['avatar'],
                'createdTime': services.get_local_string_date_time(comment['createdTime']),
                'listCommentsReply': list_replies,
            })

        return Response(res, status=status.HTTP_200_OK)


class AddComment(GenericAPIView):
    permission_classes = [IsAuthenticated, ]

    def comment_replied(self, data):
        try:
            return data['commentReplied']
        except KeyError:
            return ''

    def get_name_avatar(self, your_id):
        profile = Profile.objects.get(user=your_id)
        information = Information.objects.get(user=your_id)

        return {
            'name': profile.anonymous_name,
            'avatar': services.choose_private_avatar(information.gender)
        }

    def post(self, request, bubble_id):
        my_id = services.get_user_id_from_request(request)

        new_comment = {
            'id': str(ObjectId()),
            'content': request.data['content'],
            'creatorId': my_id,
            'createdTime': str(services.get_datetime_now()),
            'peopleLike': []
        }

        comment_replied_id = self.comment_replied(request.data)
        name_avatar = self.get_name_avatar(my_id)

        if comment_replied_id:
            mongoDb.profilePost.find_one_and_update(
                {
                    '_id': ObjectId(bubble_id),
                    'listComments.id': comment_replied_id,
                },
                {
                    '$addToSet': {
                        'listUsersComment': my_id
                    },
                    '$push': {
                        'listComments.$.listCommentsReply': new_comment
                    },
                    '$inc': {
                        'totalComments': 1,
                    }
                }
            )
            new_comment = {
                'id': new_comment['id'],
                'content': new_comment['content'],
                'numberLikes': 0,
                'isLiked': False,
                'creatorId': new_comment['creatorId'],
                'creatorName': name_avatar['name'],
                'creatorAvatar': name_avatar['avatar'],
                'createdTime': services.get_local_string_date_time(new_comment['createdTime']),
                'replyOf': comment_replied_id,
            }

        else:
            new_comment = {
                **new_comment,
                'listCommentsReply': []
            }
            mongoDb.profilePost.find_one_and_update(
                {
                    '_id': ObjectId(bubble_id)
                },
                {
                    '$addToSet': {
                        'listUsersComment': my_id
                    },
                    '$push': {
                        'listComments': new_comment
                    },
                    '$inc': {
                        'totalComments': 1
                    }
                }
            )

            new_comment = {
                'id': new_comment['id'],
                'content': new_comment['content'],
                'numberLikes': 0,
                'isLiked': False,
                'creatorId': new_comment['creatorId'],
                'creatorName': name_avatar['name'],
                'creatorAvatar': name_avatar['avatar'],
                'createdTime': services.get_local_string_date_time(new_comment['createdTime']),
                'listCommentsReply': new_comment['listCommentsReply'],
            }

        return Response(new_comment, status=status.HTTP_200_OK)
