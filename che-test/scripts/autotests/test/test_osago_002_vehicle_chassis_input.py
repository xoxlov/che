# -*- coding: utf-8; -*-
from selenium.webdriver.common.keys import Keys


def test_chassis_input_default(
        osago_web_app, open_calculator_page):
    """
    [osago-764]
    [osago-765]
    """
    page = osago_web_app.calculator_page
    assert not page.is_vehicle_chassis_input_displayed()
    page.drivers_amount_unlimited_button.click()
    assert page.is_vehicle_chassis_input_displayed()
    assert page.get_vehicle_chassis_number() == ""
    assert not page.is_vehicle_chassis_checked_good()


def test_chassis_input_value(
        osago_web_app, open_calculator_page,
        unlimited_number_of_drivers, data_osago_vehicle_chassis):
    """
    [osago-766]
    [osago-767]
    """
    page = osago_web_app.calculator_page
    counter_before = page.get_values_to_enter_count()
    page.set_vehicle_chassis_number(data_osago_vehicle_chassis.value)
    counter_after = page.get_values_to_enter_count()
    if data_osago_vehicle_chassis.valid:
        assert page.is_vehicle_chassis_checked_good()
        assert counter_before - 1 == counter_after
    else:
        assert not page.is_vehicle_chassis_checked_good()
        assert counter_before == counter_after
        assert page.vehicle_chassis_error_message


def test_chassis_input_drivers_limited(
        osago_web_app, open_calculator_page, unlimited_number_of_drivers):
    """
    [osago-796]
    """
    page = osago_web_app.calculator_page
    page.drivers_amount_limited_button.click()
    assert not page.is_vehicle_chassis_input_displayed()


def test_one_character_and_jump(
        osago_web_app, open_calculator_page, unlimited_number_of_drivers,
        json_osago_vehicle_chassis):
    """
    [osago-769]
    """
    page = osago_web_app.calculator_page
    page.vehicle_chassis_input_send_keys(
        json_osago_vehicle_chassis.value[0] + Keys.BACK_SPACE + Keys.TAB)
    assert not page.vehicle_chassis_error_message
    assert not page.is_vehicle_chassis_checked_good()
    assert page.get_vehicle_chassis_number() == ""


def test_one_character_and_stand(
        osago_web_app, open_calculator_page, unlimited_number_of_drivers,
        json_osago_vehicle_chassis):
    """
    [osago-770]
    """
    page = osago_web_app.calculator_page
    page.vehicle_chassis_input_send_keys(json_osago_vehicle_chassis.value[0])
    assert not page.vehicle_chassis_error_message
    assert not page.is_vehicle_chassis_checked_good()


def test_multi_characters_and_stand(
        osago_web_app, open_calculator_page, unlimited_number_of_drivers,
        json_osago_vehicle_chassis):
    """
    [osago-771]
    """
    page = osago_web_app.calculator_page
    page.vehicle_chassis_input_send_keys(json_osago_vehicle_chassis.value[:-1])
    assert not page.vehicle_chassis_error_message
    assert not page.is_vehicle_chassis_checked_good()


def test_all_characters_and_stand(
        osago_web_app, open_calculator_page, unlimited_number_of_drivers,
        json_osago_vehicle_chassis):
    """
    [osago-772]
    """
    page = osago_web_app.calculator_page
    page.vehicle_chassis_input_send_keys(json_osago_vehicle_chassis.value)
    assert not page.vehicle_chassis_error_message
    assert not page.is_vehicle_chassis_checked_good()
