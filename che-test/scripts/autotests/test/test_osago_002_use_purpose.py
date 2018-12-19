# -*- coding: utf-8; -*-


def test_use_purpose_default(osago_web_app, open_calculator_page):
    """
    [osago-302]
    """
    page = osago_web_app.calculator_page
    assert "Личная" in str(page.get_use_purpose_value())
    assert page.is_use_purpose_checked_good()


def test_use_purpose_inner_value(osago_web_app, open_calculator_page):
    """
    [osago-303]
    """
    page = osago_web_app.calculator_page
    page.select_use_purpose("Личная")
    assert "Личная" in str(page.get_use_purpose_value())
    assert page.is_use_purpose_checked_good()


def test_one_character_and_stand(osago_web_app, open_calculator_page):
    """
    [osago-304]
    """
    page = osago_web_app.calculator_page
    page.send_keys(page.use_purpose, "Л")
    assert "Личная" in str(page.get_use_purpose_value())
    assert page.is_use_purpose_checked_good()


def test_two_characters_and_stand(osago_web_app, open_calculator_page):
    """
    [osago-305]
    """
    page = osago_web_app.calculator_page
    page.send_keys(page.use_purpose, "Ли")
    assert "Личная" in str(page.get_use_purpose_value())
    assert page.is_use_purpose_checked_good()
