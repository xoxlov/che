# -*- coding: utf-8; -*-
import string
import random


def get_random_int_from_set():
    """Return random integer number from predefined set (big numbers are byte range aligned)
    """
    return random.choice([
        0, 1, 8, 32, 33, 127, 128, 129, 255, 256,
        65535, 0xffff + 1,
        0xffffff, 0xffffff + 1,
        0xffffffff, 0xffffffff + 1,
        0xffffffffff, 0xffffffffff + 1,
        0xffffffffffff, 0xffffffffffff + 1,
        0xffffffffffffff, 0xffffffffffffff + 1,
        0xffffffffffffffff, 0xffffffffffffffff + 1
    ])


def get_random_string(size=10, chars=string.ascii_lowercase):
    """Return random string with specified size made with specified chars
    """
    return ''.join(random.choice(chars) for _ in range(size))


def get_random_spacechar_filled_string(size=None):
    """Return string containing randomly placed space_chars, optional param
    size defines result length. For list of spacechars see 'man ascii'.
    """
    size = size or random.choice([1, 2, 3, 5, 7, 10, 15, 16, 127, 254])
    return get_random_string(size=size, chars=string.whitespace)


def make_random_email(prefix="test"):
    buyer_email = "".join([
        prefix,
        "@",
        get_random_string(),
        ".",
        get_random_string(size=2),
    ])
    return buyer_email
