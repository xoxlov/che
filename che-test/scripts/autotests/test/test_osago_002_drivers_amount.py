# -*- coding: utf-8; -*-


def test_drivers_amount_default(osago_web_app, open_calculator_page):
    """
    [osago-440]
    """
    page = osago_web_app.calculator_page
    assert page.is_drivers_amount_limited()
    assert not page.is_drivers_amount_unlimited()


def test_drivers_amount_switch(osago_web_app, open_calculator_page):
    """
    [osago-441]
    [osago-442]
    """
    page = osago_web_app.calculator_page
    page.drivers_amount_unlimited_button.click()
    assert not page.is_drivers_amount_limited()
    assert page.is_drivers_amount_unlimited()
    page.drivers_amount_limited_button.click()
    assert page.is_drivers_amount_limited()
    assert not page.is_drivers_amount_unlimited()
