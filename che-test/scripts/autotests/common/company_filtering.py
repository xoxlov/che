# -*- coding: utf-8; -*-
from common.config_module import get_value_from_config
from common.database import CheDb
from common.request import send_http_request


def get_partners_with_disabled_companies():
    with CheDb() as db:
        query = "SELECT DISTINCT partnerId FROM partnerProperties " \
                "WHERE propName='disabled_company';"
        partner_ids_with_disabled_companies = db.execute_query(query)[0]
        assert partner_ids_with_disabled_companies, \
            "Cannot get from DB partner with disabled companies"
        return partner_ids_with_disabled_companies


def get_random_partner_without_disabled_companies():
    with CheDb() as db:
        query = "SELECT DISTINCT apiKeys.partnerId FROM apiKeys " \
                "LEFT JOIN partnerProperties ON apiKeys.partnerId = partnerProperties.partnerId " \
                "LEFT JOIN partners ON partners.id = apiKeys.partnerId " \
                "WHERE partnerProperties.propName is NULL " \
                "AND partners.id is NOT NULL " \
                "ORDER BY RAND() LIMIT 1"
        partner_id_without_disabled_companies = db.execute_query(query)
        assert partner_id_without_disabled_companies, \
            "Cannot get from DB partner without disabled companies"
        return partner_id_without_disabled_companies


def get_partner_code_by_id(partner_id):
    with CheDb() as db:
        query = "SELECT code FROM cherehapa_funk.partners WHERE id=%s" % partner_id
        query_result = db.execute_query(query)
        return query_result[0][0]


def make_company_api_request(partner_id=None):
    api_url = get_value_from_config("['api']['url']")
    request_url = ''.join(["http:", api_url, "/company"])
    if partner_id:
        request_url = ''.join([request_url, "?partnerId=", str(partner_id)])
    authorization = get_value_from_config("['authorization']", "config/api.json")
    headers = {'Authorization': authorization}
    response = send_http_request(request_url, "get", headers=headers)
    return response


def get_companies_from_response(response):
    return [company['id'] for company in response.json()['company']]


def retrieve_enabled_companies_from_calculator_page(app, db):
    """Open calculator web page and get available companies ids from it.

    :param app: web client to access VZR application
    :param db: existing database object
    :return: list of ids for enabled companies shown on the page
    """
    app.calculator_page.open_calculator_page_no_structure_checks()
    # set parameters to maximize offers amount
    initial_data_serial = app.calculator_page.data_serial_value
    app.calculator_page.set_travel_dates()
    app.calculator_page.set_service_medicine(50000)
    app.calculator_page.wait_dataset_serial_has_changed(initial_data_serial)
    company_names = app.calculator_page.get_enabled_company_names()
    return [db.get_company_id_by_name(company) for company in company_names]


def get_dataset_of_all_disabled_company_ids(db):
    all_disabled_company_ids = [db.get_disabled_companies_for_partner_id(pid)
                                for pid in get_partners_with_disabled_companies()]
    # flatten list and convert it to set
    all_disabled_company_ids = set(sum(all_disabled_company_ids, []))
    # exclude blocked companies
    all_disabled_company_ids = all_disabled_company_ids.difference(set(db.get_blocked_companies()))
    return all_disabled_company_ids
