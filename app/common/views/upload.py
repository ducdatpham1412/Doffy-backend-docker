from authentication.models import User
from common import models
from common.forms import ImageForm
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from utilities import services


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
        form = ImageForm(files=request.data)
        if True:
            list_image = form.files.getlist('image')

            for image in list_image:
                time_stamp = services.get_datetime_now().timestamp()
                name = int(float(time_stamp) * 1000)
                image.name = '{0}{1}.jpeg'.format(id, name)

                resize_image = services.handle_resize_image(image, quality)
                models.Images.objects.create(image=resize_image)
                res.append(resize_image.name)

        return Response(res, status=status.HTTP_200_OK)
