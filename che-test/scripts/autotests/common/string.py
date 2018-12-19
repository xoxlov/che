# -*- coding: utf-8; -*-
from random import randint, choice
from string import ascii_letters
from common.randomize import get_random_string


russian_chars = "абвгдеёжзийклмнопрстуфхцчшщъыьэюя"


def replace_random_char_in_string(src, func):
    dst = src[:]
    while True:
        pos = randint(0, len(dst))
        dst = dst.replace(dst[pos], func(dst[pos]), 1)
        if dst != src:
            return dst


def replace_digit_with_letter(date):
    while True:
        index = randint(0, 9)
        if date[index].isdigit():
            return ''.join([date[:index], choice(ascii_letters), date[index+1:]])


def make_full_name_rus():
    return ' '.join(make_valid_name_rus() for _ in range(3))


def make_valid_name_rus(size=0):
    size = size or randint(2, 10)
    name = ''.join(get_random_string(size, russian_chars))
    return name.title()


def make_capital_letter():
    return choice(russian_chars).upper()
