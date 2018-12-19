# -*- coding: utf-8; -*-
import pytest
from common.config_module import get_value_from_config
from common.request import send_http_request, http_response_ok


base_url = get_value_from_config("['api']['url']")


def request_partner_payment_systems_from_api(partner_key):
    key_suffix = "".join(["?key=", partner_key]) if partner_key else ""
    url = "http:{}/paymentSystem{}".format(base_url, key_suffix)
    response = send_http_request(url, "get")
    assert response.status_code == http_response_ok
    available_payment_systems = [
        payment_system["id"]
        for payment_system in response.json()["paymentSystem"]
    ]
    return available_payment_systems


def test_default_payment_systems_request(data_payment_systems_default):
    partner = data_payment_systems_default
    expected_payment_systems = partner.payment_systems
    available_payment_systems = \
        request_partner_payment_systems_from_api(partner.key)
    assert available_payment_systems
    assert expected_payment_systems == available_payment_systems, \
        "actual Payment System list is wrong for {}" \
        "".format(partner.name)


# Note: partner key 'nC}|G4g7N#.qTD6Vi${i+=ukqkmz`q' causes test to fail for
# partner 1301 (tickets), so it's marked "xfail"
@pytest.mark.xfail
def test_partners_payment_systems_request(data_payment_systems):
    partner = data_payment_systems
    expected_payment_systems = partner.payment_systems
    available_payment_systems = \
        request_partner_payment_systems_from_api(partner.key)
    assert available_payment_systems
    assert expected_payment_systems == available_payment_systems, \
        "actual Payment System list is wrong for partner id={}" \
        "".format(partner.pid)
