# -*- coding: utf-8; -*-


def test_osago_001_default(osago_web_app, open_main_page):
    """
    [osago-828]
    """
    page = osago_web_app.main_page
    assert page.verify_page_title()
    assert page.is_travel_insurance_inactive()
    assert page.is_auto_insurance_active()


def test_osago_001_navigate_to_travel(osago_web_app, open_main_page):
    """
    [osago-829]
    """
    page = osago_web_app.main_page
    page.button_travel_insurance.click()
    assert page.is_travel_insurance_active()
    assert page.is_auto_insurance_inactive()


def test_osago_001_default_number(osago_web_app, open_main_page):
    """
    [osago-352]
    """
    page = osago_web_app.main_page
    assert page.is_car_number_empty()
    assert page.is_car_region_empty()


def test_osago_001_car_number_and_region(
        osago_web_app, open_main_page, data_osago_car_number):
    """
    [osago-353]
    [osago-354]
    """
    page = osago_web_app.main_page
    page.input_car_number_and_region(data_osago_car_number)
    assert page.read_car_number_and_region() == data_osago_car_number
    if data_osago_car_number.valid:
        assert page.is_car_number_error_hidden()
    else:
        assert page.is_car_number_error_displayed()


def test_osago_001_submit_car_number(
        osago_web_app, open_main_page, json_osago_car_number):
    """
    [osago-360]
    """
    main_page = osago_web_app.main_page
    main_page.input_car_number_and_region(json_osago_car_number)
    assert main_page.start_insurance_search(), "OSAGO main page result"
    assert osago_web_app.calculator_page.wait()
