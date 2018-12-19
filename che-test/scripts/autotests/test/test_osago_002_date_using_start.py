# -*- coding: utf-8; -*-
from selenium.webdriver.common.keys import Keys


def test_date_using_start_default(osago_web_app, open_calculator_page):
    """
    [osago-363]
    """
    page = osago_web_app.calculator_page
    assert not page.is_date_using_start_displayed()


def test_date_using_start_display(osago_web_app, open_calculator_page):
    """
    [osago-364]
    """
    page = osago_web_app.calculator_page
    page.select_insurable_period("10")
    assert page.is_date_using_start_displayed()
    assert page.get_date_using_start_value() == ""


def test_date_using_start_values(
        osago_web_app, open_calculator_page, data_osago_date_start):
    """
    [osago-365]
    [osago-366]
    """
    page = osago_web_app.calculator_page
    page.select_insurable_period("10")
    page.set_date_using_start(data_osago_date_start.value)
    if data_osago_date_start.valid:
        assert page.is_date_using_start_checked_good()
    else:
        assert not page.is_date_using_start_checked_good()
        assert page.date_using_start_error_message


def test_date_using_start_exceeded(osago_web_app, open_calculator_page):
    """
    [osago-367]
    """
    page = osago_web_app.calculator_page
    page.select_insurable_period("12")
    assert not page.is_date_using_start_displayed()


def test_one_character_and_jump(osago_web_app, open_calculator_page, tomorrow):
    """
    [osago-370]
    """
    page = osago_web_app.calculator_page
    page.select_insurable_period("10")
    page.date_using_start_send_keys("1" + Keys.BACK_SPACE + Keys.TAB)
    assert not page.date_using_start_error_message
    assert page.is_date_using_start_checked_good()
    assert tomorrow == page.get_date_using_start_value()


def test_one_character_and_stand(osago_web_app, open_calculator_page):
    """
    [osago-371]
    """
    page = osago_web_app.calculator_page
    page.select_insurable_period("10")
    page.date_using_start_send_keys("1")
    assert not page.date_using_start_error_message
    assert not page.is_date_using_start_checked_good()


def test_multi_characters_and_stand(
        osago_web_app, open_calculator_page, tomorrow):
    """
    [osago-372]
    """
    page = osago_web_app.calculator_page
    page.select_insurable_period("10")
    page.date_using_start_send_keys(tomorrow[:-1])
    assert not page.date_using_start_error_message
    assert not page.is_date_using_start_checked_good()


def test_all_characters_and_stand(
        osago_web_app, open_calculator_page, tomorrow):
    """
    [osago-373]
    """
    page = osago_web_app.calculator_page
    page.select_insurable_period("10")
    page.date_using_start_send_keys(tomorrow)
    assert not page.date_using_start_error_message
    assert not page.is_date_using_start_checked_good()
