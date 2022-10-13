from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from utilities import services
from authentication.models import User
from myprofile.models import ErrorLog


class CreateErrorLog(GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        my_id = services.get_user_id_from_request(request)
        error = request.data['error']

        user = User.objects.get(id=my_id)
        error_log = ErrorLog(user=user, error=error)
        error_log.save()

        return Response(None, status=status.HTTP_200_OK)
