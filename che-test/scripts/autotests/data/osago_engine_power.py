# -*- coding: utf-8; -*-
from collections import namedtuple
from random import randint, choice
from string import ascii_letters, punctuation
from common.string import replace_random_char_in_string


Engine = namedtuple("Engine", ["value", "valid"])
MIN_POWER = 1
MAX_POWER = 200
testdata = [
    # Integer number
    Engine(
        value=str(randint(MIN_POWER, MAX_POWER)),
        valid=True),
    # fractional number with dot as divider, two digits in a fractional part
    Engine(
        value=str(randint(MIN_POWER, MAX_POWER) + randint(1, 99) / 100.0).replace(",", "."),
        valid=True),
    # fractional number with comma as divider, two digits in a fractional part
    Engine(
        value=str(randint(MIN_POWER, MAX_POWER) + randint(1, 99) / 100.0).replace(".", ","),
        valid=True),
    # fractional number with comma as divider, one digits in a fractional part
    Engine(
        value=str(randint(MIN_POWER, MAX_POWER) + randint(1, 9) / 10.0).replace(".", ","),
        valid=True),
    # fractional number with comma as divider, three digits in a fractional part
    Engine(
        value=str(randint(MIN_POWER, MAX_POWER) + randint(1, 999) / 1000.0).replace(".", ","),
        valid=False),
    # fractional number with comma as divider, two zeros in a fractional part
    Engine(
        value=str(randint(MIN_POWER, MAX_POWER)) + ",00",
        valid=True),
    # fractional number with comma as divider, three zeros in a fractional part
    Engine(
        value=str(randint(MIN_POWER, MAX_POWER)) + ",000",
        valid=True),
    # Integer number with leading zero
    Engine(
        value="0" + str(randint(MIN_POWER, MAX_POWER)),
        valid=True),
    # Integer negative number
    Engine(
        value="-" + str(randint(MIN_POWER, MAX_POWER)),
        valid=False),
    # Integer positive number with explicit plus sign
    Engine(
        value="+" + str(randint(MIN_POWER, MAX_POWER)),
        valid=False),
    # number with punctuation sign
    Engine(
        value=replace_random_char_in_string(
            str(randint(MIN_POWER, MAX_POWER)),
            lambda x: choice(punctuation)),
        valid=False),
    # number with letter
    Engine(
        value=replace_random_char_in_string(
            str(randint(MIN_POWER, MAX_POWER)),
            lambda x: choice(ascii_letters)),
        valid=False),
    # arythmetic expression
    Engine(
        value=''.join([
            str(randint(MIN_POWER, MAX_POWER)),
            choice("+-*/"),
            str(randint(MIN_POWER, MAX_POWER))]),
        valid=False),
    # very large number
    Engine(
        value=str(randint(MIN_POWER * 1000000, MAX_POWER * 1000000)),
        valid=True),
]
