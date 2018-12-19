#!/usr/bin/env python3
# -*- coding: utf-8; -*-
#
# python hooking functions used by dredd for cherehapa api testing.
#
# these two imports must be 1st - required by dredd, right in this order:
import hooks
import dredd_hooks as hooks

import json
import sys
import requests
import datetime
import re

# add dir with common_test_functions.py and import what we need there
sys.path.append("../autotests")
import common.logger as logger
from common.config_module import get_value_from_config
from common.database import CheDb


###############################################################################
# Functions used in Test Cases
###############################################################################
def refuse_production_configuration():
    production_db_host = "db.aws.che.lo"
    cfg_dbhost = get_value_from_config("['database']['host']")
    cfg_environment = get_value_from_config("['partner']['rollbar']['env']")
    if "api.cherehapa.ru" in base_url \
            or cfg_dbhost == production_db_host \
            or cfg_environment == "production":
        raise Exception("Dredd tests cannot be executed on production environment")


def add_dredd_user_in_database():
    # login, password = "dredd", "123123" (hash is used in table for password)
    query = "insert into cherehapa_funk.users " \
            "(`dateRegister`, `login`, `password`, `partnerId`) " \
            "values " \
            "(NOW(), 'dredd', 'idxgXaLE2549c202d6db0d070555e1bd608c6303', 0);"
    with CheDb() as db:
        db.execute_query(query)


def delete_dredd_users_in_database():
    query = "delete from cherehapa_funk.users where login='dredd';"
    with CheDb() as db:
        db.execute_query(query)


def add_dredd_key_in_database():
    # access key = "dredd"
    query = "insert into cherehapa_funk.apiKeys " \
            "(`key`, `partnerId`) " \
            "values " \
            "('dredd', 1);"
    with CheDb() as db:
        db.execute_query(query)


def delete_dredd_keys_in_database():
    query = "delete from cherehapa_funk.apiKeys where `key`='dredd';"
    with CheDb() as db:
        db.execute_query(query)


def skip_transaction_processing_by_hook(transaction):
    logger.info("Skipping this test.")
    if transaction["name"]:
        command = re.findall("([A-Z]* /.*)*$", transaction["name"])[0]
        logger.info("'%s' will be tested outside of dredd." % command)
    transaction["skip"] = True


def replace_taskid_in_transaction(transaction, new_task_id):
    transaction["request"]["uri"] = "/task/%s" % new_task_id
    transaction["fullPath"] = "/v2/task/%s" % new_task_id
    transaction["id"] = "GET /task/%s" % new_task_id


def replace_task_osago_uuid_in_transaction(transaction, new_uuid):
    transaction["request"]["uri"] = "/task/osago/%s" % new_uuid
    transaction["fullPath"] = "/v2/task/osago/%s" % new_uuid
    transaction["id"] = "GET /task/osago/%s" % new_uuid

def replace_order_avia_osago_uuid_in_delete_transaction(transaction, new_uuid):
    transaction["request"]["uri"] = "/order/avia/%s" % new_uuid
    transaction["fullPath"] = "/v2/order/avia/%s" % new_uuid
    transaction["id"] = "GET /order/avia/%s" % new_uuid

def replace_task_avia_uuid_in_transaction(transaction, new_uuid):
    transaction["request"]["uri"] = "/task/avia/%s" % new_uuid
    transaction["fullPath"] = "/v2/task/avia/%s" % new_uuid
    transaction["id"] = "GET /task/avia/%s" % new_uuid


###############################################################################
# Config values and settings
###############################################################################
response_stash = {}
base_url = "http:" + get_value_from_config("['api']['url']")
logger.info("base_url: %s" % base_url)

days_start_from_now = 4
days_to_insure = 1
date_start = datetime.date.today() + datetime.timedelta(days=days_start_from_now)
# start date is in scope, therefore temidelta is 1 day shorter
date_end = date_start + datetime.timedelta(days=days_to_insure - 1)

