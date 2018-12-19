# -*- coding: utf-8; -*-


def test_auto_number_default(
        osago_web_app, open_calculator_page, json_osago_car_number):
    """
    [osago-274]
    """
    page = osago_web_app.calculator_page
    assert json_osago_car_number == page.get_auto_number()


def test_auto_number_change(osago_web_app, open_calculator_page):
    """
    [osago-275]
    """
    osago_web_app.calculator_page.change_number_button.click()
    assert osago_web_app.main_page.is_travel_page_open()
