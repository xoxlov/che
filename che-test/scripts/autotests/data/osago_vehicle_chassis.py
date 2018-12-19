# -*- coding: utf-8; -*-
from collections import namedtuple
import random
import string
from common.string import russian_chars
from common.string import replace_random_char_in_string
from common.randomize import get_random_string


VehicleChassis = namedtuple("VehicleChassis", ["value", "valid"])
CHASSISNUM_MAX_SIZE = 30
valid_chars = ''.join([
    string.ascii_uppercase,
    string.digits,
    russian_chars.upper()
])


def make_vehicle_body_number(size=None, chars=valid_chars):
    if not size:
        size = 1 + random.randint(1, CHASSISNUM_MAX_SIZE)
    return get_random_string(size=size, chars=chars)


testdata = [
    # Корректное значение, 17 символов латиницы и цифры
    VehicleChassis(
        value=make_vehicle_body_number(),
        valid=True),
    # Значение только из букв латиницы
    VehicleChassis(
        value=make_vehicle_body_number(chars=string.ascii_uppercase),
        valid=True),
    # Значение только из букв кириллицы
    VehicleChassis(
        value=make_vehicle_body_number(chars=russian_chars.upper()),
        valid=True),
    # Значение только из цифр
    VehicleChassis(
        value=make_vehicle_body_number(chars=string.digits),
        valid=True),
    # Значение из одного символа
    VehicleChassis(
        value=make_vehicle_body_number(size=1, chars=string.ascii_uppercase),
        valid=True),
    # Значение со спецсимволами или знаками препинания
    VehicleChassis(
        value=replace_random_char_in_string(
            make_vehicle_body_number(),
            lambda x: random.choice(string.punctuation)),
        valid=False),
    # Значение длиной в максимальное количество символов
    VehicleChassis(
        value=make_vehicle_body_number(size=CHASSISNUM_MAX_SIZE),
        valid=True),
    # Значение длиной в максимальное количество символов плюс 1
    VehicleChassis(
        value=make_vehicle_body_number(size=CHASSISNUM_MAX_SIZE + 1),
        valid=False),
    # Сверхдлинное значение
    VehicleChassis(
        value=make_vehicle_body_number(size=random.randint(2 * CHASSISNUM_MAX_SIZE, 1024)),
        valid=False),
]
