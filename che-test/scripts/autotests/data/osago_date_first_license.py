# -*- coding: utf-8; -*-
from datetime import datetime
from dateutil.relativedelta import relativedelta
from random import randint
from common.date_time import Date, format
from common.string import replace_digit_with_letter
from common.randomize import get_random_spacechar_filled_string as get_spaces


valid_date = datetime.today() - relativedelta(years=1)
# Note: age of driver should be set to 30 years before today
testdata = [
    # today
    Date(format(datetime.today()), True),
    # tomorrow
    Date(format(datetime.today() + relativedelta(days=1)), False),
    # 1 year after today
    Date(format(datetime.today() + relativedelta(years=1)), False),
    # yesterday
    Date(format(datetime.today() - relativedelta(days=1)), True),
    # majority date
    Date(format(datetime.today() - relativedelta(years=12)), True),
    # one day before majority date
    Date(format(datetime.today() - relativedelta(years=12, days=1)), False),
    # 1 year before today with zeros in 'days'
    Date(valid_date.strftime("00.%m.%Y"), False),
    # 1 year before today with zeros in 'month'
    Date(valid_date.strftime("%d.00.%Y"), False),
    # 1 year before today with zeros in 'year'
    Date(valid_date.strftime("%d.%m.0000"), False),
    # 1 year before today with incorrect day
    Date(valid_date.strftime("32.%m.%Y"), False),
    # 1 year before today with incorrect month
    Date(valid_date.strftime("%d.13.%Y"), False),
    # 1 year before today with text characters
    Date(replace_digit_with_letter(format(valid_date)), False),
    # 1 year before today with slashes as separators
    Date(valid_date.strftime("%d/%m/%Y"), False),
    # 1 year before today without separators
    Date(valid_date.strftime("%d%m%Y"), False),
    # 1 year before today with format differrent from "DD.MM.YYYY"
    Date(valid_date.strftime("%m%d%Y"), False),
    # 1 year before today with short year
    Date(valid_date.strftime("%m%d%y"), True),
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
