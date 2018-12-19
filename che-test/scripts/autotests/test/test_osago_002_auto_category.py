# -*- coding: utf-8; -*-


def test_auto_category_default(osago_web_app, open_calculator_page):
    """
    [osago-291]
    """
    category = "CATEGORY_B_BE"
    page = osago_web_app.calculator_page
    assert category == page.get_auto_category()
    assert page.is_auto_category_checked_good()


def test_auto_category_select(osago_web_app, open_calculator_page):
    """
    [osago-49]
    """
    category = "CATEGORY_C"
    page = osago_web_app.calculator_page
    page.select_auto_category(category)
    assert category == page.get_auto_category()
    assert page.is_auto_category_checked_good()


def test_auto_category_type(osago_web_app, open_calculator_page):
    """
    [osago-292]
    """
    category = "CATEGORY_D"
    page = osago_web_app.calculator_page
    page.auto_category_send_keys("D")
    assert category == page.get_auto_category()
    assert page.is_auto_category_checked_good()


def test_auto_category_type_retype(osago_web_app, open_calculator_page):
    """
    [osago-293]
    """
    category = "CATEGORY_D_DE"
    page = osago_web_app.calculator_page
    page.auto_category_send_keys("DE")
    assert category == page.get_auto_category()
    assert page.is_auto_category_checked_good()
