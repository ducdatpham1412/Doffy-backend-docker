from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from authentication import models
from utilities.services import get_user_id_from_request, get_object, get_utc_now
from utilities.enums import status_active, request_user_upgrade_to_shop, account_shop
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from utilities.exception.exception_handler import CustomError, error_message, error_key
from django.db.models import Q
from datetime import timedelta
from utilities.validate import is_phone_valid


class UpgradeAccount(GenericAPIView):
    permission_classes = [IsAuthenticated, ]

    def get_user(self, user_id, phone):
        try:
            models.User.objects.get(
                ~Q(id=user_id), phone=phone, is_active=status_active)
            raise CustomError(error_message.phone_existed,
                              error_key.phone_existed)
        except models.User.DoesNotExist:
            try:
                user = models.User.objects.get(
                    id=user_id, is_active=status_active)
                return user
            except models.User.DoesNotExist:
                raise CustomError(error_message.username_not_exist,
                                  error_key.username_not_exist)

    def check_requested(self, user_id):
        try:
            # Not need to add status, because if status = 0 -> Admin had accept to upgrade to shop account
            models.User_Request.objects.get(
                creator=user_id, type=request_user_upgrade_to_shop)
            raise CustomError(error_message.had_requested_upgrade,
                              error_key.had_requested_upgrade)
        except models.User_Request.DoesNotExist:
            pass

    def put(self, request):
        my_id = get_user_id_from_request(request)
        request_data = request.data
        location = get_object(request_data, 'location')
        phone = get_object(request_data, 'phone')
        bank_code = get_object(request_data, 'bankCode')
        bank_account = get_object(request_data, 'bankAccount')

        self.check_requested(user_id=my_id)

        if not location or not phone or not bank_code or not bank_account:
            raise CustomError()
        if not is_phone_valid(phone):
            raise CustomError()

        user = self.get_user(user_id=my_id, phone=phone)
        if user.account_type == account_shop:
            raise CustomError()

        now = get_utc_now()
        expired = now + timedelta(days=20)
        data = {
            'location': location,
            'phone': phone,
            'bank_code': bank_code,
            'bank_account': bank_account,
        }

        request_user = models.User_Request(
            creator=user, type=request_user_upgrade_to_shop, created=now, expired=expired, data=str(data))
        request_user.save()

        return Response(None, status=status.HTTP_200_OK)
