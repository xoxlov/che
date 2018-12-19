#!/usr/bin/env python3
# -*- coding: utf-8; -*-
#
# Test for cherehapa api testing
#
#План тестирования:
# Каждое взаимодействие с remote предполагает проверку ответа согласно json схеме
# step 1. Сделать API запрос на создание полиса POST /policy. Это создает задачу, сохранить её id.
#         Поля ответа на соответствие схеме уже проверяет dredd, так что не проверяем.
# step 2. Запустить через shell supervisor (если итак запущен то этот шаг не важен)
# step 3. Подождать timeout_for_policy_id_is_ready секунд на работу по созданию полиса выполняя шаг 4 каждые wait_step секунд
# step 4. API запрос GET /task/id , проверить что полис присутствует. 
#         Если есть - переход к 7 (предварительно сделав проверки схем ответа для незавершенной  и завершенной задачи).
#         Если нет - через shell запустить задачу на выполнение:
#         'php artisan process:start task_id' и выдать результат 'php artisan process:debug task_id' и 'php artisan process:error task_id'
#         Если информация по id полиса есть - убедиться, что в БД площадки есть такой полис.
#         Проверить вывод запрос на соответсвие схеме.
# step 5. Повтор пункта 3 (несколько раз запрашиваем policy_id) так как задача перезапускалась через shell.
# step 6. Если полиса нет - тест не пройден - завершаем с ошибкой.
# step 7. API запрос  GET /policy/id , проверка полей ответа на соответствие схеме, сохранение id файла полиса, проверка по БД что файл с таким id есть.
# step 8. API запрос  GET /file/id , проверка полей ответа на соответствие схеме. Убедиться, что файл скачивается. 
# step 9. API запрос  DELETE /policy/id , проверка полей ответа на соответствие схеме,  убедиться, что полис переводится в состояние удален в БД площадки.
# note:   incorrect access with wrong or no API key are not subject for this test
#
import requests
from time import sleep
import datetime
from dateutil.relativedelta import relativedelta

import common.logger as logger
from common.config_module import get_value_from_config, load
from common.randomize import get_random_string
from common.system import wait_and_count, execute_native_shell_command
from common.json_functions import validate_json_by_schema
from common.database import CheDb


###############################################################################
## functions
###############################################################################
def show_shell_debug_output(task_id):
    """Report to stdout 'php artisan <params>' output on API host for task_id

    :param task_id: task id from policy creation request
    :return:
    """
    logger.warning("Debug information for task %s" % task_id)
    debug_cmds = ['php artisan process:active',
                  'php artisan process:error ' + str(task_id),
                  'php artisan process:debug ' + str(task_id)
                  ]
    for cmd in debug_cmds:
        logger.print_empty_line()
        command = "cd /var/www/che-partner/public_html;" + cmd
        command_result = execute_native_shell_command(command)
        logger.warning("'%s' shows:" % cmd)
        logger.debug("\n%s" % command_result.get("output"))


def check_schema(url, schema_name, task_id, resp=None, success_status_code=200, method='GET'):
    """ checks reply from API for schema. If reply is omited (use only for GET method) - makes request 1st.
        param url: url used for response
        param schema_name: string to name the schema, must be same with the schema definition file name
        param task_id: task id as string, used to show debug output from API host
        param resp: the response to check against schema, None value allowed for GET - if none makes request first
        param success_status_code: the status code treated as success return code
        param method: http method used to fetch resp parameter
        return: True on success check. All other casess aborts execution
    """
    if not resp:
        logger.info("Requesting '%s'.." % url)
        resp = requests.get(url, headers=req_headers)
        resp.encoding = 'utf-8'
    else:
        logger.info("Checking '%s' response code.." % url)

    if resp.status_code == success_status_code:
        logger.success("Response code is %s" % resp.status_code)
        replyData = resp.json()
        context = "checking %s response from %s " % ( url, method)
        logger.info("Validating reply from %s %s for schema '%s'.." % (method, url, schema_name))
        validation_state = validate_json_by_schema(replyData, schema_name, context)
        if validation_state:
            logger.success("JSON reply matches schema")
            return True
        else:
            show_shell_debug_output(task_id)
            fail_report = "JSON reply does NOT match schema '%s' for %s from url '%s'" % (schema_name, method, url)
            logger.fail(fail_report)
            raise Exception(fail_report)
    else:
        logger.finishError("FAIL: Unexpected response code in reply from %s %s" % (method, url))
        logger.debug("Response text: \n%s" % resp.text)
        show_shell_debug_output(task_id)
        fail_report = "Unexpected response code in reply from %s %s" % (method, url)
        raise Exception(fail_report)


