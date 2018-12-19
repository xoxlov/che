# -*- coding: utf-8; -*-
from datetime import datetime
from dateutil import relativedelta
from selenium.webdriver.common.keys import Keys


def test_owner_birthday_default(osago_web_app, open_calculator_page):
    """
    [osago-711]
    """
    page = osago_web_app.calculator_page
    assert not page.is_owner_birthday_displayed()


def test_owner_birthday_drivers_amount(osago_web_app, open_calculator_page):
    """
    [osago-712]
    """
    page = osago_web_app.calculator_page
    page.drivers_amount_unlimited_button.click()
    assert page.is_owner_birthday_displayed()
    assert page.get_owner_birthday() == ""
    assert not page.is_owner_birthday_checked_good()


def test_owner_birthday_values(
        osago_web_app, open_calculator_page, data_osago_date_birth):
    """
    [osago-713]
    [osago-714]
    """
    page = osago_web_app.calculator_page
    page.drivers_amount_unlimited_button.click()
    counter_before = page.get_values_to_enter_count()
    page.set_owner_birthday_date(data_osago_date_birth)
    counter_after = page.get_values_to_enter_count()
    if data_osago_date_birth.valid:
        assert page.is_owner_birthday_checked_good()
        assert counter_before - 1 == counter_after
    else:
        assert not page.is_owner_birthday_checked_good()
        assert counter_before == counter_after
        assert page.date_owner_birthday_error_message


def test_one_character_and_jump(osago_web_app, open_calculator_page):
    """
    [osago-716]
    """
    page = osago_web_app.calculator_page
    page.drivers_amount_unlimited_button.click()
    page.date_owner_birthday_send_keys("1" + Keys.BACK_SPACE + Keys.TAB)
    assert not page.date_owner_birthday_error_message
    assert not page.is_owner_birthday_checked_good()
    assert page.get_owner_birthday() == ""


def test_one_character_and_stand(osago_web_app, open_calculator_page):
    """
    [osago-717]
    """
    page = osago_web_app.calculator_page
    page.drivers_amount_unlimited_button.click()
    page.date_owner_birthday_send_keys("1")
    assert not page.date_owner_birthday_error_message
    assert not page.is_owner_birthday_checked_good()


def test_multi_characters_and_stand(osago_web_app, open_calculator_page):
    """
    [osago-718]
    """
    page = osago_web_app.calculator_page
    page.drivers_amount_unlimited_button.click()
    date = (datetime.today() - relativedelta(years=30)).strftime("%d.%m.%Y")
    page.date_owner_birthday_send_keys(date[:-1])
    assert not page.date_owner_birthday_error_message
    assert not page.is_owner_birthday_checked_good()


def test_all_characters_and_stand(osago_web_app, open_calculator_page):
    """
    [osago-719]
    """
    page = osago_web_app.calculator_page
    page.drivers_amount_unlimited_button.click()
    date = (datetime.today() - relativedelta(years=30)).strftime("%d.%m.%Y")
    page.date_owner_birthday_send_keys(date)
    assert not page.date_owner_birthday_error_message
    assert not page.is_owner_birthday_checked_good()
