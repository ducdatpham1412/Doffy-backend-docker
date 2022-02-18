import random
import string
from django.core.mail import send_mail
from findme.settings import EMAIL_HOST_USER, SIMPLE_JWT
from rest_framework_simplejwt.backends import TokenBackend
from utilities import enums
import io
from PIL import Image, ImageOps
from django.core.files.uploadedfile import InMemoryUploadedFile
import sys
from datetime import datetime, timedelta
import pytz
from django.conf import settings


def send_to_mail(mail, verify_code):
    send_mail(
        'Doffy verify code',
        'Your verify code is: {}\nPlease not share this code to anyone'.format(
            verify_code),
        EMAIL_HOST_USER,
        [mail, ],
        fail_silently=False,
    )


def get_randomCode(numberDigits=4):
    start = pow(10, numberDigits - 1)
    end = pow(10, numberDigits) - 1
    return random.randint(start, end)


def obscure_destination(destination, type='email'):
    if type == 'email':
        if not destination:
            temp = ''.join(random.sample(string.ascii_letters, 2))
            return '**{}@gmail.com'.format(temp)
        else:
            index = str(destination).find('@')
            temp = destination[index-2:len(destination)]
            return '**' + temp

    elif type == 'phone':
        if not destination:
            temp = ''.join(random.sample('0123456789', 2))
            return '**{}'.format(temp)
        else:
            last = len(destination)
            temp = destination[last-2:last]
            return '**' + last
    return ''


def get_user_id_from_request(request):
    def get_token_from_header():
        authorization = str(request.headers['authorization'])
        token = authorization.split(" ")[1]
        return token

    token = get_token_from_header()
    validate_data = TokenBackend(
        algorithm=SIMPLE_JWT['ALGORITHM']).decode(token, verify=False)
    return validate_data['user_id']


def create_socket_bubble_chattag(group_id):
    return 'bubble_chattag_{}'.format(group_id)


def create_socket_message_detail(group_id):
    return 'message_detail_{}'.format(group_id)


def handle_resize_image(image, new_width=150):
    img_io = io.BytesIO()
    img = Image.open(image)
    img = ImageOps.exif_transpose(img)

    # if image's size is smaller than standart, not need to thumbnail
    if (img.width < new_width):
        return image
    # if image is not jpeg (png,...), convert it jpg
    if (img.mode != 'RGB'):
        img = img.convert('RGB')

    # else thumbnail it
    percent = img.height / img.width
    new_height = int(percent * new_width)
    img.thumbnail((new_width, new_height), Image.ANTIALIAS)
    img.save(img_io, format='JPEG')

    new_pic = InMemoryUploadedFile(
        file=img_io,
        field_name='ImageField',
        name=image.name,
        content_type=image.content_type,
        size=sys.getsizeof(img_io),
        charset=image.charset,
        content_type_extra=image.content_type_extra,
    )

    return new_pic


def create_link_image(image_name):
    return '{}/{}'.format(settings.AWS_IMAGE_URL, image_name)


def choose_private_avatar(gender: int):
    if (gender == enums.gender_female):
        return create_link_image(enums.PRIVATE_AVATAR['girl'])
    if (gender == enums.gender_male):
        return create_link_image(enums.PRIVATE_AVATAR['boy'])
    if (gender == enums.gender_not_to_say):
        return create_link_image(enums.PRIVATE_AVATAR['lgbt'])
    return create_link_image(enums.PRIVATE_AVATAR['girl'])


def filter_the_same_id(list_user_ids: list):
    res = []
    for user_id in list_user_ids:
        if res.count(user_id) == 0:
            res.append(user_id)
    return res


def check_is_user_enjoy_mode(user_route: str):
    index = user_route.find('__')
    return index >= 0


def get_datetime_now():
    return datetime.now()


def get_local_string_date_time(utc_time: datetime):
    # print('time zone info: ', datetime.now().astimezone().tzinfo)
    hanoi_time = utc_time + timedelta(hours=7)
    return str(hanoi_time)
