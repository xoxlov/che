# -*- coding: utf-8; -*-
import random
import string
import re
from model.car_number import valid_letters, invalid_letters, translit
from model.car_number import valid_regions
from model.car_number import CarNumber
from common.string import replace_random_char_in_string


def get_random_car_number():
    return ''.join([
        random.choice(valid_letters),
        ''.join(random.choice(string.digits) for _ in range(3)),
        ''.join(random.choice(valid_letters) for _ in range(2)),
    ])


def get_random_valid_region(size=None):
    if size is None:
        region = random.choice(valid_regions)
    else:
        region = random.choice([r for r in valid_regions if len(r) == size])
    return region


def get_random_invalid_region(size=None):
    if not size:
        size = random.randint(1, 4)
    region = ''.join([random.choice(string.digits) for _ in range(size)])
    while region in valid_regions:
        region = ''.join([random.choice(string.digits) for _ in range(size)])
    return region


testdata = [
    # Номер верного формата с заглавными буквами и корректным номером региона
    CarNumber(number=get_random_car_number(),
              region=get_random_valid_region(),
              valid=True),
    # Номер верного формата, одна из букв строчная
    CarNumber(number=replace_random_char_in_string(get_random_car_number(), str.lower),
              region=get_random_valid_region(),
              valid=True),
    # Номер верного формата, номер региона из двух цифр
    CarNumber(number=get_random_car_number(),
              region=get_random_valid_region(size=2),
              valid=True),
    # Номер без указания собственно номера
    CarNumber(number="",
              region=get_random_valid_region(),
              valid=False),
    # Номер без указания региона
    CarNumber(number=get_random_car_number(),
              region="",
              valid=False),
    # Номер верного формата, номер региона из одной цифры
    CarNumber(number=get_random_car_number(),
              region=get_random_invalid_region(size=1),
              valid=False),
    # Номер верного формата, номер региона из четырёх цифр
    CarNumber(number=get_random_car_number(),
              region=get_random_invalid_region(size=4),
              valid=False),
    # Номер верного формата с некорректным номером региона
    CarNumber(number=get_random_car_number(),
              region=get_random_invalid_region(),
              valid=False),
    # Номер с латинской буквой вместо кириллической
    CarNumber(number=replace_random_char_in_string(
                        get_random_car_number(),
                        lambda x: translit[x] if str.isalpha(x) else x),
              region=get_random_valid_region(),
              valid=False),
    # Номер с буквой кириллицы, не имеющей аналогов в латинице
    CarNumber(number=replace_random_char_in_string(
                        get_random_car_number(),
                        lambda x: random.choice(invalid_letters) if str.isalpha(x) else x),
              region=get_random_valid_region(),
              valid=False),
    # Номер с переставленной буквой
    CarNumber(number=''.join(random.sample(get_random_car_number(), 6)),
              region=get_random_valid_region(),
              valid=False),
    # Номер с нулевыми цифрами номера
    CarNumber(number=re.sub(r"[0-9]", "0", get_random_car_number()),
              region=get_random_valid_region(),
              valid=False),
    # Номер с максимальными цифрами номера
    CarNumber(number=re.sub(r"[0-9]", "9", get_random_car_number()),
              region=get_random_valid_region(),
              valid=True),
    # Номер с недостающей буквой
    CarNumber(number=replace_random_char_in_string(get_random_car_number(),
                                                   lambda x: "" if str.isalpha(x) else x),
              region=get_random_valid_region(),
              valid=False),
    # Номер с недостающей цифрой
    CarNumber(number=re.sub(r"[0-9]", "", get_random_car_number(), 1),
              region=get_random_valid_region(),
              valid=False),
    # Номер с лишней буквой
    CarNumber(number=replace_random_char_in_string(get_random_car_number(),
                                                   lambda x: x*2 if str.isalpha(x) else x),
              region=get_random_valid_region(),
              valid=False),
    # Номер с лишней цифрой
    CarNumber(number=re.sub(r"[0-9]",
                            "".join([random.choice(string.digits) for _ in range(2)]),
                            get_random_car_number(), 1),
              region=get_random_valid_region(),
              valid=False),
    # Номер с нулями в коде региона
    CarNumber(number=get_random_car_number(),
              region="00",
              valid=False),
    # Номер со знаком препинания в номере автомобиля
    CarNumber(number=replace_random_char_in_string(get_random_car_number(),
                                                   lambda x: random.choice(string.punctuation)),
              region=get_random_valid_region(),
              valid=False),
    # Номер со знаком препинания в номере региона
    CarNumber(number=get_random_car_number(),
              region=replace_random_char_in_string(get_random_valid_region(),
                                                   lambda x: random.choice(string.punctuation)),
              valid=False),
]
