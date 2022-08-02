
from authentication.models import User
from common.serializers import GetPassportSerializer
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from utilities import services


class GetListUserInfo(GenericAPIView):
    permission_classed = [IsAuthenticated, ]

    def post(self, request):
        list_user_id = request.data['listUserId']
        display_avatar = request.data['displayAvatar']

        result = []

        for user_id in list_user_id:
            user = User.objects.get(id=user_id)
            passport = GetPassportSerializer(user).data

            avatar = passport['profile']['avatar'] if display_avatar else services.choose_private_avatar(
                passport['information']['gender'])

            temp = {
                'id': user_id,
                'avatar': avatar,
                'name': passport['profile']['name'],
                'gender': passport['information']['gender']
            }

            result.append(temp)

        return Response(result, status=status.HTTP_200_OK)
