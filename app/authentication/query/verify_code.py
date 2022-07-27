def SEARCH_OTP(username: str, code=0):
    if code:
        return "SELECT * FROM doffy.authentication_verifycode WHERE username='{}' AND code={} AND code!=0 LIMIT 1".format(username, code)

    return "SELECT * FROM doffy.authentication_verifycode WHERE username='{}' LIMIT 1".format(username)


def UPDATE_OTP(username: str, code: int):
    return "UPDATE doffy.authentication_verifycode SET code={} WHERE username='{}'".format(code, username)


def INSERT_OTP(username: str, code: int):
    return "INSERT INTO doffy.authentication_verifycode (username, code) VALUES ('{}', {})".format(username, code)
