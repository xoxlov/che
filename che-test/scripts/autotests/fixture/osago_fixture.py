# -*- coding: utf-8; -*-
import pytest
from model.car_number import CarNumber


@pytest.fixture()
def open_main_page(osago_web_app):
    assert osago_web_app.main_page.open_osago_page(), "Main OSAGO page not opened"


@pytest.fixture()
def open_calculator_page(osago_web_app):
    main_page = osago_web_app.main_page
    calculator_page = osago_web_app.calculator_page
    if not calculator_page.is_active():
        open_main_page(osago_web_app)
        osago_car_number = CarNumber(number="Е807КН", region="197")
        main_page.input_car_number_and_region(osago_car_number)
        main_page.start_insurance_search()
    assert calculator_page.wait(), "OSAGO Calculator page not opened"


@pytest.fixture()
def limited_number_of_drivers(osago_web_app):
    open_calculator_page(osago_web_app)
    calculator_page = osago_web_app.calculator_page
    calculator_page.drivers_amount_limited_button.click()
    assert calculator_page.is_driver_1_icon_displayed(), "Driver #1 data cannot be found"


@pytest.fixture()
def unlimited_number_of_drivers(osago_web_app):
    open_calculator_page(osago_web_app)
    calculator_page = osago_web_app.calculator_page
    calculator_page.drivers_amount_unlimited_button.click()
    assert not calculator_page.is_driver_1_icon_displayed(), "Cannot limit number of drivers"
