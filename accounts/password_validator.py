from django.core.exceptions import ValidationError

import json
import re

from django_password_history.models import UserPasswordHistory

with open("accounts/config/pass.json") as file:
    val_helper = json.load(file)


class CustomPasswordValidator():
    def validate(self, password, user=None):
        password_validator(password, user)

    def get_help_text(self):
        return ""


def password_validator(password, user):
        if len(password) < val_helper['len']:
            raise ValidationError(f"password must contain at least {val_helper['len']} characters", code='invalid')
        if not all(re.search(i, password) for i in val_helper["must_include"]):
            raise ValidationError(f"password must include: {make_prettier_condition('must_include')} [Must include one from each category]", code='invalid')
        if password in val_helper["dict_pass"]:
            raise ValidationError("common passwords are not allowed", code='invalid')

        user_history = UserPasswordHistory.objects.filter(user=user).last()
        if user_history:
            if user_history.password_is_used(password):
                raise ValidationError("You have used this password at the past.", code='invalid')


def make_prettier_condition(conditions):
    tmp_str = ""
    for condition in val_helper[conditions]:
        tmp_str = tmp_str + f"{condition}  ,"
    return replace_char(tmp_str)


def replace_char(string_value: str):
    string_value = string_value.replace('[', ' ')
    string_value = string_value.replace(']', ' ')
    string_value = string_value[:-1]
    return string_value


