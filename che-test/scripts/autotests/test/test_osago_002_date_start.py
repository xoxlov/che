# -*- coding: utf-8; -*-
from selenium.webdriver.common.keys import Keys


def test_date_default(osago_web_app, open_calculator_page, tomorrow):
    """
    [osago-276]
    """
    page = osago_web_app.calculator_page
    assert tomorrow == page.date_start_input.get_value()
    assert page.is_date_start_checked_good()


def test_date_start(
        osago_web_app, open_calculator_page, data_osago_date_start):
    """
    [osago-43]
    [osago-44]
    """
    page = osago_web_app.calculator_page
    counter_before = page.get_values_to_enter_count()
    page.set_date_start(data_osago_date_start.value)
    counter_after = page.get_values_to_enter_count()
    if data_osago_date_start.valid:
        assert page.is_date_start_checked_good()
        assert counter_before - 1 == counter_after
    else:
        assert not page.is_date_start_checked_good()
        assert counter_before == counter_after
        assert page.date_start_error_message


def test_one_character_and_jump(osago_web_app, open_calculator_page, tomorrow):
    """
    [osago-278]
    """
    page = osago_web_app.calculator_page
    page.date_start_input.send_keys("1" + Keys.BACK_SPACE + Keys.TAB)
    assert not page.date_start_error_message
    assert page.is_date_start_checked_good()
    assert tomorrow == page.date_start_input.get_value()


def test_one_character_and_stand(osago_web_app, open_calculator_page):
    """
    [osago-279]
    """
    page = osago_web_app.calculator_page
    page.date_start_input.send_keys("0")
    assert not page.date_start_error_message
    assert not page.is_date_start_checked_good()


def test_multi_characters_and_stand(
        osago_web_app, open_calculator_page, today):
    """
    [osago-280]
    """
    page = osago_web_app.calculator_page
    page.date_start_input.send_keys(today[:-1])
    assert not page.date_start_error_message
    assert not page.is_date_start_checked_good()


def test_all_characters_and_stand(osago_web_app, open_calculator_page, today):
    """
    [osago-281]
    """
    page = osago_web_app.calculator_page
    page.date_start_input.send_keys(today)
    assert not page.date_start_error_message
    assert not page.is_date_start_checked_good()