# POST request parameters for policy creation request
req_data_vzr = {
    "currency": "eur",
    "dateStart": date_start.strftime("%d.%m.%Y"),
    "dateEnd": date_end.strftime("%d.%m.%Y"),
    "insuredDays": days_to_insure,
    "country[]": "italy",
    "service[medicine]": 30000,
    "service[aviaCargo]": 1500,
    "service[accident]": 0,
    "service[civilLiability]": 0,
    "service[urgentStomatology]": 1,
    "service[cargo]": 1500,
    "tourist[0][firstName]": "Touristname",
    "tourist[0][lastName]": "Touristfamily",
    "tourist[0][hidden]": 0,
    "tourist[0][birthday]": "24.12.1983",
    "insurer[name]": "Insurername",
    "insurer[lastName]": "Insurerlastname",
    "insurer[secondName]": "Insurersecondname",
    "insurer[nameRU]": "required",
    "insurer[lastNameRU]": "%B6%D0%B5%D0%B7%D0%B8%D0%BD%D1%81%D0%BA%D0%B8%D0%B9",
    "insurer[secondNameRU]": "%B8%D0%BC%D1%83%D0%BB%D1%8C%D0%B4%D0%B8%D0%BD%D0%BE%D0%B2%D0%B8%D1%87",
    "insurer[phone]": "71111234567",
    "insurer[email]": "nomail@nodomain.no",
    "insuranceProduct[]": 9,
    "paymentSystem": 7,
    # use test card without 3d secure: 4111111111111112
    "card[number]": "4111111111111112",
    "card[month]": 12,
    "card[year]": 18,
    "card[cvc]": 123,
    "card[holder]": "Torvlandor%2BBzhezinskiy",
    "sport[]": "waterAerobics",
    "key": "dredd",
    "partnerId": 1,
    "_method": "post"
}
req_data_osago = {
    "returnUrl": "http://osago.che.test/payment",
    "cardData[number]": "5555555555555599",
    "cardData[month]": 12,
    "cardData[year]": 2019,
    "cardData[cvc]": 123,
    "cardData[holder]": "Test Test",
    "_method": "post"
}
req_data_avia = {
    "dateStart": "24.12.2018",
    "dateEnd": "24.12.2018",
    "products[0]": "cargoAccident",
    "tourist[0][firstName]": "Test",
    "tourist[0][lastName]": "Testov",
    "tourist[0][birthday]": "02.01.1990",
    "tourist[0][ticketPrice]": 19101.7,
    "insurer[firstName]": "Test",
    "insurer[lastName]": "Testov",
    "insurer[email]": "testtestov@mailinator.com",
    "paymentSystem": "wire",
    "partnerId": 1,
    "key": "dredd",
    "_method": "post"
}
req_headers = {
    "Authorization": "Basic YXBhaGVyZWhjOjlzQmJPeTZk",
    "key": "dredd"
}


###############################################################################
# Functions implementing hooks
###############################################################################
refuse_production_configuration()


@hooks.before_all
def my_before_all_hook(transactions):
    delete_dredd_users_in_database()
    add_dredd_user_in_database()
    delete_dredd_keys_in_database()
    add_dredd_key_in_database()


@hooks.after_all
def my_after_all_hook(transactions):
    delete_dredd_users_in_database()
    delete_dredd_keys_in_database()


@hooks.before_each
def my_before_each_hook(transaction):
    logger.info("Transaction name: %s" % transaction["name"])

    if transaction["name"] in (
            "API travel insurance - Расчет и выписка полиса > "
            + "policy: получить информацию по полису > "
            + "Метод: GET /policy/id",
            "API travel insurance - Расчет и выписка полиса > "
            + "policy: отмена выписанного ранее полиса > "
            + "Метод: DELETE /policy/id",
            "API avia insurance \"Черехапа Страхование\" - справочник методов > "
            + "aviaPolicyCancel: отмена одного полиса из ранее созданного заказа > "
            + "Метод DELETE /policy/avia/{encryptedId}/delete",
            "API справочник приватных методов \"Черехапа Страхование\" > " \
            "osagoInfo: получение информации для заполнения полей осаго из сторонних сервисов > " \
            "Метод GET /info/osago/{licensePlate}",
            "",
    ):
        skip_transaction_processing_by_hook(transaction)

    if transaction["name"] == \
            "API travel insurance - Расчет и выписка полиса > " \
            "task: информация по задаче и её статусе > " \
            "Метод GET /task/id":
        if "new_policy_vzr" in response_stash:
            logger.info("Replacing task in url with just created one (%s) to be used by dredd now.."
                        % response_stash["new_policy_vzr"]["task_uuid"])
            replace_taskid_in_transaction(transaction, response_stash["new_policy_vzr"]["task_uuid"])
        else:
            logger.info("Making POST request to %s/policy to create a task to get info about.." % base_url)
            response = requests.post(base_url + "/policy", headers=req_headers, data=req_data_vzr)
            if response.status_code == 201:
                task_id = response.json()["task"]["id"]
                replace_taskid_in_transaction(transaction, task_id)
            else:
                logger.error("Unexpected response code while making request to create policy.")
                logger.debug("Request text:\n%s" % response.text)
                transaction["skip"] = True

    if transaction["name"] == \
            "API справочник приватных методов \"Черехапа Страхование\" > " \
            "task: информация по задаче и её статусе > " \
            "Метод GET /task/osago/uuid":
        if "new_policy_osago" in response_stash:
            logger.info("Replacing task in url with just created one (%s) to be used by dredd now.."
                        % response_stash["new_policy_osago"]["task_uuid"])
            replace_task_osago_uuid_in_transaction(transaction, response_stash["new_policy_osago"]["task_uuid"])
        else:
            logger.info("Making POST request to %s/policy/osago to create a task to get info about.." % base_url)
            response = requests.post(base_url + "/policy/osago", headers=req_headers, data=req_data_osago)
            if response.status_code == 201:
                task_uuid = response.json()["uuid"]
                replace_task_osago_uuid_in_transaction(transaction, task_uuid)
            else:
                logger.error("Unexpected response code while making request to create policy.")
                logger.debug("Request text:\n" + response.text)
                transaction["skip"] = True

    if transaction["name"] == \
                "API avia insurance \"Черехапа Страхование\" - справочник методов > " \
                "task: информация по задаче создания или отмены полисов авиастрахования > " \
                "Метод GET /task/avia/id":
            if "new_policy_avia" in response_stash:
                logger.info("Replacing task in url with just created one (%s) to be used by dredd now.."
                            % response_stash["new_policy_avia"]["task_uuid"])
                replace_task_avia_uuid_in_transaction(transaction, response_stash["new_policy_avia"]["task_uuid"])
            else:
                logger.info("Making POST request to %s/policy/avia to create a task to get info about.." % base_url)
                response = requests.post(base_url + "/policy/avia", headers=req_headers, data=req_data_avia)
                if response.status_code == 201:
                    task_uuid = response.json()["id"]
                    replace_task_avia_uuid_in_transaction(transaction, task_uuid)
                else:
                    logger.error("Unexpected response code while making request to create policy.")
                    logger.debug("Request text:\n" + response.text)
                    transaction["skip"] = True

    if transaction["name"] == \
                    "API avia insurance \"Черехапа Страхование\" - справочник методов > " \
                    "aviaOrderCancel: отмена ранее созданного заказа > " \
                    "Метод DELETE /order/avia/{id}":
                if "new_policy_avia" in response_stash:
                    logger.info("Replacing task in url with just created one (%s) to be used by dredd now.."
                                % response_stash["new_policy_avia"]["task_uuid"])
                    replace_order_avia_osago_uuid_in_delete_transaction(transaction, response_stash["new_policy_avia"]["task_uuid"])
                else:
                    logger.info("Making POST request to %s/policy/avia to create a task to get info about.." % base_url)
                    response = requests.post(base_url + "/policy/avia", headers=req_headers, data=req_data_avia)
                    if response.status_code == 201:
                        task_uuid = response.json()["id"]
                        replace_order_avia_osago_uuid_in_delete_transaction(transaction, task_uuid)
                    else:
                        logger.error("Unexpected response code while making request to create policy.")
                        logger.debug("Request text:\n" + response.text)
                        transaction["skip"] = True

