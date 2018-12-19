# -*- coding: utf-8; -*-
import random
import string
from model.passport import Passport
from common.string import replace_random_char_in_string, russian_chars


CHARACTERS = string.ascii_letters + string.punctuation + russian_chars
SERIEZ_SIZE = 4
NUMBER_SIZE = 6


def get_random_pass_seriez(size=SERIEZ_SIZE, chars=string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


def get_random_pass_number(size=NUMBER_SIZE, chars=string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


testdata = [
    # Номер верного формата
    Passport(
        seriez=get_random_pass_seriez(),
        number=get_random_pass_number(),
        valid=True),
    # Серия содержит буквы, спецсимволы или знаки препинания
    Passport(
        seriez=replace_random_char_in_string(
            get_random_pass_seriez(),
            lambda x: random.choice(CHARACTERS) if x.isdigit() else x),
        number=get_random_pass_number(),
        valid=True),
    # Номер содержит буквы, спецсимволы или знаки препинания
    Passport(
        seriez=get_random_pass_seriez(),
        number=replace_random_char_in_string(
            get_random_pass_number(),
            lambda x: random.choice(CHARACTERS) if x.isdigit() else x),
        valid=True),
    # Дефис (случайный знак) между серией и номером
    Passport(
        seriez=get_random_pass_seriez(),
        number=get_random_pass_number(),
        sep=random.choice(string.punctuation),
        valid=True),
    # Серия только из нулей
    Passport(
        seriez="0" * SERIEZ_SIZE,
        number=get_random_pass_number(),
        valid=True),
    # Номер только из нулей
    Passport(
        seriez=get_random_pass_seriez(),
        number="0" * NUMBER_SIZE,
        valid=True),
    # Короткая строка для серии и номера
    Passport(
        seriez=get_random_pass_seriez(size=random.randint(1, SERIEZ_SIZE - 1)),
        number=get_random_pass_number(),
        valid=True),
    Passport(
        seriez=get_random_pass_seriez(),
        number=get_random_pass_number(size=random.randint(1, NUMBER_SIZE - 1)),
        valid=True),
    # Длинная строка для серии и номера
    Passport(
        seriez=get_random_pass_seriez(size=SERIEZ_SIZE + 1),
        number=get_random_pass_number(),
        valid=True),
    Passport(
        seriez=get_random_pass_seriez(),
        number=get_random_pass_number(size=NUMBER_SIZE + 1),
        valid=True),
    # Сверхдлинная строка
    Passport(
        seriez=get_random_pass_seriez(size=random.randint(2 * SERIEZ_SIZE, 1024)),
        number=get_random_pass_number(),
        valid=True),
    Passport(
        seriez=get_random_pass_seriez(),
        number=get_random_pass_number(size=random.randint(2 * NUMBER_SIZE, 1024)),
        valid=True),
    # Строка из 10 пробельных символов
    Passport(
        seriez=" " * SERIEZ_SIZE,
        number=" " * NUMBER_SIZE,
        valid=True),
]
