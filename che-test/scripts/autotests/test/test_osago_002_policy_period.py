# -*- coding: utf-8; -*-


def test_period_default(osago_web_app, open_calculator_page):
    """
    [osago-282]
    """
    page = osago_web_app.calculator_page
    assert "12" in str(page.get_insurable_period())
    assert page.is_insurable_period_checked_good()


def test_period_inner_value(osago_web_app, open_calculator_page):
    """
    [osago-46]
    """
    page = osago_web_app.calculator_page
    page.select_insurable_period("3")
    assert "3" in str(page.get_insurable_period())
    assert page.is_insurable_period_checked_good()


def test_one_character_and_stand(osago_web_app, open_calculator_page):
    """
    [osago-47]
    """
    page = osago_web_app.calculator_page
    page.insurable_period_send_keys("1")
    assert "10" in str(page.get_insurable_period())
    assert page.is_insurable_period_checked_good()


def test_two_characters_and_stand(osago_web_app, open_calculator_page):
    """
    [osago-290]
    """
    page = osago_web_app.calculator_page
    page.insurable_period_send_keys("12")
    assert "12" in str(page.get_insurable_period())
    assert page.is_insurable_period_checked_good()
