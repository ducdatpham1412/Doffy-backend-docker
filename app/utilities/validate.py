from utilities import enums
import re


def validate_password(password):
    if (len(password) > enums.PASSWORD_MAX_LENGTH or len(password) < enums.PASSWORD_MIN_LENGTH):
        return False
    return True


def is_email_valid(email):
    if re.match(r'\b[\w\.-]+@[\w\.-]+\.\w{2,6}\b', email) != None:
        return True
    return False


def is_phone_valid(phone):
    if re.match(r"^[\-]?[0-9][0-9]*\.?[0-9]+$", phone) != None:
        return True
    return False