def get_policy_info_from_api(policy_id, task_id):
    """Request policy information for policy_id from API, check response with schema
    """
    url = base_url + '/policy/' + str(policy_id) + "?key=" + key
    logger.info("Making GET request to %s" % url)
    req = requests.get(url, headers=req_headers)
    req.encoding = 'utf-8'
    check_schema(url, 'policy_id_get_reply_schema', task_id, req)


def get_file_info_from_api(file_id, task_id):
    url = base_url + '/file/' + str(file_id) + "?key=" + key
    logger.info("Making GET request to %s" % url)
    response = requests.get(url, headers=req_headers)
    if response.status_code == 200:
        logger.success("Response code is 200")
        check_schema(url, 'file_id_get_reply_schema', task_id, response)
    else:
        logger.fail("Unexpected response code %s while getting file information" % response.status_code)
        logger.debug("Response:\n%s" % response.text)
        return False


def request_policy_id_from_api(task_id):
    url = base_url + '/task/' + str(task_id)
    logger.info("Requesting '%s'.." % url)
    response = requests.get(url, headers=req_headers)
    if response.status_code == 200:
        logger.success("Response code is 200")
        if 'policy' in response.json():
            data = response.json()['policy']
            policy_id = data[0]['id']
            logger.success("Got policy id = %s" % policy_id)
            return policy_id
        logger.warning("Response has no information about policy yet")
        return False
    logger.fail("Unexpected response code while making request to get policy id from task information")
    logger.debug("Response text:\n%s" % response.text)
    return False


def wait_till_policy_ready(task_id):
    """Continuously requests for policy id within timeout_for_policy_id_is_ready
    seconds waiting wait_step seconds between retries

    :param task_id: task id from policy creation request
    :return: policy_id or False if no policy available at last retry
    """
    wait_step = timeout_for_policy_id_is_ready / 15
    logger.info("Retrying  request_policy_id_from_api() within %s seconds with step %s.." % (timeout_for_policy_id_is_ready, wait_step))
    current = datetime.datetime.now()
    future = datetime.datetime.now() + datetime.timedelta(seconds=timeout_for_policy_id_is_ready)
    while current < future:
        wait_and_count(wait_step)
        current = datetime.datetime.now()
        policy_id = request_policy_id_from_api(task_id)
        if policy_id:
            return policy_id
    return False


def get_file_id_from_database(policy_id):
    query = "select fileId from policies where id=%s" % policy_id
    with CheDb() as db:
        query_result = db.execute_query(query)
        if len(query_result) == 1 and query_result[0][0]:
            logger.success("Got file id = %s" % query_result[0][0])
            return query_result[0][0]
        logger.error("Wrong results for query '%s':" % query)
        logger.debug(*query_result)
        return False


def send_request_to_delete_policy(policy_id, task_id):
    url = base_url + '/policy/' + str(policy_id) + "?key=" + key
    logger.info("Executing DELETE request: %s" % url)
    response = requests.delete(url, headers=req_headers)
    response.encoding = 'utf-8'
    check_schema(url, 'policy_id_delete_reply_schema', task_id, response, success_status_code=201, method='DELETE')


