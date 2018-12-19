# -*- coding: utf-8; -*-
import re
import urllib.parse
from string import digits
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from common.config_module import get_value_from_config, load
from common.request import send_http_request, make_headers
from common.database import CheDb
from common.randomize import get_random_string


def make_request_url():
    with CheDb() as db:
        key = db.get_key_for_partner_code('biletix')
        assert key, "Cannot get from DB 'key' for partner 'biletix'"
    config = load("config/acceptance_vzr.json")
    days_from_now_to_start = config['insurance']['days_from_now_to_start']
    date_start = datetime.today() + timedelta(days=days_from_now_to_start)
    insured_days = config['insurance']['insuredDays']
    date_end = date_start + timedelta(days=insured_days - 1)
    traveller_age = config['traveller']['age']
    tourist_birthday = datetime.today() - relativedelta(years=traveller_age)
    parameters = {
        "key": key,
        "if[iata]": "PRG",
        "if[date_start]": date_start.strftime("%d.%m.%Y"),
        "if[date_end]": date_end.strftime("%d.%m.%Y"),
        "if[tourists]": 2,
        "ord[buyer][phone]": config['buyer']['phone'],
        "ord[tourists][0][firstName]": config['traveller']['first_name'],
        "ord[tourists][0][lastName]": config['traveller']['last_name'],
        "ord[tourists][0][passport]": get_random_string(chars=digits),
        "ord[tourists][0][birthDay]": tourist_birthday.strftime("%d.%m.%Y"),
        "ord[tourists][1][firstName]": config['buyer']['first_name'],
        "ord[tourists][1][lastName]": config['buyer']['last_name'],
        "ord[tourists][1][passport]": get_random_string(chars=digits),
        "ord[tourists][1][birthDay]": tourist_birthday.strftime("%d.%m.%Y"),
        "convertImages": 0,
    }
    request_url = "".join([
        "http:",
        get_value_from_config("['api']['url']").replace("/v2", "/v1"),
        '/mail.html?',
        urllib.parse.urlencode(parameters)
    ])
    return request_url


def test_biletix_html():
    """
    1. Сделать API запрос mail.html, проверить код ответа.
    2. Проверить что возвращаемое имеет базовую html-структуру.
    3. Проверить что в теле содержится кнопка "Купить".
    """
    response = \
        send_http_request(make_request_url(), "get", headers=make_headers())
    assert response.status_code == 200, \
        "Unexpected response code for /v1/mail request"
    is_response_html = all([
        re.match('<!DOCTYPE HTML', response.text, re.I),
        re.search('<html>', response.text, re.I),
        re.search('<body', response.text, re.I),
        re.search('</body>', response.text, re.I),
    ])
    assert is_response_html, "Response doesn't seem to be html"
    is_buy_button_present = \
        re.search('<img src="http.*alt=\"КУПИТЬ\"', response.text, re.I)
    assert is_buy_button_present, "Response has no 'Buy' button"
