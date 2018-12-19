# -*- coding: utf-8; -*-
from selenium.webdriver.common.keys import Keys


def test_owner_passport_default(
        osago_web_app, open_calculator_page, limited_number_of_drivers):
    """
    [osago-722]
    [osago-723]
    """
    page = osago_web_app.calculator_page
    assert page.is_owner_passport_displayed()
    assert page.get_owner_passport() == ""
    assert not page.is_owner_passport_checked_good()


def test_owner_passport_value(
        osago_web_app, open_calculator_page,
        limited_number_of_drivers, data_osago_passport):
    """
    [osago-724]
    [osago-725]
    """
    page = osago_web_app.calculator_page
    counter_before = page.get_values_to_enter_count()
    page.set_owner_passport(data_osago_passport)
    counter_after = page.get_values_to_enter_count()
    if data_osago_passport.valid:
        assert page.is_owner_passport_checked_good()
        assert counter_before - 1 == counter_after
    else:
        assert not page.is_owner_passport_checked_good()
        assert counter_before == counter_after
        assert page.owner_passport_error_message


def test_owner_passport_drivers_limited(
        osago_web_app, open_calculator_page, limited_number_of_drivers):
    """
    [osago-790]
    """
    page = osago_web_app.calculator_page
    page.drivers_amount_unlimited_button.click()
    assert page.is_owner_passport_displayed()
    assert page.get_owner_passport() == ""
    assert not page.is_owner_passport_checked_good()


def test_one_character_and_jump(
        osago_web_app, open_calculator_page, json_osago_passport):
    """
    [osago-727]
    """
    page = osago_web_app.calculator_page
    page.owner_passport_send_keys(
        json_osago_passport[0] + Keys.BACK_SPACE + Keys.TAB)
    assert not page.owner_passport_error_message
    assert not page.is_owner_passport_checked_good()
    assert page.get_owner_passport() == ""


def test_one_character_and_stand(
        osago_web_app, open_calculator_page, json_osago_passport):
    """
    [osago-728]
    """
    page = osago_web_app.calculator_page
    page.owner_passport_send_keys(json_osago_passport[0])
    assert not page.owner_passport_error_message
    assert not page.is_owner_passport_checked_good()


def test_multi_characters_and_stand(
        osago_web_app, open_calculator_page, json_osago_passport):
    """
    [osago-729]
    """
    page = osago_web_app.calculator_page
    page.owner_passport_send_keys(json_osago_passport)
    assert not page.owner_passport_error_message
    assert not page.is_owner_passport_checked_good()


def test_all_characters_and_stand(
        osago_web_app, open_calculator_page, json_osago_passport):
    """
    [osago-730]
    """
    page = osago_web_app.calculator_page
    page.owner_passport_send_keys(json_osago_passport)
    assert not page.owner_passport_error_message
    assert not page.is_owner_passport_checked_good()
