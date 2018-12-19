# -*- coding: utf-8; -*-
from selenium.webdriver.common.keys import Keys


def test_active_license_default(
        osago_web_app, open_calculator_page, limited_number_of_drivers):
    """
    [osago-330]
    """
    page = osago_web_app.calculator_page
    assert page.is_driver_1_license_displayed()
    assert page.get_driver_1_license() == ""
    assert not page.is_driver_1_license_checked_good()


def test_active_license_value(
        osago_web_app, open_calculator_page,
        limited_number_of_drivers, data_osago_driver_license):
    """
    [osago-331]
    [osago-332]
    """
    page = osago_web_app.calculator_page
    counter_before = page.get_values_to_enter_count()
    page.set_driver_1_license(data_osago_driver_license)
    counter_after = page.get_values_to_enter_count()
    if data_osago_driver_license.valid:
        assert page.is_driver_1_license_checked_good()
        assert counter_before - 1 == counter_after
    else:
        assert not page.is_driver_1_license_checked_good()
        assert counter_before == counter_after
        assert page.date_driver_1_license_error_message


def test_one_character_and_jump(
        osago_web_app, open_calculator_page, json_osago_driver_license):
    """
    [osago-333]
    """
    page = osago_web_app.calculator_page
    page.driver_1_license_send_keys(json_osago_driver_license[0]
                                    + Keys.BACK_SPACE + Keys.TAB)
    assert not page.date_driver_1_license_error_message
    assert not page.is_driver_1_license_checked_good()
    assert page.get_driver_1_license() == ""


def test_one_character_and_stand(
        osago_web_app, open_calculator_page, json_osago_driver_license):
    """
    [osago-334]
    """
    page = osago_web_app.calculator_page
    page.driver_1_license_send_keys(json_osago_driver_license[0])
    assert not page.date_driver_1_license_error_message
    assert not page.is_driver_1_license_checked_good()


def test_multi_characters_and_stand(
        osago_web_app, open_calculator_page, json_osago_driver_license):
    """
    [osago-335]
    """
    page = osago_web_app.calculator_page
    page.driver_1_license_send_keys(json_osago_driver_license[:-1])
    assert not page.date_driver_1_license_error_message
    assert not page.is_driver_1_license_checked_good()


def test_all_characters_and_stand(
        osago_web_app, open_calculator_page, json_osago_driver_license):
    """
    [osago-336]
    """
    page = osago_web_app.calculator_page
    page.driver_1_license_send_keys(json_osago_driver_license)
    assert not page.date_driver_1_license_error_message
    assert not page.is_driver_1_license_checked_good()
