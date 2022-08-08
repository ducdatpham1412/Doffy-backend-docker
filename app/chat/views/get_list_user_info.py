
from authentication.models import User
from common.serializers import GetPassportSerializer
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from utilities.exception.exception_handler import CustomError
from utilities.exception import error_message, error_key


class GetListUserInfo(GenericAPIView):
    permission_classed = [IsAuthenticated, ]

    def post(self, request):
        list_user_id = request.data['listUserId']

        result = []

        for user_id in list_user_id:
            try:
                user = User.objects.get(id=user_id)
                passport = GetPassportSerializer(user).data

                temp = {
                    'id': user_id,
                    'avatar': passport['profile']['avatar'],
                    'name': passport['profile']['name'],
                    'gender': passport['information']['gender']
                }

                result.append(temp)
            except User.DoesNotExist:
                raise CustomError(error_message.username_not_exist,
                                  error_key.username_not_exist)

        return Response(result, status=status.HTTP_200_OK)
