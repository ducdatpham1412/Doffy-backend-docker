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
from datetime import datetime
from django.conf import settings
import requests
import json
from django.conf import settings
from utilities.exception.exception_handler import CustomError
import pyheif
from dateutil import parser
import pytz
from django.db.models import Q
from setting.models import Block
from setting.serializers import BlockSerializer


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


"""
Resize image
"""


def change_to_content_jpeg(image: InMemoryUploadedFile):
    if image.content_type == 'image/heic':
        img_io = io.BytesIO()
        heif_file = pyheif.read(image)
        img = Image.frombytes(
            heif_file.mode,
            heif_file.size,
            heif_file.data,
            "raw",
            heif_file.mode,
            heif_file.stride,
        )
        img.save(img_io, format='JPEG')
        temp = InMemoryUploadedFile(
            file=img_io,
            field_name='ImageField',
            name=image.name,
            content_type='image/jpeg',
            size=sys.getsizeof(img_io),
            charset=image.charset,
            content_type_extra=image.content_type_extra,
        )
        return temp

    return image


def handle_resize_image(image: InMemoryUploadedFile, new_width=150):
    img_io = io.BytesIO()

    image_changed = change_to_content_jpeg(image)

    img = Image.open(image_changed)
    img = ImageOps.exif_transpose(img)

    # If image's size is smaller than standard, not need to thumbnail
    if (img.width < new_width):
        return image

    # if image is not jpeg (png,...), convert it jpg
    if (img.mode != 'RGB'):
        img = img.convert('RGB')

    # Else thumbnail it
    percent = img.height / img.width
    new_height = int(percent * new_width)
    img.thumbnail((new_width, new_height), Image.ANTIALIAS)
    # can pass quality= to here to compress image
    img.save(img_io, format='JPEG',)

    new_pic = InMemoryUploadedFile(
        file=img_io,
        field_name='ImageField',
        name=image_changed.name,
        content_type='image/jpeg',
        size=sys.getsizeof(img_io),
        charset=image_changed.charset,
        content_type_extra=image_changed.content_type_extra,
    )

    return new_pic


"""
Resize image
"""


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


def get_local_string_date_time(utc_time: any):
    # print('time zone info: ', datetime.now().astimezone().tzinfo)
    parsed_date = parser.parse(str(utc_time))
    parsed_date_vn = parsed_date.astimezone(pytz.timezone('Asia/Ho_Chi_Minh'))
    return datetime.strftime(parsed_date_vn, '%Y-%m-%d %H:%M:%S')


def format_datetime(time: datetime):
    temp = datetime.strftime(time, '%Y-%m-%d %H:%M:%S')
    return datetime.strptime(temp, '%Y-%m-%d %H:%M:%S')


def format_utc_time(time: str):  # time have to be UTC format
    return parser.parse(time)


# Notification follow user
headers = {
    "Content-Type": "application/json; charset=utf-8",
    "Authorization": "Basic {}".format(settings.ONESIGNAL_API_KEY)
}


def send_notification(body: object):
    try:
        requests.post("https://onesignal.com/api/v1/notifications", headers=headers, data=json.dumps({
            "app_id": settings.ONESIGNAL_APP_ID,
            **body
        }))
    except Exception as e:
        print('Err send notification: ', e)


data_anonymous_name = ['Rồng', 'Sói', 'Ngựa', 'Cáchép', 'Hổ', 'SưTử',
                       'Cáo', 'Báo', 'Chồn', 'TêTê', 'Gà', 'ĐạiBàng', 'Mèo', 'Khỉ', ]


def init_name_profile():
    return '{}{}'.format(random.choice(data_anonymous_name), 'ẩndanh')


def check_had_i_know(list_user_id: list, partner_id: int):
    for user_id in list_user_id:
        if user_id == partner_id:
            return True
    return False


def check_include(list: list, value: any) -> bool:
    for _value in list:
        if _value == value:
            return True
    return False


def google_validate_id_token(id_token: str) -> bool:
    response = requests.get(
        enums.GOOGLE_ID_TOKEN_INFO_URL,
        params={'id_token': id_token}
    )

    if not response.ok:
        raise CustomError()

    return response.json()


def get_index(list: list, index: int, default=None):
    try:
        return list[index]
    except IndexError:
        return default


def get_object(object: dict, key: str, default=None):
    try:
        return object[key]
    except KeyError or TypeError:
        return default


def get_list_user_block(user_id: int) -> list:
    try:
        query = Block.objects.filter(
            Q(block=user_id) | Q(blocked=user_id))
        list_blocks = BlockSerializer(query, many=True).data
        temp = []
        for block in list_blocks:
            if (block['block'] != user_id):
                temp.append(block['block'])
            else:
                temp.append(block['blocked'])
        return temp
    except Block.DoesNotExist:
        return []


fake_user_profile = {
    'id': None,
    'name': '',
    'avatar': '',
    'location': '',
    'description': ''
}
