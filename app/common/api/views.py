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


class GetPassport(GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get_my_bubbles(self, passport):
        def get_private_avatar():
            if passport['setting']['display_avatar']:
                return passport['profile']['avatar']
            else:
                if passport['information']['gender'] == enums.gender_male:
                    return services.create_link_image(enums.PRIVATE_AVATAR['boy'])
                if passport['information']['gender'] == enums.gender_female:
                    return services.create_link_image(enums.PRIVATE_AVATAR['girl'])
                if passport['information']['gender'] == enums.gender_not_to_say:
                    return services.create_link_image(enums.PRIVATE_AVATAR['lgbt'])

            return ''

        def get_hobby(id_hobby):
            try:
                query = models.Hobby.objects.get(id=id_hobby)
                hobby = serializers.HobbySerializer(query).data
                return hobby
            except models.Hobby.DoesNotExist:
                raise CustomError()

        # # # #
        try:
            my_bubbles = models.MyBubbles.objects.get(
                user=passport['profile']['id'])
            res = []

            # private avatar
            private_avatar = get_private_avatar()

            # get hobby
            bubblesData = serializers.MyBubblesSerializer(my_bubbles).data
            for index, value in enumerate(bubblesData['listHobbies']):
                hobby = get_hobby(value)
                res.append({
                    'idHobby': hobby['id'],
                    'name': hobby['name'],
                    'icon': hobby['icon'],
                    'description': bubblesData['listDescriptions'][index],
                    'privateAvatar': private_avatar
                })
            return res

        except models.MyBubbles.DoesNotExist:
            return []

    def get(self, request):
        id = services.get_user_id_from_request(request)
        user = User.objects.get(id=id)
        passport = serializers.GetPassportSerializer(user).data

        res = {
            **passport,
            'listBubbles': self.get_my_bubbles(passport)
        }

        return Response(res, status=status.HTTP_200_OK)


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

    def get_image_background_and_gradient(self):
        mongo_resource = mongoDb.resource.find()

        image_background = mongo_resource[0]['imageBackground']
        gradient = mongo_resource[1]['gradient']

        return {
            'imageBackground': image_background,
            'gradient': gradient
        }

    def get(self, request):
        res = {
            'listHobbies': self.get_list_hobbies(),
            **self.get_image_background_and_gradient()
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
