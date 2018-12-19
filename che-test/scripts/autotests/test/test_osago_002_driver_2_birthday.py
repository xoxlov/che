# -*- coding: utf-8; -*-
from datetime import datetime
from dateutil import relativedelta
from selenium.webdriver.common.keys import Keys


def test_birthday_default(
        osago_web_app, open_calculator_page, limited_number_of_drivers):
    """
    [osago-404]
    """
    page = osago_web_app.calculator_page
    assert page.is_driver_2_birthday_displayed()
    assert page.get_driver_2_birthday() == ""
    assert not page.is_driver_2_birthday_checked_good()


def test_driver_2_birthday(
        osago_web_app, open_calculator_page,
        limited_number_of_drivers, data_osago_date_birth):
    """
    [osago-405]
    [osago-406]
    """
    page = osago_web_app.calculator_page
    counter_before = page.get_values_to_enter_count()
    page.set_driver_2_birthday_date(data_osago_date_birth)
    counter_after = page.get_values_to_enter_count()
    if data_osago_date_birth.valid:
        assert page.is_driver_2_birthday_checked_good()
        assert counter_before - 1 == counter_after
    else:
        assert not page.is_driver_2_birthday_checked_good()
        assert counter_before == counter_after
        assert page.date_driver_2_birthday_error_message


def test_one_character_and_jump(
        osago_web_app, open_calculator_page, limited_number_of_drivers):
    """
    [osago-408]
    """
    page = osago_web_app.calculator_page
    page.date_driver_2_birthday_send_keys("1" + Keys.BACK_SPACE + Keys.TAB)
    assert not page.date_driver_2_birthday_error_message
    assert not page.is_driver_2_birthday_checked_good()
    assert page.get_driver_2_birthday() == ""


def test_one_character_and_stand(
        osago_web_app, open_calculator_page, limited_number_of_drivers):
    """
    [osago-409]
    """
    page = osago_web_app.calculator_page
    page.date_driver_2_birthday_send_keys("1")
    assert not page.date_driver_2_birthday_error_message
    assert not page.is_driver_2_birthday_checked_good()


def test_multi_characters_and_stand(
        osago_web_app, open_calculator_page, limited_number_of_drivers):
    """
    [osago-410]
    """
    page = osago_web_app.calculator_page
    date = (datetime.today() - relativedelta(years=30)).strftime("%d.%m.%Y")
    page.date_driver_2_birthday_send_keys(date[:-1])
    assert not page.date_driver_2_birthday_error_message
    assert not page.is_driver_2_birthday_checked_good()


def test_all_characters_and_stand(
        osago_web_app, open_calculator_page, limited_number_of_drivers):
    """
    [osago-411]
    """
    page = osago_web_app.calculator_page
    date = (datetime.today() - relativedelta(years=30)).strftime("%d.%m.%Y")
    page.date_driver_2_birthday_send_keys(date)
    assert not page.date_driver_2_birthday_error_message
    assert not page.is_driver_2_birthday_checked_good()
