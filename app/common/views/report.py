from findme.mongo import mongoDb
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from utilities import services


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
