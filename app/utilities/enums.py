

USERNAME_MIN_LENGTH = 7
USERNAME_MAX_LENGTH = 20

PASSWORD_MIN_LENGTH = 7
PASSWORD_MAX_LENGTH = 150

PHONE_MIN_LENGTH = 5
PHONE_MAX_LENGTH = 15

NAME_MAX_LENGTH = 100
DESCRIPTION_MAX_LENGTH = 1002

NAME_DEFAULT = 'Name'
AVATAR_DEFAULT = '__admin_logo.png'
COVER_DEFAULT = '__admin_logo.png'

PRIVATE_AVATAR = {
    'girl': '__admin_girl.png',
    'boy': '__admin_boy.png',
    'lgbt': '__admin_lgbt.png',
}

GOOGLE_ID_TOKEN_INFO_URL = 'https://www.googleapis.com/oauth2/v3/tokeninfo'

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
relationship_not_know = 10


# group palace relationship
group_relationship_self = 0
group_relationship_joined = 1
group_relationship_not_joined = 2

# type message
message_text = 0
message_image = 1
message_sticker = 2
message_join_community = 3
message_change_color = 4
message_change_name = 5


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
disable_profile_post = 'profilePost'

# notification
notification_message = 0
notification_comment = 1
notification_follow = 2
notification_like_post = 3
notification_friend_post_new = 4
notification_like_gb = 5
notification_comment_gb = 6


# social sign in
sign_in_apple = 'apple'
sign_in_facebook = 'facebook'
sign_in_google = 'google-oauth2'

# os
os_android = 0
os_iOS = 1

# status
status_not_active = 0
status_active = 1
status_draft = 2
status_temporarily_closed = 3
status_requesting_delete = 4

status_conversation_stop = 0
status_conversation_active = 1

status_notification_delete = 0
status_notification_not_read = 1
status_notification_read = 2

status_joined_deleted = 0
status_not_joined = 1
# joined but merchant not confirm went or not to confirm time
status_joined_not_bought = 2
# joined and merchant confirmed went or over the confirm time
status_joined_bought = 3

# request_user
request_user_lock_account = 0
request_user_delete_account = 1
request_user_upgrade_to_shop = 2
request_update_price = 3
request_delete_gb = 4

# topic discovery post
topic_travel = 0
topic_cuisine = 1
topic_shopping = 2

# reaction
react_post = 0
react_comment = 1
react_message = 2

# save
save_post = 0

# total_items
total_discovery_post = 0
total_message = 1
total_reputation = 2

# type account
account_user = 0
account_shop = 1
account_admin = 2

# discovery post type
post_review = 0
post_group_buying = 1
