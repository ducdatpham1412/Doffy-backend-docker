from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from findme.mongo import mongoDb
from myprofile.models import Profile


class Check(GenericAPIView):
    def get(self, request):
        return Response(None, status=200)

    def post(self, request):
        list_group_bookings = mongoDb.discovery_post.find({
            'post_type': 1
        })
        list_group_bookings = list(list_group_bookings)

        for post in list_group_bookings:
            profile = Profile.objects.get(user=post['creator'])
            mongoDb.discovery_post.find_one_and_update(
                {
                    '_id': post['_id'],
                },
                {
                    '$set': {
                        'location': profile.location
                    }
                }
            )

        return Response('Hello', status=200)
