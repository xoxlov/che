# -*- coding: utf-8; -*-


def test_offers_default(osago_web_app, open_calculator_page):
    """
    [osago-443]
    """
    page = osago_web_app.calculator_page
    assert page.offers_displayed
    assert page.get_price(page.offers_displayed[0]) == "--.--"
    assert not page.is_buy_button_enabled(page.offers_displayed[0])


def test_valid_offers(osago_web_app, open_calculator_page):
    """
    [osago-444]
    """
    page = osago_web_app.calculator_page
    # TODO: Заполнить корректные данные страховки для одного водителя
    assert page.offers_displayed
    assert page.is_buy_button_enabled(page.offers_displayed[0])
    assert page.is_details_button_displayed(page.offers_displayed[0])
    assert page.is_details_block_hidden(page.offers_displayed[0])


def test_offers_details(osago_web_app, open_calculator_page):
    """
    [osago-445]
    [osago-446]
    """
    page = osago_web_app.calculator_page
    # TODO: Заполнить корректные данные страховки для одного водителя
    page.details_show_offer_0_button.click()
    assert not page.is_details_block_hidden(page.offers_displayed[0])
    page.details_hide_offer_0_button.click()
    assert page.is_details_block_hidden(page.offers_displayed[0])


def test_offers_proceed(osago_web_app, open_calculator_page):
    """
    [osago-447]
    """
    page = osago_web_app.calculator_page
    page.policy_buy_offer_0_button.click()
    assert osago_web_app.policy_details_page.wait()
