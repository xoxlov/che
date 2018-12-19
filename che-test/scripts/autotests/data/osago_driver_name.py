# -*- coding: utf-8; -*-
from collections import namedtuple
import random
from string import ascii_letters, digits, punctuation
from common.string import replace_random_char_in_string
from common.string import make_full_name_rus, make_valid_name_rus, make_capital_letter


DriverName = namedtuple("DriverName", ["value", "valid"])


testdata = [
    # correct name
    DriverName(make_full_name_rus(), True),
    # name with initials in place of first and middle names
    DriverName(' '.join([
        make_valid_name_rus(),
        make_capital_letter(), ".",
        make_capital_letter(), "."
    ]), True),
    # name with initials only with dots
    DriverName('.'.join(make_capital_letter() for _ in range(3)) + ".", False),
    # name with initials only without dots
    DriverName(''.join([make_capital_letter() for _ in range(3)]), False),
    # name with non-cyrillic symbols
    DriverName(
        replace_random_char_in_string(
            make_full_name_rus(),
            lambda x: random.choice(ascii_letters) if str.isalpha(x) else x),
        False),
    # name with digits as separators
    DriverName(
        replace_random_char_in_string(
            make_full_name_rus(),
            lambda x: random.choice(digits) if str.isspace(x) else x),
        False),
    # name with hyphen
    DriverName(' '.join([
        make_valid_name_rus() + "-" + make_valid_name_rus(),
        make_valid_name_rus(),
        make_valid_name_rus(),
    ]), True),
    # name with digits separately
    DriverName(' '.join([
        make_valid_name_rus(),
        make_valid_name_rus(),
        make_valid_name_rus(),
        str(random.randint(1, 10))
    ]), False),
    # name with punctuations
    DriverName(
        replace_random_char_in_string(
            make_full_name_rus(),
            lambda x: random.choice(punctuation) if str.isalpha(x) else x),
        False),
    # extra long name
    DriverName(' '.join(make_valid_name_rus(100) for _ in range(3)), False),
]
