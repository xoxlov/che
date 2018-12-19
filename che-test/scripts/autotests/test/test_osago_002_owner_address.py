# -*- coding: utf-8; -*-
from selenium.webdriver.common.keys import Keys


def test_owner_address_default(
        osago_web_app, open_calculator_page, limited_number_of_drivers):
    """
    [osago-433]
    """
    page = osago_web_app.calculator_page
    assert page.is_owner_address_displayed()
    assert page.get_owner_address() == ""
    assert not page.is_owner_address_checked_good()


def test_owner_address_drivers_unlim(
        osago_web_app, open_calculator_page, limited_number_of_drivers):
    """
    [osago-700]
    """
    page = osago_web_app.calculator_page
    page.drivers_amount_unlimited_button.click()
    assert page.is_owner_address_displayed()
    assert page.get_owner_address() == ""
    assert not page.is_owner_address_checked_good()


def test_owner_address_value(
        osago_web_app, open_calculator_page,
        limited_number_of_drivers, data_osago_address):
    """
    [osago-434]
    [osago-435]
    """
    page = osago_web_app.calculator_page
    counter_before = page.get_values_to_enter_count()
    page.set_owner_address(data_osago_address)
    counter_after = page.get_values_to_enter_count()
    if data_osago_address.valid:
        assert page.is_owner_address_checked_good()
        assert counter_before - 1 == counter_after
    else:
        assert not page.is_owner_address_checked_good()
        assert counter_before == counter_after
        assert page.owner_address_error_message


def test_one_character_and_jump(
        osago_web_app, open_calculator_page, json_osago_address):
    """
    [osago-437]
    """
    page = osago_web_app.calculator_page
    page.owner_address_send_keys(json_osago_address[0]
                                 + Keys.BACK_SPACE + Keys.TAB)
    assert not page.owner_address_error_message
    assert not page.is_owner_address_checked_good()
    assert page.get_owner_address() == ""


def test_one_character_and_stand(
        osago_web_app, open_calculator_page, json_osago_address):
    """
    [osago-438]
    """
    page = osago_web_app.calculator_page
    page.owner_address_send_keys(json_osago_address[0])
    assert not page.owner_address_error_message
    assert not page.is_owner_address_checked_good()


def test_all_characters_and_stand(
        osago_web_app, open_calculator_page, json_osago_address):
    """
    [osago-439]
    """
    page = osago_web_app.calculator_page
    page.owner_address_send_keys(json_osago_address)
    assert not page.owner_address_error_message
    assert not page.is_owner_address_checked_good()
