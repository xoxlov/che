# -*- coding: utf-8; -*-
import pytest
from common.company_filtering import *


@pytest.mark.parametrize("partner_id", get_partners_with_disabled_companies(),
                         ids=["partner #%s: %s" % (pid, get_partner_code_by_id(pid))
                              for pid in get_partners_with_disabled_companies()])
def test_partners_with_disabled_companies(db, partner_id):
    """
    - Для каждого partner_id с фильтрацией запросить GET /v2/company?partnerId=...
    - Для каждого partner_id с фильтрацией получить из БД набор disabled компаний
    - Убедиться, что в наборе компаний из api запросов отсутствует каждая disabled компания
    """
    response = make_company_api_request(partner_id)
    assert response.status_code == 200, "Bad response for /v2/company?partnerId=.. request"
    enabled_company_ids_received = set(get_companies_from_response(response))

    disabled_company_ids_from_db = set(db.get_disabled_companies_for_partner_id(partner_id))
    intersection = enabled_company_ids_received & disabled_company_ids_from_db
    assert not intersection, \
        "Response for partner with id=%s includes wrong companies" % partner_id


@pytest.mark.parametrize("partner_id",
                         [pytest.param(pid, id="partner #%s: %s"
                                               % (pid[0], get_partner_code_by_id(pid[0])))
                          for pid in get_random_partner_without_disabled_companies()])
def test_partners_without_disabled_companies(db, partner_id):
    """
    - Для случайного partner_id, на котором нет фильтрации, запросить GET /v2/company?partnerId=..
    - Получить из БД полный набор disabled компаний для всех партнёров,
      за исключением заблокированных
    - Убедиться, что в полном наборе компаний есть каждая disabled компания из предыдущего шага
    """
    response = make_company_api_request(partner_id)
    assert response.status_code == 200, "Bad response for /v2/company?partnerId=.. request"
    enabled_company_ids_received = set(get_companies_from_response(response))

    all_disabled_company_ids_from_db = get_dataset_of_all_disabled_company_ids(db)

    intersection = all_disabled_company_ids_from_db & enabled_company_ids_received
    assert intersection == all_disabled_company_ids_from_db, \
        "Response for partner with id=%s includes wrong companies" % partner_id


def test_no_partner(db):
    """
    - Запросить GET /v2/company без указания кода партнёра
    - Получить из БД полный набор disabled компаний для всех партнёров,
      за исключением заблокированных
    - Убедиться, что в полном наборе компаний есть каждая disabled компания из предыдущего шага
    """
    response = make_company_api_request()
    assert response.status_code == 200, "Bad response for /v2/company request"
    enabled_company_ids_received = set(get_companies_from_response(response))

    all_disabled_company_ids_from_db = get_dataset_of_all_disabled_company_ids(db)

    intersection = all_disabled_company_ids_from_db & enabled_company_ids_received
    assert intersection == all_disabled_company_ids_from_db, \
        "Response without partner id includes wrong companies"
