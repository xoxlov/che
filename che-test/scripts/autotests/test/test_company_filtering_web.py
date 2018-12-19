# -*- coding: utf-8; -*-
import pytest
from common.company_filtering import *


@pytest.mark.parametrize("partner_id", get_partners_with_disabled_companies(),
                         ids=["partner #%s: %s" % (pid, get_partner_code_by_id(pid))
                              for pid in get_partners_with_disabled_companies()])
def test_partners_with_disabled_companies(vzr_web_app, db, partner_id):
    """Для каждого partner_id с фильтрацией перейти на страницу калькулятора,
    используя параметр partnerId. Убедиться что набор доступных компаний не
    имеет пересечений с набором запрещённых для партнёра компаний.
    """
    vzr_web_app.webdriver.delete_all_cookies()
    vzr_web_app.set_url_params({"partnerId": partner_id})
    enabled_company_ids_displayed = \
        set(retrieve_enabled_companies_from_calculator_page(vzr_web_app, db))
    assert enabled_company_ids_displayed, "No enabled companies found on calculator page"

    disabled_company_ids_from_db = set(db.get_disabled_companies_for_partner_id(partner_id))
    # exclude blocked companies
    disabled_company_ids_from_db = disabled_company_ids_from_db - set(db.get_blocked_companies())

    disabled_company_ids_displayed = enabled_company_ids_displayed & disabled_company_ids_from_db
    assert not disabled_company_ids_displayed, \
        "Calculator page shows wrong companies list for partner id=%s" % partner_id


@pytest.mark.parametrize("partner_id",
                         [pytest.param(pid[0], id="partner #%s: %s"
                                               % (pid[0], get_partner_code_by_id(pid[0])))
                          for pid in get_random_partner_without_disabled_companies()])
def test_partners_without_disabled_companies(vzr_web_app, db, partner_id):
    """Для случайного partner_id без фильтрации перейти на страницу калькулятора,
    используя параметр partnerId. Убедиться, что набор компаний, показанных
    на странице, включает в себя набор компаний, запрещенных для других партнёров.
    """
    vzr_web_app.webdriver.delete_all_cookies()
    vzr_web_app.set_url_params({"partnerId": partner_id})
    enabled_company_ids_displayed = \
        set(retrieve_enabled_companies_from_calculator_page(vzr_web_app, db))
    assert enabled_company_ids_displayed, "No enabled companies found on calculator page"

    all_disabled_company_ids_from_db = get_dataset_of_all_disabled_company_ids(db)

    disabled_companies_from_page = enabled_company_ids_displayed & all_disabled_company_ids_from_db
    assert disabled_companies_from_page == all_disabled_company_ids_from_db


def test_no_partner(vzr_web_app, db):
    """Перейти на страницу калькулятора, не используя параметр partnerId.
    Убедиться, что набор компаний, показанных на странице, включает в себя
    набор компаний, запрещенных для других партнёров.
    """
    vzr_web_app.webdriver.delete_all_cookies()
    vzr_web_app.delete_url_param("partnerId")
    enabled_company_ids_displayed = \
        set(retrieve_enabled_companies_from_calculator_page(vzr_web_app, db))
    assert enabled_company_ids_displayed, "No enabled companies found on calculator page"

    all_disabled_company_ids_from_db = get_dataset_of_all_disabled_company_ids(db)

    disabled_companies_from_page = enabled_company_ids_displayed & all_disabled_company_ids_from_db
    assert disabled_companies_from_page == all_disabled_company_ids_from_db
