# -*- coding: utf-8; -*-
from selenium.webdriver.common.keys import Keys
from common.string import make_full_name_rus


def test_driver_2_name_default(
        osago_web_app, open_calculator_page, limited_number_of_drivers):
    """
    [osago-393]
    """
    page = osago_web_app.calculator_page
    assert page.is_driver_2_name_displayed()
    assert page.get_driver_2_name_value() == ""
    assert page.is_driver_2_checked_good()


def test_driver_2_name_data(
        osago_web_app, open_calculator_page,
        limited_number_of_drivers, data_osago_driver_name):
    """
    [osago-396]
    [osago-397]
    """
    page = osago_web_app.calculator_page
    counter_before = page.get_values_to_enter_count()
    page.set_driver_2_name(data_osago_driver_name)
    counter_after = page.get_values_to_enter_count()
    if data_osago_driver_name.valid:
        assert page.is_driver_2_name_checked_good()
        assert counter_before - 1 == counter_after
    else:
        assert not page.is_driver_2_name_checked_good()
        assert counter_before == counter_after
        assert page.driver_2_name_error_message


def test_one_character_and_jump(
        osago_web_app, open_calculator_page, limited_number_of_drivers):
    """
    [osago-399]
    """
    page = osago_web_app.calculator_page
    driver_name = make_full_name_rus()
    page.driver_2_name_send_keys(driver_name[:1] + Keys.BACK_SPACE + Keys.TAB)
    assert not page.driver_2_name_error_message
    assert not page.is_driver_2_name_checked_good()
    assert page.get_driver_2_name_value() == ""


def test_one_character_and_stand(
        osago_web_app, open_calculator_page, limited_number_of_drivers):
    """
    [osago-400]
    """
    driver_name = make_full_name_rus()
    page = osago_web_app.calculator_page
    page.driver_2_name_send_keys(driver_name[1])
    assert not page.driver_2_name_error_message
    assert not page.is_driver_2_name_checked_good()


def test_multi_characters_and_stand(
        osago_web_app, open_calculator_page, limited_number_of_drivers):
    """
    [osago-834]
    """
    driver_name = make_full_name_rus()
    page = osago_web_app.calculator_page
    page.driver_2_name_send_keys(driver_name[:-1])
    assert not page.driver_2_name_error_message
    assert not page.is_driver_2_name_checked_good()


def test_all_characters_and_stand(
        osago_web_app, open_calculator_page, limited_number_of_drivers,
        json_osago_driver_name):
    """
    [osago-401]
    """
    page = osago_web_app.calculator_page
    driver_name = json_osago_driver_name.value
    page.driver_2_name_send_keys(driver_name)
    assert not page.driver_2_name_error_message
    assert not page.is_driver_2_name_checked_good()