def is_policy_in_database(task_id, policy_id):
    with CheDb() as db:
        parent_task_id = db.find_task_id(task_id)[0]
        if parent_task_id:
            logger.success("Parent task %s was found successfully" % parent_task_id)
        else:
            logger.fail("Parent task %s was found successfully" % parent_task_id)
            return False
        child_task_id = db.get_task_id_list_to_create_policy(task_id)[0]
        if child_task_id:
            logger.success("Child task %s to create policy was found successfully" % child_task_id)
        else:
            logger.fail("Child task corresponding to parent task %s was found successfully" % parent_task_id)
            return False
        query = "select fileId from policies where taskId='%s' and id=%s" % (child_task_id, policy_id)
        query_result = db.execute_query(query)
        if query_result and query_result[0][0]:
            file_id = query_result[0][0]
            logger.success("Policy file id = %s was found successfully" % file_id)
        else:
            logger.fail("File corresponding to task %s was found successfully" % child_task_id)
            return False
        return True


def is_policy_cancelled_in_database(policy_id):
    query = "select dateCancelled from policies where id=%s" % policy_id
    with CheDb() as db:
        query_result = db.execute_query(query)
        if len(query_result) == 1:
            if query_result[0][0]:
                logger.success("'dateCancelled' for policy id %s is '%s'" % (policy_id, query_result[0][0]))
                return True
            logger.fail("'dateCancelled' for policy id %s is not Null" % policy_id)
            return False
        logger.error("Wrong results for query '%s':" % query)
        logger.debug(*query_result)
        return False


def is_policy_file_deleted_in_database(policy_id, file_id):
    query = "select dateDeleted from files where id=%s" % file_id
    with CheDb() as db:
        query_result = db.execute_query(query)
        if len(query_result) == 1:
            if query_result[0][0]:
                logger.success("'dateDeleted' for file id %s is '%s'" % (policy_id, query_result[0][0]))
                return True
            logger.fail("'dateDeleted' for file id %s is not Null" % file_id)
            return False
        logger.error("Wrong results for query '%s':" % query)
        logger.debug(*query_result)
        return False


###############################################################################
#### settings, globals and config values
###############################################################################
api_timeouts = load("config/api.json")["timeouts"]
timeout_for_policy_file_is_ready = api_timeouts[u'wait_for_policy_file_is_ready']
timeout_for_policy_id_is_ready = api_timeouts[u'wait_for_policy_id_is_ready']
timeout_for_policy_marked_as_deleted = api_timeouts[u'wait_for_policy_marked_as_deleted']
# how long to wait for supervisor to finish its start/reload
timeout_supervisor_reload_time = 5

# параметры для post запроса
base_url = "http:" + get_value_from_config("[u'api'][u'url']")
key = get_value_from_config("[u'api'][u'key']")

# prepare values
config = load("config/acceptance_vzr.json")

days_start_from_now = config[u'insurance'][u'days_from_now_to_start']
days_to_insure = config[u'insurance'][u'insuredDays']
date_start = datetime.date.today() + datetime.timedelta(days=days_start_from_now)
# для date_end: 1 день когда дата начала = дате конца страховки, т.е. стартовая считается всегда
date_end = date_start + datetime.timedelta(days=days_to_insure - 1)

tourist_birthday = datetime.datetime.today() - relativedelta(years=int(config[u'traveller'][u'age']))
tourist_birthday = tourist_birthday.strftime("%d.%m.%Y").encode('utf-8')

# get buyer email from config file or generate it
buyer_email = config[u'buyer'][u'email'].encode('utf-8')
if not buyer_email:
    random_base = get_random_string()
    random_suffix = get_random_string(size=2)
    random_domain = random_base + '.' + random_suffix
    buyer_email = "fakemail@" + random_domain

