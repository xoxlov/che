# -*- coding: utf-8; -*-
from datetime import datetime
from collections import namedtuple


Date = namedtuple("Date", ["value", "valid"])


def format(date):
    assert isinstance(date, datetime)
    return date.strftime("%d.%m.%Y")
