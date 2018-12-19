# -*- coding: utf-8; -*-
import random
import string
from model.driver_license import valid_letters, translit
from model.driver_license import DriverLicense
from common.string import replace_random_char_in_string


SERIEZ_SIZE = 4
NUMBER_SIZE = 6


def get_random_lic_seriez(size=SERIEZ_SIZE, chars=None):
    MASK_DIGITS = 2
    MASK_CHARS = 2
    MASK_MORE_DIGITS = size - MASK_DIGITS - MASK_CHARS
    if chars:
        lic_series = ''.join(random.choice(chars) for _ in range(size))
    else:
        lic_series = ''.join([
            ''.join(random.choice(string.digits) for _ in range(MASK_DIGITS)),
            ''.join(random.choice(valid_letters) for _ in range(MASK_CHARS)),
            ''.join(random.choice(string.digits) for _ in range(MASK_MORE_DIGITS)),
        ])
    return lic_series


def get_random_lic_number(size=NUMBER_SIZE, chars=string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


testdata = [
    # Номер верного формата
    DriverLicense(
        seriez=get_random_lic_seriez(),
        number=get_random_lic_number(),
        valid=True),
    # Значение введённое не по маске
    DriverLicense(
        seriez=get_random_lic_seriez(size=NUMBER_SIZE),
        number=get_random_lic_number(size=SERIEZ_SIZE),
        valid=True),
    # Значение только из букв кириллицы
    DriverLicense(
        seriez=get_random_lic_seriez(chars=valid_letters),
        number=get_random_lic_number(chars=valid_letters),
        valid=False),
    # Значение только из цифр
    DriverLicense(
        seriez=get_random_lic_seriez(chars=string.digits),
        number=get_random_lic_number(),
        valid=False),
    # Короткое значение
    DriverLicense(
        seriez=get_random_lic_seriez(),
        number=get_random_lic_number(size=random.randint(1, NUMBER_SIZE - 1)),
        valid=False),
    # Длинное значение
    DriverLicense(
        seriez=get_random_lic_seriez(),
        number=get_random_lic_number(size=NUMBER_SIZE + 1),
        valid=False),
    # Значение с латинскими буквами
    DriverLicense(
        seriez=replace_random_char_in_string(
            get_random_lic_seriez(),
            lambda x: translit[x] if str.isalpha(x) else x),
        number=get_random_lic_number(),
        valid=False),
    DriverLicense(
        seriez=get_random_lic_seriez(),
        number=replace_random_char_in_string(
            get_random_lic_number(),
            lambda x: random.choice(string.ascii_letters) if str.isdigit(x) else x),
        valid=False),
    # Значение со строчными кириллическими буквами
    DriverLicense(
        seriez=replace_random_char_in_string(
            get_random_lic_seriez(),
            lambda x: x.lower() if str.isalpha(x) else x),
        number=get_random_lic_number(),
        valid=False),
    # Значение с дополнительными знаками
    DriverLicense(
        seriez=replace_random_char_in_string(
            get_random_lic_seriez(),
            lambda x: random.choice(string.punctuation) if str.isalnum(x) else x),
        number=get_random_lic_number(),
        valid=False),
    DriverLicense(
        seriez=get_random_lic_seriez(),
        number=replace_random_char_in_string(
            get_random_lic_number(),
            lambda x: random.choice(string.punctuation) if str.isalnum(x) else x),
        valid=False),
    # Значение только с нулями в качестве цифр
    DriverLicense(
        seriez="0" * SERIEZ_SIZE,
        number="0" * NUMBER_SIZE,
        valid=False),
    # Отрицательное значение номера
    DriverLicense(
        seriez=get_random_lic_seriez(),
        number="-" + get_random_lic_number(),
        valid=False),
    # Сверхдлинное значение
    DriverLicense(
        seriez=get_random_lic_seriez(),
        number=get_random_lic_number(size=random.randint(2 * NUMBER_SIZE, 1024)),
        valid=False),
]