@hooks.after_each
def my_after_each(transaction):
    # validations already passed at this point, "transaction" type is dict
    if not transaction:
        logger.warning("empty transaction.")
        return
    if transaction["skip"]:
        return
    if transaction["name"] == \
            "API travel insurance - Расчет и выписка полиса > " \
            "policy: создание нового полиса по продуктам insuranceProduct > " \
            "Метод по продуктам insuranceProduct: POST /policy":
        logger.info("hooks after response POST /policy")
        try:
            status = transaction["real"]["statusCode"]
            body = json.loads(transaction["real"]["body"])
            if status == 201:
                logger.info("Storing task_uuid - will be used in other requests..")
                task_uuid = body["task"]["id"]
                response_stash["new_policy_vzr"] = {"status": status, "task_uuid": task_uuid}
            else:
                logger.warning("Status for POST /policy is not 201, "
                               "thus response data is not subject for save between API tests.")
                logger.warning("This may have impact on /task/id API test.")
        except Exception as e:
            logger.error("Exception accessing transaction['real']['body']: %s" % str(e))
            logger.error("Actual transaction:\n" + transaction)

    if transaction["name"] == \
            "API справочник приватных методов \"Черехапа Страхование\" > " \
            "osago: запрос на выписку полиса > " \
            "Метод: POST /policy/osago":
            logger.info("hooks after response POST /policy/osago")
            try:
                status = transaction["real"]["statusCode"]
                body = json.loads(transaction["real"]["body"])

                if status == 201:
                    logger.info("Storing task_uuid - will be used in other requests..")
                    task_uuid = body["uuid"]
                    response_stash["new_policy_osago"] = {"status": status, "task_uuid": task_uuid}
                else:
                    logger.warning("Status for POST /policy/osago is not 201, "
                                   "thus response data is not subject for save between API tests.")
                    logger.warning("This may have impact on /task/osago/uuid API test.")
            except Exception as e:
                logger.error("Exception accessing transaction['real']['body']: %s" % str(e))
                logger.error("Actual transaction:\n" + transaction)

    if transaction["name"] == \
            "API avia insurance \"Черехапа Страхование\" - справочник методов > " \
            "task: информация по задаче выписки полисов авиастрахования > " \
            "Метод GET /task/avia/id":
            logger.info("hooks after response POST /policy/avia")
            try:
                status = transaction["real"]["statusCode"]
                body = json.loads(transaction["real"]["body"])

                if status == 201:
                    logger.info("Storing task_uuid - will be used in other requests..")
                    task_uuid = body["id"]
                    response_stash["new_policy_avia"] = {"status": status, "task_uuid": task_uuid}
                else:
                    logger.warning("Status for POST /policy/avia is not 201, "
                                   "thus response data is not subject for save between API tests.")
                    logger.warning("This may have impact on /task/avia/uuid API test.")
            except Exception as e:
                logger.error("Exception accessing transaction['real']['body']: %s" % str(e))
                logger.error("Actual transaction:\n" + transaction)

