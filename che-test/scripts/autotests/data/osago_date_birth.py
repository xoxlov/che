# -*- coding: utf-8; -*-
from datetime import datetime
from dateutil.relativedelta import relativedelta
from random import randint
from common.date_time import Date, format
from common.string import replace_digit_with_letter
from common.randomize import get_random_spacechar_filled_string as get_spaces


valid_age = datetime.today() - relativedelta(years=30)
testdata = [
    # 30 years before today
    Date(format(valid_age), True),
    # 18 years before today
    Date(format(datetime.today() - relativedelta(years=18)), True),
    # 18 years before today + 1 day
    Date(format(datetime.today() - relativedelta(years=18, days=-1)), False),
    # 100 years before today
    Date(format(datetime.today() - relativedelta(years=100)), True),
    # yesterday
    Date(format(datetime.today() - relativedelta(days=1)), False),
    # today
    Date(format(datetime.today()), False),
    # tomorrow
    Date(format(datetime.today() + relativedelta(days=1)), False),
    # 30 years before today with zeros in 'days'
    Date(valid_age.strftime("00.%m.%Y"), False),
    # 30 years before today with zeros in 'month'
    Date(valid_age.strftime("%d.00.%Y"), False),
    # 30 years before today with zeros in 'year'
    Date(valid_age.strftime("%d.%m.0000"), False),
    # 30 years before today with incorrect day
    Date(valid_age.strftime("32.%m.%Y"), False),
    # 30 years before today with incorrect month
    Date(valid_age.strftime("%d.13.%Y"), False),
    # 30 years before today with text characters
    Date(replace_digit_with_letter(format(valid_age)), False),
    # 30 years before today with slashes as separators
    Date(valid_age.strftime("%d/%m/%Y"), False),
    # 30 years before today without separators
    Date(valid_age.strftime("%d%m%Y"), False),
    # 30 years before today with format differrent from "DD.MM.YYYY"
    Date(valid_age.strftime("%m%d%Y"), False),
    # 30 years before today with short year
    Date(valid_age.strftime("%m%d%y"), True),
    # data value made of spacechars
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
