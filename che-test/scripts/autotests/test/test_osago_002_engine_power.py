# -*- coding: utf-8; -*-
from selenium.webdriver.common.keys import Keys


def test_engine_power_default(osago_web_app, open_calculator_page):
    """
    [osago-295]
    """
    page = osago_web_app.calculator_page
    assert not page.is_engine_power_checked_good()
    assert not page.get_engine_power()


def test_engine_power_validity(
        osago_web_app, open_calculator_page, data_osago_engine_power):
    """
    [osago-51]
    [osago-52]
    """
    page = osago_web_app.calculator_page
    counter_before = page.get_values_to_enter_count()
    page.set_engine_power(data_osago_engine_power)
    counter_after = page.get_values_to_enter_count()
    if data_osago_engine_power.valid:
        assert page.is_engine_power_checked_good()
        assert counter_before - 1 == counter_after
    else:
        assert not page.is_engine_power_checked_good()
        assert counter_before == counter_after
        assert page.engine_power_error_message


def test_engine_one_character_and_jump(osago_web_app, open_calculator_page):
    """
    [osago-297]
    """
    page = osago_web_app.calculator_page
    page.engine_power_send_keys("1" + Keys.BACK_SPACE + Keys.TAB)
    assert not page.engine_power_error_message
    assert not page.is_engine_power_checked_good()
    assert not page.get_engine_power()


def test_engine_one_character_and_stand(osago_web_app, open_calculator_page):
    """
    [osago-298]
    """
    page = osago_web_app.calculator_page
    page.engine_power_send_keys("1")
    assert not page.engine_power_error_message
    assert not page.is_engine_power_checked_good()


def test_engine_multi_characters_and_stand(
        osago_web_app, open_calculator_page):
    """
    [osago-299]
    """
    page = osago_web_app.calculator_page
    page.engine_power_send_keys("9")
    assert not page.engine_power_error_message
    assert not page.is_engine_power_checked_good()


def test_engine_all_characters_and_stand(osago_web_app, open_calculator_page):
    """
    [osago-300]
    """
    page = osago_web_app.calculator_page
    page.engine_power_send_keys("90")
    assert not page.engine_power_error_message
    assert not page.is_engine_power_checked_good()
