# -*- coding: utf-8; -*-
# to see intermediate output during execution run 'pytest -s <test_script.py>'
#
# План тестирования:
# Каждый запрос к remote предполагает проверку ответа согласно json схеме
# 1. Проверить, что курсы валют установлены на текущий день.
# 2. Сделать API запрос на создание полиса POST /policy.
#    Получить идентификатор задачи task_id.
#    Замечание: поля ответа на соответствие схеме проверяет dredd тест.
# 3. Запустить supervisor через shell (если уже запущен, то этот шаг не важен).
# 4. Подождать, пока полис не будет создан, получить policy_id.
# 5. Проверить наличие policy_id, если его нет (полис недоступен), тогда:
#     - перезапустить задачу создания полиса;
#     - подождать, пока полис не будет создан, получить policy_id.
# 6. Проверить наличие policy_id, если полиса нет - тест не пройден.
# 7. Проверить, что БД содержит записи о выполненных задачах.
# 8. Проверить, что БД содержит записи о полисе.
# 9. Проверить, что БД содержит записи о файле полиса, получить file_id.
# 10. Проверить, что файл с file_id доступен.
# 11. Послать запрос на удаление полиса.
#    Проверить, что полис переводится в состояние "удален" в БД.
# Note: incorrect access with wrong or no API key are not subject for this test
import string
import datetime
from dateutil.relativedelta import relativedelta
from time import sleep

from common.config_module import get_value_from_config, load
from common.system import execute_native_shell_command
from common.json_functions import validate_json_by_schema
from common.randomize import make_random_email
from common.request import send_http_request
from common.database import CheDb
from common.currency import verify_currency_is_set_for_today


base_url = "http:{}".format(get_value_from_config("['api']['url']"))
api_key = get_value_from_config("['api']['key']")
request_headers = {
    "Authorization":
        get_value_from_config("['authorization']", "config/api.json"),
    "key": api_key,
}

api_timeouts = load("config/api.json")["timeouts"]
timeout_for_policy_file_is_ready = \
    api_timeouts['timeout_policy_file_is_ready']
timeout_for_policy_id_is_ready = \
    api_timeouts['timeout_policy_id_is_ready']
timeout_for_policy_marked_as_deleted = \
    api_timeouts['timeout_policy_marked_as_deleted']
timeout_supervisor_reload_time = \
    api_timeouts['timeout_supervisor_reload_time']
timeout_between_requests = \
    api_timeouts['timeout_between_http_requests']


def test_create_verify_delete_policy():
    verify_currency_is_set_for_today()
    task_id = send_request_to_create_policy_and_get_task_id()
    make_supervisor_service_run()
    policy_id = wait_for_policy_ready_and_get_policy_id(task_id)
    if not policy_id:
        restart_artisan_task(task_id)
        policy_id = wait_for_policy_ready_and_get_policy_id(task_id)
    assert policy_id, "No policy created by task '{}'".format(task_id)
    wait_for_task_completed(task_id)
    verify_policy_tasks_in_database(task_id)
    verify_policy_created_successfully(policy_id)
    file_id = get_file_id_by_policy_id(task_id, policy_id)
    verify_file_is_available_through_api(task_id)
    delete_policy_id_in_database(policy_id, file_id)


