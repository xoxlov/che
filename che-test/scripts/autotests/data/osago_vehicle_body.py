# -*- coding: utf-8; -*-
from collections import namedtuple
import random
import string
from common.string import russian_chars
from common.string import replace_random_char_in_string
from common.randomize import get_random_string


VehicleBody = namedtuple("VehicleBody", ["value", "valid"])
BODYNUM_MAX_SIZE = 30
valid_chars = ''.join([
    string.ascii_uppercase,
    string.digits,
    russian_chars.upper(),
])


def make_vehicle_body_number(size=None, chars=valid_chars):
    if not size:
        size = 1 + random.randint(1, BODYNUM_MAX_SIZE)
    return get_random_string(size=size, chars=chars)


testdata = [
    # Корректное значение, 17 символов латиницы и цифры
    VehicleBody(
        value=make_vehicle_body_number(),
        valid=True),
    # Значение только из букв латиницы
    VehicleBody(
        value=make_vehicle_body_number(chars=string.ascii_uppercase),
        valid=True),
    # Значение только из букв кириллицы
    VehicleBody(
        value=make_vehicle_body_number(chars=russian_chars.upper()),
        valid=True),
    # Значение только из цифр
    VehicleBody(
        value=make_vehicle_body_number(chars=string.digits),
        valid=True),
    # Значение из одного символа
    VehicleBody(
        value=make_vehicle_body_number(size=1, chars=string.ascii_uppercase),
        valid=True),
    # Значение со спецсимволами или знаками препинания
    VehicleBody(
        value=replace_random_char_in_string(
            make_vehicle_body_number(),
            lambda x: random.choice(string.punctuation)),
        valid=False),
    # Значение длиной в максимальное количество символов
    VehicleBody(
        value=make_vehicle_body_number(size=BODYNUM_MAX_SIZE),
        valid=True),
    # Значение длиной в максимальное количество символов плюс 1
    VehicleBody(
        value=make_vehicle_body_number(size=BODYNUM_MAX_SIZE + 1),
        valid=False),
    # Сверхдлинное значение
    VehicleBody(
        value=make_vehicle_body_number(size=random.randint(2 * BODYNUM_MAX_SIZE, 1024)),
        valid=False),
]
