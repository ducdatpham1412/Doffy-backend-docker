from utilities.services import create_link_image


USERNAME_MIN_LENGTH = 7
USERNAME_MAX_LENGTH = 20

PASSWORD_MIN_LENGTH = 7
PASSWORD_MAX_LENGTH = 150

PHONE_MIN_LENGTH = 5
PHONE_MAX_LENGTH = 15

NAME_MAX_LENGTH = 100
DESCRIPTION_MAX_LENGTH = 1001

NAME_DEFAULT = 'Name'
AVATAR_DEFAULT = '__admin_logo.png'
COVER_DEFAULT = '__admin_logo.png'

PRIVATE_AVATAR = {
    'girl': '__admin_girl.png',
    'boy': '__admin_boy.png',
    'lgbt': '__admin_lgbt.png',
}

# any value not specify
number_not_specify = -1
string_not_specify = ''


# sign up type
target_info_facebook = 0
target_info_email = 1
target_info_phone = 2


# type otp
type_otp_register = 0
type_otp_reset_password = 1
type_otp_change_info = 2
type_otp_request_open_account = 3

# gender type
gender_male = 0
gender_female = 1
gender_not_to_say = 2

# theme
theme_dark = 0
theme_light = 1

# language
language_en = 0
language_vi = 1

# display_avatar
display_avatar_yes = True
display_avatar_no = False

# profile relationship
relationship_self = 0
relationship_not_following = 1
relationship_following = 2
relationship_block = 3
relationship_friend = 4
relationship_not_know = 10


# type_chat_tag
chat_tag_new_from_bubble = 0
chat_tag_new_from_profile = 1

# type message
message_text = 0
message_image = 1
message_sticker = 2


# socket
socket_bubble = '3'
socket_delete_bubble = '3.5'
socket_chat_tag = '4'
socket_message = '5'
socket_seen_message = '6'
socket_request_public = '7'
socket_all_agree_public = '8'
socket_is_blocked = '9'
socket_un_blocked = '10'
socket_change_group_name = '11'
socket_stop_coversation = '12'
socket_open_conversation = '13'


# type follow
follow_follower = 0
follow_following = 1


# chat color - follow id hobby in resource
color_talking = 1
color_movie = 2
color_technology = 3
color_gaming = 4
color_animal = 5
color_travel = 6
color_fashion = 7
color_other = 8


# disable object
disable_user = 'user'
disable_follow = 'follow'
disable_profile_post = 'profilePost'
disable_message = 'message'
disable_request_delete_account = 'requestDeleteAccount'
