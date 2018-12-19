# -*- coding: utf-8; -*-


def test_add_driver_default(osago_web_app, open_calculator_page):
    """
    [osago-387]
    """
    page = osago_web_app.calculator_page
    assert page.is_add_driver_button_displayed()
    assert page.is_driver_1_icon_displayed()


def test_add_driver_unlimited_amount(osago_web_app, open_calculator_page):
    """
    [osago-677]
    """
    page = osago_web_app.calculator_page
    page.drivers_amount_unlimited_button.click()
    assert not page.is_add_driver_button_displayed()
    assert not page.is_driver_1_icon_displayed()


def test_add_driver_new_drivers(osago_web_app, open_calculator_page):
    """
    [osago-388]
    [osago-389]
    [osago-390]
    [osago-391]
    [osago-392]
    """
    page = osago_web_app.calculator_page

    page.drivers_amount_limited_button.click()
    assert page.is_add_driver_button_displayed()
    assert page.is_driver_2_icon_displayed()

    page.drivers_amount_limited_button.click()
    assert page.is_add_driver_button_displayed()
    assert page.is_driver_3_icon_displayed()

    page.drivers_amount_limited_button.click()
    assert page.is_add_driver_button_displayed()
    assert page.is_driver_4_icon_displayed()

    page.drivers_amount_limited_button.click()
    assert not page.is_add_driver_button_displayed()
    assert page.is_driver_5_icon_displayed()
