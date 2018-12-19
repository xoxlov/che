# -*- coding: utf-8; -*-


def test_no_vin_but_chassis_default(
        osago_web_app, open_calculator_page, limited_number_of_drivers):
    """
    [osago-794]
    [osago-759]
    """
    page = osago_web_app.calculator_page
    assert not page.no_vin_but_chassis_checkbox.is_displayed()

    page.drivers_amount_unlimited_button.click()
    assert page.no_vin_but_chassis_checkbox.is_displayed()
    assert not page.no_vin_but_chassis_checkbox.is_selected()
    assert page.is_vehicle_vin_number_enabled()
    assert not page.is_vehicle_chassis_input_displayed()


def test_no_vin_but_chassis_set_unset(
        osago_web_app, open_calculator_page, limited_number_of_drivers):
    """
    [osago-760]
    [osago-761]
    """
    page = osago_web_app.calculator_page
    page.drivers_amount_unlimited_button.click()
    page.no_vin_but_chassis_checkbox.set(True)
    assert not page.is_vehicle_vin_number_enabled()
    assert page.is_vehicle_chassis_input_displayed()
    assert not page.no_vin_but_body_checkbox.is_selected()

    page.no_vin_but_chassis_checkbox.set(False)
    assert page.is_vehicle_vin_number_enabled()
    assert not page.is_vehicle_chassis_input_displayed()


def test_no_vin_but_chassis_drivers_limited(
        osago_web_app, open_calculator_page, limited_number_of_drivers):
    """
    [osago-795]
    """
    page = osago_web_app.calculator_page
    page.drivers_amount_unlimited_button.click()
    page.no_vin_but_chassis_checkbox.set(True)
    page.drivers_amount_limited_button.click()
    assert not page.no_vin_but_chassis_checkbox.is_displayed()
