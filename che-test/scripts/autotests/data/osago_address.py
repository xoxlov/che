# -*- coding: utf-8; -*-
import random
import string
import re
from common.string import russian_chars
from model.address import Address
from common.string import replace_random_char_in_string
from common.randomize import get_random_string


MIN_SIZE = 10
DEFAULT_SIZE = 100


def make_random_address(size=DEFAULT_SIZE, chars=None):
    size = MIN_SIZE if MIN_SIZE > size else size - MIN_SIZE
    if not chars:
        chars = russian_chars + string.digits + string.punctuation + " "
    return get_random_string(size=random.randint(MIN_SIZE, size), chars=chars)


testdata = [
    # Корректное значение
    Address(
        address="Москва, Плавский проезд, д.2, кв.52",
        valid=True),
    # Значение с латинским символом
    Address(
        address=replace_random_char_in_string(
            make_random_address(),
            lambda x: random.choice(string.ascii_letters) if str.isalpha(x) else x),
        valid=True),
    # Все кириллические символы строчные
    Address(
        address=make_random_address().upper(),
        valid=True),
    # Все кириллические символы прописные
    Address(
        address=make_random_address().lower(),
        valid=True),
    # Значение со спецсимволами
    Address(
        address=replace_random_char_in_string(
            make_random_address(),
            lambda x: random.choice(string.punctuation) if str.isalpha(x) else x),
        valid=True),
    # Значение без цифр
    Address(
        address=re.sub(r"[0-9]", "", make_random_address()),
        valid=True),
    # Значение без пробелов и знаков препинания
    Address(
        address=re.sub(r"[" + string.whitespace + "]", "", make_random_address()),
        valid=True),
    # Короткое значение
    Address(
        address=random.choice(russian_chars),
        valid=True),
    # Сверхдлинное значение
    Address(
        address=make_random_address(size=1024),
        valid=True),
    # Строка только из спецсимволов
    Address(
        address=make_random_address(chars=string.punctuation),
        valid=False),
    # Строка только из цифр
    Address(
        address=make_random_address(chars=string.digits),
        valid=False),
]
