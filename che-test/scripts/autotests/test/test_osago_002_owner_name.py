# -*- coding: utf-8; -*-
from selenium.webdriver.common.keys import Keys
from common.string import make_full_name_rus


def test_owner_name_default(osago_web_app, open_calculator_page):
    """
    [osago-780]
    """
    page = osago_web_app.calculator_page
    assert not page.is_owner_name_displayed()


def test_owner_name_drivers_unlim(
        osago_web_app, open_calculator_page):
    """
    [osago-781]
    """
    page = osago_web_app.calculator_page
    page.drivers_amount_unlimited_button.click()
    assert page.is_owner_name_displayed()
    assert page.get_owner_name_value() == ""
    assert not page.is_owner_checked_good()


def test_owner_name_data(
        osago_web_app, open_calculator_page, data_osago_driver_name):
    """
    [osago-782]
    [osago-783]
    """
    page = osago_web_app.calculator_page
    counter_before = page.get_values_to_enter_count()
    page.set_owner_name(data_osago_driver_name)
    counter_after = page.get_values_to_enter_count()
    if data_osago_driver_name.valid:
        assert page.is_owner_name_checked_good()
        assert counter_before - 1 == counter_after
    else:
        assert not page.is_owner_name_checked_good()
        assert counter_before == counter_after
        assert page.owner_name_error_message


def test_owner_name_drivers_limit(osago_web_app, open_calculator_page):
    """
    [osago-784]
    """
    page = osago_web_app.calculator_page
    page.drivers_amount_unlimited_button.click()
    driver_name = make_full_name_rus()
    page.set_owner_name(driver_name)
    page.drivers_amount_limited_button.click()
    assert not page.is_owner_name_displayed()


def test_one_character_and_jump(osago_web_app, open_calculator_page):
    """
    [osago-786]
    """
    page = osago_web_app.calculator_page
    page.drivers_amount_unlimited_button.click()
    driver_name = make_full_name_rus()
    page.owner_name_send_keys(driver_name[:1] + Keys.BACK_SPACE + Keys.TAB)
    assert not page.owner_name_error_message
    assert not page.is_owner_name_checked_good()
    assert page.get_owner_name_value() == ""


def test_one_character_and_stand(osago_web_app, open_calculator_page):
    """
    [osago-787]
    """
    page = osago_web_app.calculator_page
    page.drivers_amount_unlimited_button.click()
    driver_name = make_full_name_rus()
    page.owner_name_send_keys(driver_name[:-1])
    assert not page.owner_name_error_message
    assert not page.is_owner_name_checked_good()


def test_multi_characters_and_stand(osago_web_app, open_calculator_page):
    """
    [osago-788]
    """
    page = osago_web_app.calculator_page
    page.drivers_amount_unlimited_button.click()
    driver_name = make_full_name_rus()
    page.owner_name_send_keys(driver_name[:-1])
    assert not page.owner_name_error_message
    assert not page.is_owner_name_checked_good()


def test_all_characters_and_stand(osago_web_app, open_calculator_page):
    """
    [osago-789]
    """
    page = osago_web_app.calculator_page
    page.drivers_amount_unlimited_button.click()
    driver_name = make_full_name_rus()
    page.owner_name_send_keys(driver_name)
    assert not page.owner_name_error_message
    assert not page.is_owner_name_checked_good()