auth = get_value_from_config("['authorization']", "config/api.json")
req_headers = {
    'Authorization': auth,
    'key': key
}
req_data = {
    'currency': 'eur',
    'dateStart': date_start.strftime("%d.%m.%Y"),
    'dateEnd': date_end.strftime("%d.%m.%Y"),
    'insuredDays': days_to_insure,
    'country[]': 'italy',
    'service[medicine]': 50000,
    'service[aviaCargo]': 1500,
    'service[accident]': 0,
    'service[civilLiability]': 0,
    'service[urgentStomatology]': 1,
    'tourist[0][firstName]': config[u'traveller'][u'first_name'].encode('utf-8'),
    'tourist[0][lastName]': config[u'traveller'][u'last_name'].encode('utf-8'),
    'tourist[0][hidden]': 0,
    'tourist[0][birthday]': tourist_birthday,
    'insurer[name]': config[u'buyer'][u'first_name'].encode('utf-8'),
    'insurer[lastName]': config[u'buyer'][u'last_name'].encode('utf-8'),
    'insurer[secondName]': config[u'buyer'][u'middle_name'].encode('utf-8'),
    'insurer[nameRU]': 'required',
    'insurer[lastNameRU]': '%B6%D0%B5%D0%B7%D0%B8%D0%BD%D1%81%D0%BA%D0%B8%D0%B9',
    'insurer[secondNameRU]': '%B8%D0%BC%D1%83%D0%BB%D1%8C%D0%B4%D0%B8%D0%BD%D0%BE%D0%B2%D0%B8%D1%87',
    'insurer[phone]': config[u'buyer'][u'phone'].encode('utf-8'),
    'insurer[email]': buyer_email,
    'insuranceProduct[]': 9, # alfa страхование
    'paymentSystem': 7,
    'card[number]': config[u'card'][u'numberRaw'].encode('utf-8'),
    'card[month]': config[u'card'][u'month'],
    'card[year]': config[u'card'][u'year'],
    'card[cvc]': config[u'card'][u'cvv'],
    'card[holder]': config[u'card'][u'holder'].encode('utf-8'),
    'sport[]': 'waterAerobics',
    'key': key,
    'marker': '123qwe',
    'partnerId': 1,
    '_method': 'post'
}


