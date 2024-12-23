from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from authentication import models
from rest_framework import status
from utilities import enums
from utilities.services import get_user_id_from_request
from utilities.exception.exception_handler import CustomError
from utilities.exception import error_message, error_key
from myprofile.models import Profile
from django.core.mail import send_mail
from findme.settings import EMAIL_HOST_USER
from utilities.services import str_to_dict, get_datetime_now
from findme.mongo import mongoDb
from bson.objectid import ObjectId


class ApproveRequest(GenericAPIView):
    permission_classes = [IsAuthenticated, ]

    def check_is_admin(self, user_id):
        try:
            models.User.objects.get(
                id=user_id, is_active=enums.status_active, account_type=enums.account_admin)
        except models.User.DoesNotExist:
            raise CustomError(error_message.you_are_not_admin,
                              error_key.you_are_not_admin)

    def get_request(self, request_id):
        try:
            return models.User_Request.objects.get(
                id=request_id, status=enums.status_active)
        except models.User.DoesNotExist:
            raise CustomError()

    def check_user_existed(self, phone):
        try:
            models.User.objects.get(phone=phone, is_active=enums.status_active)
        except models.User.DoesNotExist:
            pass

    def put(self, request, request_id):
        my_id = get_user_id_from_request(request)
        self.check_is_admin(user_id=my_id)
        request_user = self.get_request(request_id)

        if request_user.type == enums.request_user_upgrade_to_shop:
            data = str_to_dict(request_user.data)

            self.check_user_existed(phone=data['phone'])

            user = request_user.creator
            user.phone = data['phone']
            user.account_type = enums.account_shop
            user.bank_code = data['bank_code']
            user.bank_account = data['bank_account']
            user.save()

            profile = Profile.objects.get(user=user.id)
            profile.location = data['location']
            profile.save()

            request_user.status = enums.status_not_active
            request_user.save()

            html_string_success = "<div>\n    <h1>THƯ CHÚC MỪNG</h1>\n\n    <p><i>Thân gửi </i>{0},</p>\n    <p>\n        Chúc mừng bạn đã đăng ký tài khoản\n        <b>nhà cung cấp dịch vụ du lịch</b> thành công. Giờ đây, bạn có thể đăng\n        các chiến dịch mua chung và tiếp cận được đến nhiều khách hàng.\n    </p>\n    <p>\n        Mọi thông tin đăng nhập tài khoản vẫn giữ nguyên, ngoài ra bạn cũng có\n        thể đăng nhập qua số điện thoại mới đăng ký: <b>{1}</b>\n    </p>\n    <p>\n        Doffy xin trân trọng cảm ơn sự quan tâm của bạn. Chúc bạn sức khoẻ, hạnh\n        phúc và đạt được nhiều thành công.\n    </p>\n    <p>Thân ái, <b>Doffy!</b></p>\n    <br />\n    <!-- <div\n        style=\"\n            background-image: linear-gradient(#54b3e9, #31ede2);\n            text-align: center;\n            padding-top: 5px;\n            padding-bottom: 5px;\n            border-radius: 10px;\n        \"\n        onclick=\"onOpenLink()\"\n    >\n        <p style=\"color: white\">Đi tới tạo chiến dịch mua chung</p>\n    </div> -->\n    <!-- <br /> -->\n    <p>\n        Mọi thắc mắc và yêu cầu giúp đỡ bạn vui lòng liên hệ qua:<br /><b\n            >Email &nbsp;&nbsp;: </b\n        >doffy.app@gmail.com<br /><b>Hotline : </b>(+84)886141200\n    </p>\n</div>\n".format(
                profile.name, '**{}'.format(data['phone'][-3:]))

            send_mail(subject='Đăng ký tài khoản người bán tour',
                      recipient_list=[user.email],
                      from_email=EMAIL_HOST_USER,
                      fail_silently=False,
                      html_message=html_string_success,
                      message="Notification")

        if request_user.type == enums.request_delete_gb:
            data = str_to_dict(request_user.data)
            post = mongoDb.discovery_post.find_one_and_update(
                {
                    '_id': ObjectId(data['post_id']),
                    'creator': request_user.creator.id,
                    'status': enums.status_requesting_delete,
                },
                {
                    '$set': {
                        'status': enums.status_not_active,
                    }
                }
            )
            if not post:
                raise CustomError(error_message.post_not_existed,
                                  error_key.post_not_existed)

            request_user.status = enums.status_not_active
            request_user.save()

        if request_user.type == enums.request_update_price:
            data = str_to_dict(request_user.data)
            post = mongoDb.discovery_post.find_one_and_update(
                {
                    '_id': ObjectId(request_user.post_id),
                    'creator': request_user.creator.id,
                    'status': {
                        '$in': [enums.status_active, enums.status_temporarily_closed, enums.status_requesting_delete]
                    }
                },
                {
                    '$set': {
                        'retail_price': data['retail_price'],
                        'prices': data['prices'],
                        'modified': get_datetime_now()
                    }
                }
            )
            if not post:
                raise CustomError(error_message.post_not_existed,
                                  error_key.post_not_existed)

            mongoDb.discovery_edit_history.insert_one({
                'post_id': str(post['_id']),
                'retail_price': post['retail_price'],
                'prices': post['prices'],
                'created': get_datetime_now(),
            })

            request_user.status = enums.status_not_active
            request_user.save()

        return Response(None, status=status.HTTP_200_OK)
