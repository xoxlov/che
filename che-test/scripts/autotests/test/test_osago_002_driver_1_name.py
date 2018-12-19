# -*- coding: utf-8; -*-
from selenium.webdriver.common.keys import Keys
from common.string import make_full_name_rus


def test_driver_1_name_default(
        osago_web_app, open_calculator_page, limited_number_of_drivers):
    """
    [osago-307]
    """
    page = osago_web_app.calculator_page
    assert page.is_driver_1_name_displayed()
    assert page.get_driver_1_name_value() == ""
    assert page.is_driver_1_checked_good()


def test_driver_1_name_data(
        osago_web_app, open_calculator_page,
        limited_number_of_drivers, data_osago_driver_name):
    """
    [osago-54]
    [osago-55]
    """
    page = osago_web_app.calculator_page
    counter_before = page.get_values_to_enter_count()
    page.set_driver_1_name(data_osago_driver_name)
    counter_after = page.get_values_to_enter_count()
    if data_osago_driver_name.valid:
        assert page.is_driver_1_name_checked_good()
        assert counter_before - 1 == counter_after
    else:
        assert not page.is_driver_1_name_checked_good()
        assert counter_before == counter_after
        assert page.driver_1_name_error_message


def test_driver_1_name_drivers_amount(
        osago_web_app, open_calculator_page, limited_number_of_drivers):
    """
    [osago-685]
    """
    page = osago_web_app.calculator_page
    driver_name = make_full_name_rus()
    page.set_driver_1_name(driver_name)
    page.drivers_amount_unlimited_button.click()
    assert not page.is_driver_1_name_displayed()


def test_one_character_and_jump(
        osago_web_app, open_calculator_page, limited_number_of_drivers):
    """
    [osago-309]
    """
    page = osago_web_app.calculator_page
    driver_name = make_full_name_rus()
    page.driver_1_name_send_keys(driver_name[:1] + Keys.BACK_SPACE + Keys.TAB)
    assert not page.driver_1_name_error_message
    assert not page.is_driver_1_name_checked_good()
    assert page.get_driver_1_name_value() == ""


def test_one_character_and_stand(
        osago_web_app, open_calculator_page, limited_number_of_drivers):
    """
    [osago-833]
    """
    driver_name = make_full_name_rus()
    page = osago_web_app.calculator_page
    page.driver_1_name_send_keys(driver_name[1])
    assert not page.driver_1_name_error_message
    assert not page.is_driver_1_name_checked_good()


def test_multi_characters_and_stand(
        osago_web_app, open_calculator_page, limited_number_of_drivers):
    """
    [osago-310]
    """
    driver_name = make_full_name_rus()
    page = osago_web_app.calculator_page
    page.driver_1_name_send_keys(driver_name[:-1])
    assert not page.driver_1_name_error_message
    assert not page.is_driver_1_name_checked_good()


def test_all_characters_and_stand(
        osago_web_app, open_calculator_page, limited_number_of_drivers,
        json_osago_driver_name):
    """
    [osago-311]
    """
    page = osago_web_app.calculator_page
    driver_name = json_osago_driver_name.value
    page.driver_1_name_send_keys(driver_name)
    assert not page.driver_1_name_error_message
    assert not page.is_driver_1_name_checked_good()