###############################################################################
# main test function
###############################################################################
def test_che_api():
    test_name = "api_check"
    logger.startTest(test_name)

    logger.start("STEP 1: POST /policy")
    url = base_url + '/policy'
    logger.info("Making POST request to %s to create a policy.." % url)
    resp = requests.post(url, headers=req_headers, data=req_data)
    resp.encoding = 'utf-8'
    if resp.status_code == 201:
        logger.success("Response code is 201")
        task_id = resp.json()['task']['id']
        logger.success("Task with id = %s created" % task_id)
        schema = "task_id_get_reply_schema_task_not_finished"
        url = "%s/task/%s" % (base_url, task_id)
        check_schema(url, schema, task_id)
    else:
        logger.fail("Unexpected response code while making request to create policy: %s" % resp.status_code)
        logger.finishError('STEP 1')
        logger.debug("request text: \n%s" % resp.text)
        return False
    logger.finishSuccess('STEP 1')

    logger.start("STEP 2: Make sure that supervisor is running")
    command = "sudo service supervisor start"
    # we shouldn't quit on error - supervisor may appear to be started other way via ansible
    execute_native_shell_command(command, exit_on_error=False)
    logger.finishSuccess("STEP 2: Service is running")
    sleep(timeout_supervisor_reload_time)

    logger.start("STEP 3: wait for policy..")
    policy_id = wait_till_policy_ready(task_id)
    logger.finishSuccess("STEP 3")

    logger.start("STEP 4: API request GET /task/id to check if policy is created")
    if policy_id:
        # here we have policy in responce from GET /task/id , time to check response to match schema, but the task is in unfinished state.
        schema = "task_id_get_reply_schema_task_not_finished"
        url = "%s/task/%s" % (base_url, task_id)
        check_schema(url, schema, task_id)
        logger.info("Okay to jump to step 7")
    else:
        logger.warning("There is still no policy reported by API call GET /task/%s" % task_id)
        show_shell_debug_output(task_id)
        logger.info("Trying to start this task manually..")
        cmd = 'php artisan process:start %s' % task_id
        logger.warning("'%s' shows:" % cmd)
        command = "cd /var/www/che-partner/public_html;" + cmd
        command_result = execute_native_shell_command(command, exit_on_error=False)
        logger.info(command_result.get("output"))

        logger.start("STEP 5: wait for policy..")
        policy_id = wait_till_policy_ready(task_id)
        logger.finishSuccess("STEP 5")

        logger.start("STEP 6: last check for policy")
        if policy_id:
            logger.success("Got policy id = %s" % policy_id)
            # policy is created, check response to match schema, but task may still be not finished - using weaker schema
            schema = "task_id_get_reply_schema_task_not_finished"
            url = "%s/task/%s" % (base_url, task_id)
            check_schema(url, schema, task_id)
            logger.finishSuccess("STEP 6")
        else:
            show_shell_debug_output(task_id)
            logger.error("STEP 6: No policy reported by API request 'GET /task/%s'" % task_id)
            logger.finishFail("api check")
            return False

    wait_and_count(timeout_for_policy_id_is_ready, "task completed")
    # policy is already created and finished, check response to match schema for finished task
    schema = "task_id_get_reply_schema_task_is_finished"
    url = "%s/task/%s" % (base_url, task_id)
    check_schema(url, schema, task_id)
    logger.finishSuccess("STEP 4")

    logger.start("STEP 7: get /policy/id + check response")
    get_policy_info_from_api(policy_id, task_id)
    logger.info("Checking policy is in DB..")
    if not is_policy_in_database(task_id, policy_id):
        logger.finishFail("No policy or task in database")
        logger.finishFail("Test '%s' overall result" % test_name)
        show_shell_debug_output(task_id)
        return False
    logger.finishSuccess("STEP 7")

    logger.start("STEP 8: get /file/id + check response")
    logger.info("Getting id from DB to check /file/id API..")
    current = datetime.datetime.now()
    future = datetime.datetime.now() + datetime.timedelta(seconds=timeout_for_policy_file_is_ready)
    file_id = 0
    while current < future:
        current = datetime.datetime.now()
        file_id = get_file_id_from_database(policy_id)
        if file_id:
            get_file_info_from_api(file_id, task_id)
            break
        wait_and_count(timeout_for_policy_file_is_ready, "policy file to be ready")
    if not file_id:
        logger.finishFail("STEP 8: File id is not zero after %s seconds" % timeout_for_policy_file_is_ready)
        show_shell_debug_output(task_id)
        logger.debug("task details API request shows:")
        request_policy_id_from_api(task_id)
        logger.debug("policy details API request shows:")
        get_policy_info_from_api(policy_id, task_id)
        logger.finishFail("Test '%s' overall result" % test_name)
        return False
    logger.finishSuccess('STEP 8')

    logger.start("STEP 9: delete /policy/id + check response + check in sql")
    send_request_to_delete_policy(policy_id, task_id)
    wait_and_count(timeout_for_policy_marked_as_deleted, "policy to be deleted")
    if is_policy_cancelled_in_database(policy_id) \
            and is_policy_file_deleted_in_database(policy_id, file_id):
        logger.finishSuccess("STEP9: Deletion successful (policy id=%s, file id=%s)" % (policy_id, file_id))
        logger.finishSuccess("Test '%s' overall result" % test_name)
    else:
        logger.finishFail("STEP9: policy deletion is not complete")
        show_shell_debug_output(task_id)
        logger.info("file information via API:")
        get_file_info_from_api(file_id, task_id)
        logger.info("task details API request:")
        request_policy_id_from_api(task_id)
        logger.info("policy details API request:")
        get_policy_info_from_api(policy_id, task_id)
        logger.finishFail("Test '%s' overall result" % test_name)


if __name__ == '__main__':
    test_che_api()