def send_request_to_create_policy_and_get_task_id():
    print(" > Send request to create policy..")
    url = '{}/policy'.format(base_url)
    config = load("config/acceptance_vzr.json")

    days_start_from_now = config["insurance"]["days_from_now_to_start"]
    days_to_insure = config["insurance"]["insuredDays"]
    date_start = \
        datetime.date.today() + datetime.timedelta(days=days_start_from_now)
    date_end = date_start + datetime.timedelta(days=days_to_insure - 1)

    tourist_birthday = \
        datetime.datetime.today() \
        - relativedelta(years=int(config["traveller"]["age"]))
    tourist_birthday = tourist_birthday.strftime("%d.%m.%Y")
    buyer_email = config["buyer"]["email"] or make_random_email()

    # Note: insurance product #184 is used when creating policy, it corresponds
    #   to "RESO A" product (table "insuranceProducts")
    # Note: payment system "cashless" (id=7) is used to pay the policy
    request_data = {
        "currency": "eur",
        "dateStart": date_start.strftime("%d.%m.%Y"),
        "dateEnd": date_end.strftime("%d.%m.%Y"),
        "insuredDays": days_to_insure,
        "country[]": "italy",
        "service[medicine]": 50000,
        "service[aviaCargo]": 1500,
        "service[accident]": 0,
        "service[civilLiability]": 0,
        "service[urgentStomatology]": 1,
        "tourist[0][firstName]": config["traveller"]["first_name"],
        "tourist[0][lastName]": config["traveller"]["last_name"],
        "tourist[0][hidden]": 0,
        "tourist[0][birthday]": tourist_birthday,
        "insurer[name]": config["buyer"]["first_name"],
        "insurer[lastName]": config["buyer"]["last_name"],
        "insurer[secondName]": config["buyer"]["middle_name"],
        "insurer[nameRU]": config["buyer"]["first_name_rus"],
        "insurer[lastNameRU]": config["buyer"]["last_name_rus"],
        "insurer[secondNameRU]": config["buyer"]["middle_name_rus"],
        "insurer[phone]": config["buyer"]["phone"].strip(string.punctuation),
        "insurer[email]": buyer_email,
        "insuranceProduct[]": 184,
        "paymentSystem": 7,
        "card[number]": config["card"]["numberRaw"],
        "card[month]": config["card"]["month"],
        "card[year]": config["card"]["year"],
        "card[cvc]": config["card"]["cvv"],
        "card[holder]": config["card"]["holder"],
        "sport[]": "waterAerobics",
        "key": get_value_from_config("['api']['key']"),
        "marker": "123qwe",
        "partnerId": 1,
        "_method": "post"
    }
    response = send_http_request(
        url, "post", headers=request_headers, data=request_data)
    assert response.status_code == 201, \
        "Unexpected response:\n{}" \
        "".format(response.text)
    task_id = response.json()['task']['id']
    assert task_id
    verify_task_id_schema_is_correct(
        schema_name="task_id_get_reply_schema_task_not_finished",
        task_id=task_id)
    return task_id


def make_supervisor_service_run():
    print(" > Make supervisor servise run..")
    command = "sudo service supervisor start"
    # shouldn't quit on error - supervisor may be started other way via ansible
    execute_native_shell_command(command, exit_on_error=False)
    sleep(timeout_supervisor_reload_time)


def wait_for_policy_ready_and_get_policy_id(task_id):
    print(" > Wait for policy to be ready..")
    current = datetime.datetime.now()
    future = \
        datetime.datetime.now() \
        + datetime.timedelta(seconds=timeout_for_policy_id_is_ready)
    policy_id = False
    while current < future:
        sleep(timeout_between_requests)
        current = datetime.datetime.now()
        # request policy_id from api
        url = '{}/task/{}'.format(base_url, task_id)
        response = send_http_request(url, "get", headers=request_headers)
        assert response.status_code == 200, \
            "Unexpected response while requesting policy id from task:\n{}" \
            "".format(response.text)
        if 'policy' in response.json():
            data = response.json()['policy']
            policy_id = data[0]['id']
            break
    if policy_id:
        verify_task_id_schema_is_correct(
            schema_name="task_id_get_reply_schema_task_not_finished",
            task_id=task_id)
    return policy_id


def restart_artisan_task(task_id):
    print(" > Restart artisan process to restart policy creation task..")
    cmd = 'php artisan process:start {}'.format(task_id)
    command = "cd /var/www/che-partner/public_html;" + cmd
    execute_native_shell_command(command, exit_on_error=False)


def wait_for_task_completed(task_id):
    print(" > Wait for task to be completed..")
    current = datetime.datetime.now()
    future = \
        datetime.datetime.now() \
        + datetime.timedelta(seconds=timeout_for_policy_id_is_ready)
    schema_name = "task_id_get_reply_schema_task_is_finished"
    while current < future:
        sleep(timeout_between_requests)
        current = datetime.datetime.now()
        url = "{}/task/{}".format(base_url, task_id)
        response = send_http_request(url, "get", headers=request_headers)
        is_response_code_ok = response.status_code == 200
        is_schema_ok = validate_json_by_schema(
            response.json(), schema_name, abort_on_exception=False)
        if is_response_code_ok and is_schema_ok:
            break
    verify_task_id_schema_is_correct(schema_name=schema_name, task_id=task_id)


def verify_task_id_schema_is_correct(schema_name, task_id):
    url = "{}/task/{}".format(base_url, task_id)
    response = send_http_request(url, "get", headers=request_headers)
    assert response.status_code == 200, \
        "Unexpected response while checking task {}:\n{}" \
        "".format(url, response.text)
    assert validate_json_by_schema(response.json(), schema_name), \
        "JSON reply does NOT match schema '{}' for 'GET' from url '{}'" \
        "".format(schema_name, url)


