from findme.mongo import mongoDb
from myprofile import models
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from utilities import enums, services
from utilities.exception.exception_handler import CustomError
import pymongo
from utilities.renderers import PagingRenderer


class GetListPostReviewUser(GenericAPIView):
    permission_classes = [IsAuthenticated]
    renderer_classes = [PagingRenderer]

    def get_creator_name_avatar(self, user_id):
        try:
            profile = models.Profile.objects.get(user=user_id)
            return {
                'name': profile.name,
                'avatar': services.create_link_image(profile.avatar) if profile.avatar else ''
            }
        except models.Profile.DoesNotExist:
            raise CustomError()

    def get_profile(self, user_id: int):
        try:
            profile = models.Profile.objects.get(user=user_id)
            return {
                'id': user_id,
                'name': profile.name,
                'avatar': services.create_link_image(profile.avatar) if profile.avatar else '',
                'location': profile.location,
                'description': profile.description,
            }
        except models.Profile.DoesNotExist:
            return services.fake_user_profile

    def get(self, request, user_id):
        my_id = services.get_user_id_from_request(request)
        take = int(request.query_params['take'])
        page_index = int(request.query_params['pageIndex'])

        list_posts = mongoDb.discovery_post.find({
            'post_type': enums.post_review,
            'user_id': user_id,
            'creator': {
                '$ne': user_id,
            },
            'status': enums.status_active,
        }).sort([('created', pymongo.DESCENDING)]).limit(take).skip((page_index-1)*take)

        total_posts = mongoDb.discovery_post.count({
            'post_type': enums.post_review,
            'user_id': user_id,
            'creator': {
                '$ne': user_id,
            },
            'status': enums.status_active,
        })

        list_posts_review = []
        for post in list_posts:
            link_images = []
            for image in post['images']:
                link_images.append(services.create_link_image(image))

            info_creator = self.get_creator_name_avatar(
                user_id=post['creator'])

            check_liked = mongoDb.reaction.find_one({
                'type': enums.react_post,
                'reacted_id': str(post['_id']),
                'creator': my_id,
                'status': enums.status_active
            })
            is_liked = bool(check_liked)

            relationship = enums.relationship_self if post[
                'creator'] == my_id else enums.relationship_not_know

            check_saved = mongoDb.save.find_one({
                'type': enums.save_post,
                'saved_id': str(post['_id']),
                'creator': my_id,
                'status': enums.status_active,
            })
            is_saved = bool(check_saved)

            user_reviewed = None
            user_id = services.get_object(post, 'user_id')
            if user_id:
                profile = self.get_profile(user_id)
                user_reviewed = {
                    'id': user_id,
                    'name': profile['name'],
                    'avatar': profile['avatar'],
                    'description': profile['description'],
                    'location': profile['location']
                }

            temp = {
                'id': str(post['_id']),
                'postType': enums.post_review,
                'topic': post['topic'],
                'feeling': post['feeling'],
                'location': post['location'],
                'content': post['content'],
                'images': link_images,
                'stars': post['stars'],
                'link': post['link'],
                'userReviewed': user_reviewed,
                'totalLikes': post['total_reacts'],
                'totalComments': post['total_comments'],
                'totalSaved': post['total_saved'],
                'creator': post['creator'],
                'creatorName': info_creator['name'],
                'creatorAvatar': info_creator['avatar'],
                'created': str(post['created']),
                'isLiked': is_liked,
                'isSaved': is_saved,
                'isDraft': post['status'] == enums.status_draft,
                'isArchived': False,
                'relationship': relationship,
            }

            list_posts_review.append(temp)

        res = {
            'take': take,
            'pageIndex': page_index,
            'totalItems': total_posts,
            'data': list_posts_review
        }

        return Response(res, status=status.HTTP_200_OK)
