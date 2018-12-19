# -*- coding: utf-8; -*-
from collections import namedtuple
import random
import string
from common.string import russian_chars
from common.string import replace_random_char_in_string
from common.randomize import get_random_string


VehicleVin = namedtuple("VehicleVin", ["value", "valid"])
VIN_SIZE = 17
invalid_letters = "IOQ"
valid_letters = ''.join(sorted(set(string.ascii_uppercase) - set(invalid_letters)))


def make_vehicle_vin(size=VIN_SIZE, chars=valid_letters + string.digits):
    return get_random_string(size=size, chars=chars)


testdata = [
    # Корректное значение, 17 символов латиницы и цифры
    VehicleVin(
        value=make_vehicle_vin(),
        valid=True),
    # Строчные символы латиницы
    VehicleVin(
        value=make_vehicle_vin().lower(),
        valid=True),
    # Значение только из букв латиницы
    VehicleVin(
        value=make_vehicle_vin(chars=valid_letters),
        valid=False),
    # Значение только из цифр
    VehicleVin(
        value=make_vehicle_vin(chars=string.digits),
        valid=False),
    # Кириллица в строке
    VehicleVin(
        value=replace_random_char_in_string(
            make_vehicle_vin(),
            lambda x: random.choice(russian_chars)),
        valid=False),
    # Недопустимые символы латиницы в строке (I, O, Q)
    VehicleVin(
        value=replace_random_char_in_string(
            make_vehicle_vin(),
            lambda x: random.choice(invalid_letters)),
        valid=False),
    # Значение со спецсимволами или знаками препинания
    VehicleVin(
        value=replace_random_char_in_string(
            make_vehicle_vin(),
            lambda x: random.choice(string.punctuation)),
        valid=False),
    # Короткая строка
    VehicleVin(
        value=make_vehicle_vin(size=random.randint(1, VIN_SIZE - 1)),
        valid=False),
    # Строка длиной на один символ больше
    VehicleVin(
        value=make_vehicle_vin(size=VIN_SIZE + 1),
        valid=False),
    # Очень длинная строка
    VehicleVin(
        value=make_vehicle_vin(size=random.randint(2 * VIN_SIZE, 1024)),
        valid=False),
]