def verify_policy_tasks_in_database(task_id):
    print(" > Verify policy tasks in database..")
    with CheDb() as db:
        parent_task_id = db.find_task_id(task_id)[0]
        assert parent_task_id, "Parent task is not found in DB"
        child_task_id = db.get_task_id_list_to_create_policy(task_id)[0]
        assert child_task_id, \
            "Child task for parent task {} is not found in DB" \
            "".format(parent_task_id)


def verify_policy_created_successfully(policy_id):
    print(" > Verify policy created successfully..")
    url = '{}/policy/travel/{}?key={}'.format(base_url, policy_id, api_key)
    response = send_http_request(url, "get", headers=request_headers)
    assert response.status_code == 200, \
        "Unexpected response while getting file information:\n{}" \
        "".format(url, response.text)
    schema_name = "policy_id_get_reply_schema"
    assert validate_json_by_schema(response.json(), schema_name), \
        "JSON reply does NOT match schema '{}' for 'GET' from url '{}'" \
        "".format(schema_name, url)


def get_file_id_by_policy_id(task_id, policy_id):
    print(" > Get file id for policy from DB..")
    current = datetime.datetime.now()
    future = \
        datetime.datetime.now() \
        + datetime.timedelta(seconds=timeout_for_policy_file_is_ready)
    file_id = 0
    while current < future:
        current = datetime.datetime.now()
        file_id = get_file_id_from_database(policy_id)
        if file_id:
            break
        sleep(timeout_between_requests)
    assert file_id, \
        "Cannot get file_id from DB (task_id={}, policy_id={})" \
        "".format(task_id, policy_id)
    return file_id


def get_file_id_from_database(policy_id):
    query = "select fileId from policies where id='{}'".format(policy_id)
    with CheDb() as db:
        query_result = db.execute_query(query)
        if len(query_result) == 1 and query_result[0][0]:
            return query_result[0][0]
        return False


def verify_file_is_available_through_api(task_id):
    print(" > Verify policy file is available..")
    url = '{}/task/{}'.format(base_url, task_id)
    response = send_http_request(url, "get", headers=request_headers)
    assert response.status_code == 200, \
        "Unexpected response while getting file link:\n{}" \
        "".format(url, response.text)
    response_json = response.json()
    assert response_json["order"]["downloadUrl"]
    assert response_json["policy"][0]["fileLink"]


def delete_policy_id_in_database(policy_id, file_id):
    print(" > Delete policy in database..")
    send_request_to_delete_policy(policy_id)
    sleep(timeout_for_policy_marked_as_deleted)
    verify_policy_is_cancelled_in_database(policy_id)
    verify_policy_file_is_deleted_in_database(policy_id, file_id)


def send_request_to_delete_policy(policy_id):
    url = '{}/policy/travel/{}?key={}'.format(base_url, policy_id, api_key)
    response = send_http_request(url, "get", headers=request_headers)
    delete_url = response.json()["policy"]["deleteUrl"]
    response = send_http_request(delete_url, "delete", headers=request_headers)
    assert response.status_code == 201, \
        "Unexpected response while deleting policy {}:\n{}" \
        "".format(url, response.text)
    schema_name = "policy_id_delete_reply_schema"
    assert validate_json_by_schema(response.json(), schema_name), \
        "JSON reply does NOT match schema '{}' for 'DELETE' from url '{}'" \
        "".format(schema_name, url)


def verify_policy_is_cancelled_in_database(policy_id):
    query = "select dateCancelled from policies where id='{}'" \
            "".format(policy_id)
    with CheDb() as db:
        query_result = db.execute_query(query)
    assert len(query_result) == 1
    date_cancelled = query_result[0]
    assert date_cancelled, \
        "'dateCancelled' for policy id {} is not Null".format(policy_id)


def verify_policy_file_is_deleted_in_database(policy_id, file_id):
    query = "select dateDeleted from files where id='{}'".format(file_id)
    with CheDb() as db:
        query_result = db.execute_query(query)
    assert len(query_result) == 1
    date_deleted = query_result[0]
    assert date_deleted, \
        "'dateDeleted' for file id {} is not Null for policy '{}'" \
        "".format(file_id, policy_id)
