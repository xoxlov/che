# -*- coding: utf-8; -*-
from selenium.webdriver.common.keys import Keys


def test_vin_input_default(
        osago_web_app, open_calculator_page):
    """
    [osago-733]
    [osago-734]
    """
    page = osago_web_app.calculator_page
    assert not page.is_vehicle_vin_input_displayed()
    page.drivers_amount_unlimited_button.click()
    assert page.is_vehicle_vin_input_displayed()
    assert page.get_vehicle_vin() == ""
    assert not page.is_vehicle_vin_checked_good()


def test_vin_input_value(
        osago_web_app, open_calculator_page,
        unlimited_number_of_drivers, data_osago_vehicle_vin):
    """
    [osago-735]
    [osago-736]
    """
    page = osago_web_app.calculator_page
    counter_before = page.get_values_to_enter_count()
    page.set_vehicle_vin(data_osago_vehicle_vin.value)
    counter_after = page.get_values_to_enter_count()
    if data_osago_vehicle_vin.valid:
        assert page.is_vehicle_vin_checked_good()
        assert counter_before - 1 == counter_after
    else:
        assert not page.is_vehicle_vin_checked_good()
        assert counter_before == counter_after
        assert page.vehicle_vin_error_message


def test_vin_input_drivers_limited(
        osago_web_app, open_calculator_page, unlimited_number_of_drivers):
    """
    [osago-791]
    """
    page = osago_web_app.calculator_page
    page.drivers_amount_limited_button.click()
    assert not page.is_vehicle_vin_input_displayed()


def test_one_character_and_jump(
        osago_web_app, open_calculator_page, unlimited_number_of_drivers,
        json_osago_vehicle_vin):
    """
    [osago-738]
    """
    page = osago_web_app.calculator_page
    page.vehicle_vin_input_send_keys(json_osago_vehicle_vin.value[0]
                                     + Keys.BACK_SPACE + Keys.TAB)
    assert not page.vehicle_vin_error_message
    assert not page.is_vehicle_vin_checked_good()
    assert page.get_vehicle_vin() == ""


def test_one_character_and_stand(
        osago_web_app, open_calculator_page, unlimited_number_of_drivers,
        json_osago_vehicle_vin):
    """
    [osago-739]
    """
    page = osago_web_app.calculator_page
    page.vehicle_vin_input_send_keys(json_osago_vehicle_vin.value[0])
    assert not page.vehicle_vin_error_message
    assert not page.is_vehicle_vin_checked_good()


def test_multi_characters_and_stand(
        osago_web_app, open_calculator_page, unlimited_number_of_drivers,
        json_osago_vehicle_vin):
    """
    [osago-740]
    """
    page = osago_web_app.calculator_page
    page.vehicle_vin_input_send_keys(json_osago_vehicle_vin.value[:-1])
    assert not page.vehicle_vin_error_message
    assert not page.is_vehicle_vin_checked_good()


def test_all_characters_and_stand(
        osago_web_app, open_calculator_page, unlimited_number_of_drivers,
        json_osago_vehicle_vin):
    """
    [osago-741]
    """
    page = osago_web_app.calculator_page
    page.vehicle_vin_input_send_keys(json_osago_vehicle_vin.value)
    assert not page.vehicle_vin_error_message
    assert not page.is_vehicle_vin_checked_good()
