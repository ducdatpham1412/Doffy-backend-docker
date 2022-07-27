from datetime import datetime, timedelta
from utilities import enums, services


def ADD_USER_REQUEST(user_id: int, type: int):
    now = datetime.now()
    created = services.format_datetime(now)
    expired = services.format_datetime(now + timedelta(days=20))
    query = "INSERT INTO doffy.authentication_user_request VALUES (DEFAULT, {}, {}, STR_TO_DATE('{}', '%Y-%m-%d %H:%i:%s'), STR_TO_DATE('{}', '%Y-%m-%d %H:%i:%s'), {})".format(
        user_id, type, created, expired, enums.status_active)
    return query


def CHECK_USER_IS_REQUEST_OR_LOCK_ACCOUNT(user_id: int):
    query = "SELECT * FROM doffy.authentication_user_request\
        WHERE creator_id={}\
        AND (type={} OR type={}) AND status={}"\
        .format(
        user_id, enums.request_user_lock_account, enums.request_user_delete_account, enums.status_active)
    return query


def UN_ACTIVE_REQUEST_USER(user_id):
    query = 'UPDATE doffy.authentication_user_request\
        SET status={}\
        WHERE creator_id={} AND status={}'.format(enums.status_not_active, user_id, enums.status_active)
    return query


# def CHECK_USER_IS_REQUESTING_DELETE(user_id: int):
#     query = "SELECT * FROM doffy.authentication_user_request WHERE user_id={} AND type={} AND status={}".format(
#         user_id, enums.request_user_delete_account, enums.status_active)
#     return query


# def CHECK_USER_IS_BLOCKING_ACCOUNT(user_id: int):
#     query = "SELECT * FROM doffy.authentication_user_request WHERE user_id={} AND type={} AND status={}".format(
#         user_id, enums.request_user_lock_account, enums.status_active)
#     return query
