# -*- coding: utf-8; -*-
from datetime import datetime, timedelta
from random import randint
from common.date_time import Date, format
from common.string import replace_digit_with_letter
from common.randomize import get_random_spacechar_filled_string as get_spaces


MAX_DELTA = 60  # days
valid_date = datetime.today()
testdata = [
    # today
    Date(format(valid_date), True),
    # tomorrow
    Date(format(valid_date + timedelta(days=1)), True),
    # random date within correct range
    Date(format(valid_date + timedelta(days=randint(2, MAX_DELTA))), True),
    # today + maximum delta
    Date(format(valid_date + timedelta(days=MAX_DELTA)), True),
    # today + maximum delta + 1 day
    Date(format(valid_date + timedelta(days=MAX_DELTA + 1)), False),
    # yesterday
    Date(format(valid_date - timedelta(days=1)), False),
    # date in the past
    Date(format(valid_date - timedelta(days=365)), False),
    # date with zero values of day, month, year
    Date((valid_date + timedelta(days=31)).strftime("00.%m.%Y"), False),
    Date(valid_date.strftime("%d.00.%Y"), False),
    Date(valid_date.strftime("%d.%m.0000"), False),
    # date with invalid values of day, month
    Date(valid_date.strftime("32.%m.%Y"), False),
    Date(valid_date.strftime("%d.13.%Y"), False),
    # date with text characters
    Date(replace_digit_with_letter(format(valid_date)), False),
    # date with "/" as a separator
    Date(valid_date.strftime("%d/%m/%Y"), True),
    # date in format different from "DD.MM.YYYY"
    Date((valid_date + timedelta(days=31)).strftime("%m.28.%Y"), False),
    # date with year in short format "MM.DD.YY"
    Date(valid_date.strftime("%d.%m.%y"), True),
    # date value is made of space characters
    Date(get_spaces(size=randint(1, 10)), False),
    # zero as date value
    Date("0", False),
    # date made of zeros only
    Date("00.00.0000", False),
    # special "system zero" date
    Date("01.01.1900", False),
    # upper technology border
    Date("99.99.9999", False),
]
