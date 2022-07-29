def SEARCH_USERNAME(username: str):
    return "SELECT * FROM doffy.authentication_user WHERE email='{}' OR phone='{}' AND is_active=1 LIMIT 1".format(username, username)


def UN_ACTIVE_ACCOUNT(user_id: int):
    query = 'UPDATE doffy.authentication_user\
        SET is_active=0 WHERE id={}'.format(user_id)
    return query
