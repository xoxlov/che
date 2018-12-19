#!/usr/bin/python -u
# -*- Mode: Python; coding: utf-8; indent-tabs-mode: t; c-basic-offset: 4; tab-width: 4 -*1
#
# -u option for python makes printing unbuffered.
#
# Тестирование API партнерского кабинета.
#
# Тест предполагает, что он запущен в единственном экземпляре и БД уже развернута (соответствует тому, что в config.json),
# поскольку тесты могут запускаться откуда угодно все создаваемые пользователи рандомные, очень маловероятно что данные
# в БД от двух тестов из разных мест пересекуться (на будущее: если потребуется блокировка одновременной работы, то её
#  можно только внутри БД создавать)
#
# FIXME: поделить тест на несколько согласно ф-лу API 
# FIXME: move requests w/ try catch to a function + move it to common_test_functions: result is easier to read code
# FIXME: rename variables delivered from config by cfg_* mask
#
###
#План тестирования:
#
# Для авторизации используется админский аккаунт, он точно во всех сборках есть и неизменный, 
# универсальный и является одновременно и покупательским и партнерским, из v_user и логин и email должны срабатывать для входа
# Для проверок создается тестовый пользователь с паролем как у cherehapa.
#
# Каждое взаимодействие с remote предполагает проверку ответа согласно json схеме.
#
# step 0: Подготовка:
#         *. подключиться к БД, проверить что используемый пользователь из конфига там есть,
#         *. проверить встроенные в скрипт схемы (validate_built_in_schemas() - если добавляете схемы - впишите туда)
# step 1. Проверка авторизации: 
#         *. нельзя зайти с случайными логином и паролем 
#         *. нельзя зайти с неверным паролем от правильного пользователя
#         *. нельзя зайти с пустым именем пользователя, но правильным паролем одного из пользователей
#         *. нельзя зайти с пустым паролем для существующего пользователя
#         *. нельзя зайти с пустым паролем для отсутствующего пользователя
#         *. нельзя зайти с пустым паролем и пустым пользователем
#         *. ответы соответствуют json схемам для успешного входа и для отказа во входе
#         *. можно зайти с правильным логином и паролем,
# step 2. Проверка сервиса восстановления пароля.
#         *. Создать тестового пользователя для тестирования смены пароля с заведомо известным паролем.
#         *. запросить восстановление пароля, проверить ответ 
#         *. удалить тестового пользователя
#         *. Создать тестового пользователя для тестирования смены пароля с заведомо известным паролем.
#         *. попытаться cделать sql инъекции при запросе восстановления пароля, убедится, что ответ как при ошибке
#         *. убедиться что в БД нет артифакта-вставки из sql инъекции
#         *. Удалить тестового пользователя.
#         *. Проверить почту на temp-mail.ru , убедиться что email пришёл и соответсвует требованиям из config.json
# step 3. Проверка отчета о количестве зарегистрированных в системе партнеров.
#         *. Запросить к-во в БД
#         *. Запросить API, свалидировав по схеме ответ
#         *. Сравнить результат запросов.
# step 4. 
# step 5. 
# step 6. 
# step 7. 
# step 8. 
# step 9. 
###
#
# (c) cherehapa , (c) grey-olli@ya.ru 2016

# get divison of integers to be float , imports from __future__ must stay at the beginning
from __future__ import division

# probotics related
import unittest
from proboscis import test

## encoding details, needed to trace problem printing unicode strings to console
#print "DEBUG: using console encoding: ", sys.stdout.encoding

# import test configuration
import config as configModule
config = configModule.load()

from tempmail import TempMail
import mysql.connector
import exceptions

import random
import sys

# http requests handling
import requests
import urllib

# dates/time generation
import datetime
from time import time
from time import strptime
from time import mktime

import json
import jsonschema

# guess encoding
import unicodedata

# function common for tests, new code
import common.common_logger as logger
from common.common_randomize import get_random_int_from_set
from common.common_randomize import get_random_spacechar_filled_string
from common.common_randomize import get_random_string

# functions common for tests, legacy code, FIXME: replace w/ similar code in ./common/*.py
import common_test_functions
from common_test_functions import check_mail_contents
from common_test_functions import get_SQL_injection_strings
from common_test_functions import report_SQL_injection_status
from common_test_functions import is_user_in_DB
from common_test_functions import open_validate_mysql_connection
from common_test_functions import validate_json_schema
from common_test_functions import send_http_request
from common_test_functions import validate_json_by_schema
from common_test_functions import dump_request_params

## json схемы для проверок, когда добавляете схему - добавляйте её проверку в validate_built_in_schemas() (для удобства - в том же порядке что и import'ы)
from common_json_schemas import failed_AddPartnUser_reply_schema
from common_json_schemas import okay_partnercount_reply_schema
from common_json_schemas import accepted_logon_reply_schema
from common_json_schemas import no_key_reply_schema
from common_json_schemas import failed_logon_reply_schema
from common_json_schemas import accepted_authrec_reply_schema
from common_json_schemas import failed_authrec_reply_schema

# variables common for tests 
from common_test_functions import AllOK_PrintPrefix
from common_test_functions import Warn_PrintPrefix
from common_test_functions import ERR_PrintPrefix
from common_test_functions import ExtraInfo_PrintPrefix
from common_test_functions import FinalFail_PrintPrefix


################################################################################
## functions
################################################################################
@test(groups=["api"])
def lk_api_check():
    """ основная ф-я тестирования всех API вызовов партнерского кабинета. """

    global fake_user
    global testuser
    global glob_user2inject
    global glob_test_start_time
    global glob_test_result_state

    ### начали
    test_start_datetime = datetime.datetime.now()
    glob_test_start_time = time()
 
    print AllOK_PrintPrefix + "Starting " + glob_test_name + " test.. "
    print AllOK_PrintPrefix + "Start: --> ", test_start_datetime.strftime("%Y-%m-%d.%H:%M:%S")

    print AllOK_PrintPrefix + "*** STEP 0 .."
    print AllOK_PrintPrefix + "[+] Self check.."
    validate_built_in_schemas()
    logger.success("Self check.")

    # get db_conn
    db_conn = open_validate_mysql_connection()

    print AllOK_PrintPrefix + "[+] Checking DB fits our needs.."
    confirm_user_in_DB(db_conn,cfg_admin_user)
    confirm_no_apikey_in_DB(db_conn,glob_fake_key)
    logger.success("DB fits our needs")

    # Step 1: base auth api
    print AllOK_PrintPrefix + "*** STEP 1 .."
    print AllOK_PrintPrefix + "[+] Checking authorization API .."
    check_logon_api(db_conn)
    logger.success("logon API works.")

    # Step 2:  
    print AllOK_PrintPrefix + "*** STEP 2 .."
    print AllOK_PrintPrefix + "[+] Checking change authorization API .."
    check_change_auth_api(db_conn,glob_email)
    logger.success("change authorization via API works.")
    
    # Step 3: 
    print AllOK_PrintPrefix + "*** STEP 3 .."
    print AllOK_PrintPrefix + "[+] Checking partner-count API request .."
    check_partnercount_api(db_conn)
    logger.success("partner-count via API works.")

    # Step 4: 
    print AllOK_PrintPrefix + "*** STEP 4 .."
    print AllOK_PrintPrefix + "[+] Checking add user w/ partner account API request .."
    check_add_partnered_user(db_conn,glob_test_start_time)
    logger.success("add partnered user via API works.")

    ## Step 5:
    #print AllOK_PrintPrefix + "*** STEP 5 .."
    #
    ## Step 6:
    #print AllOK_PrintPrefix + "*** STEP 6 .."
    #
    ## Step 7:
    #print AllOK_PrintPrefix + "*** STEP 7 .."

    # finish here.
    db_conn.close()

    test_end_time = time()
    test_spent_seconds = round(test_end_time - glob_test_start_time,1)

    print AllOK_PrintPrefix + "test took ", test_spent_seconds,"seconds."
    print AllOK_PrintPrefix + "End: --> ",  datetime.datetime.now().strftime("%Y-%m-%d.%H:%M:%S")
    if glob_test_result_state:
        print AllOK_PrintPrefix + "Test " + glob_test_name + " passed."
    else:
        FailReport = FinalFail_PrintPrefix + glob_test_name + "test failed: errors encountered while execution."
        assert False,FailReport
        exit(253)


def get_available_partnered_user_types() :
    """ returns array with user types available for cherehapa.ru users treated as partners.
    """
    return ['individual', 'legal'] #  only two available values: legal,individual (legal - юр лицо, individual -физ лицо)


def lk_api_login(user, passwd, context_message=False, verbose=False):
    """получает на вход параметры пользователя для входа через API ЛК, проверяет ответ на валидность согласно json схеме

    :param user:
    :param passwd:
    :param context_message:
    :param verbose: optional verbosity flag
    :return: [True,"login_token_string"] если успешно авторизовалось
             [False,"error json" ] в противном случае
    """
    context_message = context_message or "requesting login."
    from common_json_schemas import accepted_logon_reply_schema
    from common_json_schemas import failed_logon_reply_schema
    cfg_api_url = config[u'host'][u'apiUrl'].encode('utf-8')
    cfg_api_key = config[u'host'][u'key'].encode('utf-8')

    req_url = cfg_api_url + "/token?key=" + cfg_api_key
    headers = {'Authorization': 'Basic YXBhaGVyZWhjOjlzQmJPeTZk','key': cfg_api_key}
    req_params = {"login": user, "password": passwd}
    resp = send_http_request(req_url,'post', context_message, headers=headers, data=req_params)
    js = resp.json()
    if resp.status_code == 200 :
        logged_in_status=True
        schema=accepted_logon_reply_schema
        schema_name="accepted_logon_reply_schema"
        if verbose:
            logger.info("  .. login for user '%s' with password '%s' passed. Response code %s. Context: %s" % (user, passwd, resp.status_code, context_message))
    else:
        logged_in_status=False
        schema=failed_logon_reply_schema
        schema_name="failed_logon_reply_schema"
        if verbose:
            logger.info("  .. login for user '%s' with password '%s' passed. Response code %s. Context: %s" % (user, passwd, resp.status_code, context_message))
    json_functions.validate_json_by_schema(js, schema, schema_name, context_message, verbose)
    return [True, js['data']] if logged_in_status else [False, js['error']]


def has_sql_sensitive(str2check):
    """ получает на вход строку, проверяет её на наличие некоторых символов которые могли бы изменить SQL запрос.
        Если находит - возвращает True , иначе False
        нужна чтобы случайно своим тестом не устроить себе SQL инъекцию - следует использовать в ф-ях работающих с БД.

    :param str2check:
    :return:
    """
    restricted_chars = ["'", "(", ")", "=", "/", "\\", chr(0xbf), chr(0x27), "%", "*", ";"]
    for restricted in restricted_chars :
        if restricted in str2check:
            return True
    return False


def validate_built_in_schemas():
    """ проверяет встроенные в скрипт схемы на ошибки, останавливает тест если что-то не так. """

    # вставьте сюда пары (схема,"cхема") если добавите в скрипт новую схему
    for schema2validate, schema_name in [(failed_AddPartnUser_reply_schema, "failed_AddPartnUser_reply_schema"),
                                         (okay_partnercount_reply_schema, "okay_partnercount_reply_schema"),
                                         (accepted_logon_reply_schema, "accepted_logon_reply_schema"),
                                         (no_key_reply_schema, "no_key_reply_schema"),
                                         (failed_logon_reply_schema, "failed_logon_reply_schema"),
                                         (accepted_authrec_reply_schema, "accepted_authrec_reply_schema"),
                                         (failed_authrec_reply_schema, "failed_authrec_reply_schema")
                                         ]:
        validate_json_schema(schema2validate, schema_name)


def check_tokens_are_unique():
    """ проверяет что token'ы от многократных логинов уникальны. """

    global glob_test_result_state
    print AllOK_PrintPrefix + " [+] Looking for duplicates.."
    # количество одновременных логинов не ограничено, каждый логин имеет уникальный token авторизации
    tokens = []
    print AllOK_PrintPrefix + "     .. making", retry_logon, "logon attempts and collecting tokens to compare.."
    for index in range(retry_logon):
        state, string = lk_api_login(cfg_admin_user, cfg_admin_user_passwd, suppress_output=True)
        if not state:
            FailReport = FinalFail_PrintPrefix + glob_test_name + "test failed: failed to login w/ predefined user/password pair available in DB: '" + cfg_admin_user + "' / '" + cfg_admin_user_passwd + "'"
            assert False, FailReport
            exit(111)  # shouldn't reach this.
        else:
            tokens.append(string)

    size = len(tokens)
    print AllOK_PrintPrefix + "     .. passed: total", size, "tokens collected within", retry_logon, "attempts."
    failing_pairs = []
    for index1 in range(size):
        has_duplicates = False
        dupe_points = [index1]
        for index2 in range(index1, size):
            if index1 == index2:
                continue
            if tokens[index1] == tokens[index2]:
                has_duplicates = True
                dupe_points.append(index2)
        if has_duplicates:
            already_pushed = False
            for index3 in range(len(failing_pairs)):
                if failing_pairs[index3][0] == tokens[index1]:
                    already_pushed = True
            if not already_pushed:
                failing_pairs.append([tokens[index1], dupe_points])

    if len(failing_pairs):
        total = len(tokens)
        unique = len(failing_pairs)
        dupes = total - unique
        print ERR_PrintPrefix + "    Duplicate tokens returned for repeatative logins - only", unique, "are unique of", total, "."

        # show the most repeating token as an example
        most_rep_index = 0;
        last_index = unique - 1
        for index, pair in enumerate(failing_pairs):
            len_curr = len(pair[1])
            len_max = len(failing_pairs[most_rep_index][1])
            if index == last_index:
                len_near = len(failing_pairs[index - 1][1])
            else:
                len_near = len(failing_pairs[index + 1][1])
            if len_curr > len_near and len_curr > len_max:
                most_rep_index = index
        print ERR_PrintPrefix + "    For example token: '", failing_pairs[most_rep_index][
            0], "' is the same for attempts: ", failing_pairs[most_rep_index][1]
        rate = (dupes / total) * 100
        print ERR_PrintPrefix + "Attempted to login", retry_logon, "times with the same user/password pair. Got", dupes, "duplicates (rate is ", rate, "percents)\n"
        sys.stdout.flush()
        FailReport = FinalFail_PrintPrefix + glob_test_name + "test failed: tokens for diffrent logons are the same."
        assert False, FailReport
        exit(111)  # shouldn't reach this.
    else:
        print AllOK_PrintPrefix + "    .. passed.."


def confirm_user_in_DB(db_conn, username):
    """ checks that username is present in DB in v_user view, returns 'True' then. Aborts test if not. """
    global glob_test_result_state

    # abort if we passed value w/ injection to our DB related function
    if has_sql_sensitive(username):
        FailReport = "Unsafe test - programmer error. Please fix."
        db_conn.close()
        assert False, FailReport
        exit(253)

    print AllOK_PrintPrefix + "     [+] Looking databse for for user with login '" + username + "' .."
    query = "select id from v_user where login = '" + username + "'" + ";"
    # print AllOK_PrintPrefix + "query: '" + query + "'"
    try:
        db_cursor = db_conn.cursor(buffered=True)
        db_cursor.execute(query)
        if db_cursor.rowcount == 0:
            print ERR_PrintPrefix + "Cannot find a user with login '" + username + "' ."
            sys.stdout.flush()
            db_cursor.close()
            db_conn.close()
            assert False, "Database contents are'n't prepared for test."
            exit(252)  # shouldn't reach this.
        else:
            if db_cursor.rowcount == 1:
                print AllOK_PrintPrefix + "        .. passed. User found."
                return True
            else:
                print ERR_PrintPrefix + "unexpected number of results (", db_cursor.rowcount, ") for query  \"" + query + "\" - only 1 should appear as result. Abort."
                sys.stdout.flush()
                db_cursor.close()
                db_conn.close()
                assert False, "Database contents are'n't prepared for test."
                exit(253)  # shouldn't reach this.
    except mysql.connector.errors.ProgrammingError as e:
        print ERR_PrintPrefix + "exception while executing '" + query + "' :"
        print e
        print "Most probably environment is currently in 'deployng' state - please wait till environment finish deploying and rerun test."
        sys.stdout.flush()
        db_conn.close()
        exit(253)
    finally:
        db_cursor.close()


def get_user_email_from_DB(db_conn, username):
    """ returns email for username from DB. Aborts test if username is not found."""

    global glob_test_result_state

    # abort if we passed value w/ injection to our DB related function
    if has_sql_sensitive(username):
        FailReport = "Unsafe test - programmer error. Please fix."
        db_conn.close()
        assert False, FailReport
        exit(253)

    print AllOK_PrintPrefix + "     [+] Looking databse for email for user '" + username + "' .."
    query = "select email from v_user where login = '" + username + "'" + ";"
    # print AllOK_PrintPrefix + "query: '" + query + "'"
    try:
        db_cursor = db_conn.cursor(buffered=True)
        db_cursor.execute(query)
    except exceptions.StandardError as e:
        print ERR_PrintPrefix + "Exception working w/ database using query '" + query + "' :"
        print e
        sys.stdout.flush()
        db_cursor.close()
        db_conn.close()
        FailReport = FinalFail_PrintPrefix + glob_test_name + "test failed: exception while working w/ database using query '" + query + "' ."
        assert False, FailReport
        exit(253)
    if db_cursor.rowcount == 0:
        print ERR_PrintPrefix + "Cannot find a user with login '" + username + "' ."
        db_cursor.close()
        return None
    else:
        if db_cursor.rowcount == 1:
            user_email = db_cursor.fetchone()[0]
            print AllOK_PrintPrefix + "        .. passed. Got email '" + user_email + "'"
            db_cursor.close()
            return user_email
        else:
            print ERR_PrintPrefix + "unexpected number of results (", db_cursor.rowcount, ") for query  \"" + query + "\" - only 1 should appear as result. Abort."
            sys.stdout.flush()
            db_cursor.close()
            db_conn.close()
            assert False, "Database contents are'n't prepared for test."
            exit(253)  # shouldn't reach this.


def check_failedAddPartnUser_response_schema(js, suppress_output=False):
    """  получает json ответа. Если не соответствует схеме - валит тест. """

    global glob_test_result_state

    schema2check, schema_name, response_type = failed_AddPartnUser_reply_schema, "failed_AddPartnUser_reply_schema", "Failure"
    validator = jsonschema.Draft4Validator(schema2check)
    try:
        validator.validate(js)
        if not suppress_output:
            print AllOK_PrintPrefix + "      .. passed: json validation."
    except jsonschema.exceptions.ValidationError as e:
        print ERR_PrintPrefix + "validation error when checking json reply from add partnered user API:", e.message
        print "Schema used: ", schema_name, ";", response_type, " expected to be returned by remote API endpoint."
        print "JSON that failed validation:"
        print "-------------- json start ----------------------:\n"
        print json.dumps(js, indent=4, encoding='utf-8', sort_keys=True)
        print "\n-------------- json end   --------------------"
        sys.stdout.flush()
        assert False, "Reply from add partnered user API didn't pass schema validation."
        exit(111)  # shouldn't reach this.


def check_authrec_response_schema(js, error_status, suppress_output=False):
    """ получает json ответа и статус ошибки (True - ответ об ошибке,  False - нормальный ответ) для выбора схемы. Если не соответствует схеме - валит тест. """

    global glob_test_result_state

    if error_status:
        schema2check, schema_name, response_type = failed_authrec_reply_schema, "failed_authrec_reply_schema", "Failure"
    else:
        schema2check, schema_name, response_type = accepted_authrec_reply_schema, "accepted_authrec_reply_schema", "Okay"

    validator = jsonschema.Draft4Validator(schema2check)
    try:
        validator.validate(js)
        if not suppress_output:
            print AllOK_PrintPrefix + "      .. passed: json validation."
    except jsonschema.exceptions.ValidationError as e:
        print ERR_PrintPrefix + "validation error when checking json reply from authorisation change part of API:", e.message
        print "Schema used: ", schema_name, ";", response_type, " expected to be returned by remote API endpoint."
        print "JSON that failed validation:"
        print "-------------- json start ----------------------:\n"
        print json.dumps(js, indent=4, encoding='utf-8', sort_keys=True)
        print "\n-------------- json end   --------------------"
        sys.stdout.flush()
        assert False, "Reply from logon API didn't pass schema validation."
        exit(111)  # shouldn't reach this.
    pass


def check_nokey_response_schema(js, suppress_output=False):
    """  получает json ответа. Если не соответствует схеме - валит тест. """

    global glob_test_result_state
    schema2check = no_key_reply_schema

    validator = jsonschema.Draft4Validator(schema2check)
    try:
        validator.validate(js)
        if not suppress_output:
            print AllOK_PrintPrefix + "      .. passed: json validation."
    except jsonschema.exceptions.ValidationError as e:
        print ERR_PrintPrefix + "validation error when checking json reply from logon part of API:", e.message
        print "JSON that failed validation:"
        print "-------------- json start ----------------------:\n"
        print json.dumps(js, indent=4, encoding='utf-8', sort_keys=True)
        print "\n-------------- json end   --------------------"
        sys.stdout.flush()
        assert False, "Reply from logon API didn't pass schema validation."
        exit(111)  # shouldn't reach this.
    pass


def check_partnercount_response_schema(js, suppress_output=False):
    """ получает json ответа и если не соответствует схеме - валит тест."""

    global glob_test_result_state

    schema2check = okay_partnercount_reply_schema

    validator = jsonschema.Draft4Validator(schema2check)
    try:
        validator.validate(js)
        if not suppress_output:
            print AllOK_PrintPrefix + "      .. passed: json validation."
    except jsonschema.exceptions.ValidationError as e:
        print ERR_PrintPrefix + "validation error when checking json reply from partner count API call:", e.message
        print "JSON that failed validation:"
        print "-------------- json start ----------------------:\n"
        print json.dumps(js, indent=4, encoding='utf-8', sort_keys=True)
        print "\n-------------- json end   --------------------"
        assert False, "Reply from partner count API didn't pass schema validation."
        exit(111)  # shouldn't reach this.
    pass


# FIXME: move to security test pull, и попутно с переносом в коммон поменять название на чуть более развёрнутое.
def sqlinj_logon_checks(db_conn, suppress_output=False):
    """ makes attempts to use sql injection, checks it doesn't work. """

    global glob_test_result_state

    if not suppress_output:
        print AllOK_PrintPrefix + "[+] Attempting to trigger SQL injection .."
    logins_with_injection = get_SQL_injection_strings(cfg_admin_user, glob_user2inject)
    passwds_with_injection = get_SQL_injection_strings(cfg_admin_user_passwd, glob_user2inject)
    if not suppress_output:
        print AllOK_PrintPrefix, len(logins_with_injection) + len(
            passwds_with_injection), "attempts will be used for this.."
    if not suppress_output:
        print AllOK_PrintPrefix + " atempting sql injection for login . ",
    for user_with_injection in logins_with_injection:
        #         *. нельзя зайти используя SQL injection
        state, string = lk_api_login(user_with_injection, cfg_admin_user_passwd, suppress_output=True)
        if state:
            print ERR_PrintPrefix + "Got token '" + string + "' from remote. Logged in w/ incorrect login/password pair:", user_with_injection, " / ", cfg_admin_user_passwd, " ."
            report_SQL_injection_status(db_conn, glob_user2inject)
            sys.stdout.flush()
            db_conn.close()
            FailReport = FinalFail_PrintPrefix + glob_test_name + "test failed: able to login w/ random user / password with injected sql statement pair: '" + user_with_injection + "' / '" + cfg_admin_user_passwd + "'"
            assert False, FailReport
            exit(111)  # shouldn't reach this.
        if not suppress_output:
            print ".",
    print "\n" + AllOK_PrintPrefix + "   .. passed: bad logon attempts rejected."

    print AllOK_PrintPrefix + " atempting sql injection for password . ",
    for passwd_with_injection in passwds_with_injection:
        #         *. нельзя зайти используя SQL injection
        state, string = lk_api_login(cfg_admin_user, passwd_with_injection, suppress_output=True)
        if state:
            print ERR_PrintPrefix + "Got token '" + string + "' from remote. Logged in w/ incorrect login/password pair:", cfg_admin_user, " / ", passwd_with_injection, " ."
            report_SQL_injection_status(db_conn, glob_user2inject)
            sys.stdout.flush()
            db_conn.close()
            FailReport = FinalFail_PrintPrefix + glob_test_name + "test failed: able to login w/ user / password with injected sql statement: '" + cfg_admin_user + "' / '" + passwd_with_injection + "'"
            assert False, FailReport
            exit(111)  # shouldn't reach this.
        print ".",
    print "\n" + AllOK_PrintPrefix + "   .. passed: bad logon attempts rejected."

    # now check if DB has no user which insertion attempted by SQL injection
    if report_SQL_injection_status(db_conn, glob_user2inject):
        db_conn.close()
        FailReport = FinalFail_PrintPrefix + glob_test_name + "test failed: SQL injection detected (user" + glob_user2inject + " is found in DB)."
        assert False, FailReport
        exit(111)  # shouldn't reach this.


def get_partnercount_from_api(suppress_output=False):
    """ возвращает к-во партнеров из вызова API + валидирует ответ по json схеме. """

    global glob_test_result_state

    req_url = cfg_api_url + "/partner/count?key=" + cfg_api_key
    headers = {'Authorization': 'Basic YXBhaGVyZWhjOjlzQmJPeTZk', 'key': cfg_api_key}
    resp = send_http_request(req_url, 'get', "requesting partner count.", headers=headers)
    if resp.status_code == 200:
        js = resp.json()
        check_partnercount_response_schema(js, suppress_output)
        partner_count = js['data']['count']
        if not suppress_output:
            print AllOK_PrintPrefix + "  .. Got response from API, partner count is", partner_count, " (response status code ", resp.status_code, ")."
            sys.stdout.flush()
            if cfg_show_response:
                print AllOK_PrintPrefix + "     ..response text:", resp.text
                sys.stdout.flush()
        return partner_count
    else:
        print ERR_PrintPrefix + "Got response from API, with unexpected response status code ", resp.status_code, "."
        print ERR_PrintPrefix + "Response text:", resp.text
        sys.stdout.flush()
        FailReport = FinalFail_PrintPrefix + glob_test_name + "test failed: unexpected response code from partner count API call."
        assert False, FailReport
        exit(111)  # shouldn't reach this.


def get_partnercount_from_db(db_conn, suppress_output=False):
    """ возвращает к-во партнеров в БД."""

    global glob_test_result_state

    if not suppress_output:
        print AllOK_PrintPrefix + "     [+] Looking databse for for partner count value .."
    query = "select count(*) from partners;"
    # print AllOK_PrintPrefix + "query: '" + query + "'"
    try:
        db_cursor = db_conn.cursor(buffered=True)
        db_cursor.execute(query)
    except exceptions.StandardError as e:
        print ERR_PrintPrefix + "Exception working w/ database using query '" + query + "' :"
        sys.stdout.flush()
        print e
        sys.stdout.flush()
        db_cursor.close()
        db_conn.close()
        FailReport = FinalFail_PrintPrefix + glob_test_name + "test failed: exception while working w/ database using query '" + query + "' . Abort."
        assert False, FailReport
        exit(253)
    if db_cursor.rowcount == 1:
        partner_count = db_cursor.fetchone()[0]
        if not suppress_output:
            print AllOK_PrintPrefix + "      .. pass: partner count from DB is:", partner_count
        db_cursor.close()
        return partner_count
    else:
        print ERR_PrintPrefix + "unexpected number of results (", db_cursor.rowcount, ") for query  \"" + query + "\" - only 1 should appear as result. Abort."
        sys.stdout.flush()
        db_cursor.close()
        db_conn.close()
        FailReport = FinalFail_PrintPrefix + glob_test_name + "test failed: meaningless value returnd from query '" + query + "' . Check database & test script. Abort."
        assert False, FailReport
        exit(111)  # shouldn't reach this.


def wrong_requests2add_partnered_user(db_conn, suppress_output=False):
    """  делает запросы на добавление пользователя-партнера с некорректными параметрами, возвращает True если ни одной успешной попытки, иначе валит тест
         запросы с отсутсвием каждого и комбинации отсутсвия обязательных параметров
         запросы с невалидным содержимым параметров
         запросы с параметрами некорректным из-за попытки sql injection
         все эти некорретные запросы идут с корректным api key
    """
    # FIXME,for refactoring: try to test even and non-even combinations of cr/lf . The latter should cover some specific cases.
    global glob_test_result_state

    req_url = cfg_api_url + "/partner" + "?key=" + cfg_api_key
    headers = {'Authorization': 'Basic YXBhaGVyZWhjOjlzQmJPeTZk', 'key': cfg_api_key}
    # параметры:
    # 'name' - обязательно
    # 'lastName' - обязательно
    # 'url' - не обязательное, должно быть url
    # 'login' - 'required|email|unique:v_user,email'
    # 'password' - 'required|min:6|confirmed'
    # 'password_confirmation' должен совпадать с password
    # 'type' - обязательное 'alpha|in:legal,individual'
    # список символов которые должны восприниматься как пробельные, см. man ascii
    rnd_str_length = random.choice([1, 2, 3, 5, 7, 10, 15, 16, 127, 254])
    random_crlf_combination = get_random_string(rnd_str_length, "\r\n")  # random combination for new line char , FIXME: move to common/common_randomize
    # random_even_crlf_combination = random.choice( ["\r\n", "\n\r","\r\n\n\r"]) # random combination for new line char (even char count), FIXME: use this in specific cases
    # correct variations of url parameter
    url = random.choice([random.choice(["http://", "https://"]) + get_random_string(size=6) + "." + get_random_string(size=6) + "." + get_random_string(size=3),  # correct in terms of url format
                         get_random_spacechar_filled_string(),  # random space-filled
                         ''  # empty
                         ])
    random_spacechar_filled_string = get_random_spacechar_filled_string()
    # when assigning size note that in some requests name will be appended w/ random int(up to 20 chars)
    value1 = get_random_string(size=10, chars="АБВГДЕЖЗИКЛМНОПРСТУФХЧШЩЭЮЯЪЬабвгдеёжзиклмнийклмнопрстуфхчшщэюяьъ")
    # when assigning size note that in some requests name/lastname will be appended w/ random int(up to 20 chars)
    value2 = get_random_string(size=12)
    name = random.choice([value1, value2])
    lastname = random.choice([value1, value2])
    email = get_random_string(size=10) + "@" + get_random_string(size=6) + "." + get_random_string(size=6) + "." + get_random_string(size=3) + "." + get_random_string(size=2)
    passwd = get_random_string(size=8)
    # FIXME: generate all combinations for wrong set using iterators and using random values
    # correct set:
    #              {"name":name,
    #               "lastName":lastname,
    #               "url":url, # also empty, space-char filled.
    #               "login": email,
    #               "password": passwd,
    #               'password_confirmation': passwd,
    #               'type': usertype # use individual to avoid covering by requirement for Organisation field
    #              },                # FIXME: add same test for 'legal' (legal entity) type of partnered users - those require parameter OrgName
    req_params = [
        # no required 'type'
        {"name": name,
         "lastName": lastname,
         "url": url,
         "login": email,
         "password": passwd,
         'password_confirmation': passwd,
         },
        # no password_confirmation
        {"name": name,
         "lastName": lastname,
         "url": url,
         "login": email,
         "password": passwd,
         'type': 'individual'
         },
        # no password
        {"name": name,
         "lastName": lastname,
         "url": url,
         "login": email,
         'password_confirmation': passwd,
         'type': 'individual'
         },
        # no name
        {"lastName": lastname,
         "url": url,
         "password": passwd,
         'password_confirmation': passwd,
         'type': 'individual'
         },
        # no lastname
        {"name": name,
         "url": url,
         "login": email,
         "password": passwd,
         'password_confirmation': passwd,
         'type': 'individual'
         },
        # no login
        {"name": name,
         "lastName": lastname,
         "url": url,
         "password": passwd,
         'password_confirmation': passwd,
         'type': 'individual'
         },
        # no name,lastname
        {"url": url,
         "login": email,
         "password": passwd,
         'password_confirmation': passwd,
         'type': 'individual'
         },
        # no name,lastname,login
        {"url": url,
         "password": passwd,
         'password_confirmation': passwd,
         'type': 'individual'
         },
        # no name,lastname,login,password
        {"url": url,
         'password_confirmation': passwd,
         'type': 'individual'
         },
        # no name,lastname,login,password,password_confirmation
        {"url": url,
         'type': 'individual'
         },
        # no lastname, and also no optional url & required type
        {"name": name,
         "login": email,
         "password": passwd,
         'password_confirmation': passwd,
         },
        # no name, login, password
        {"lastName": lastname,
         "url": url,
         'password_confirmation': passwd,
         'type': 'individual'
         }
    ]

    # проверки только на нехватку параметров
    print AllOK_PrintPrefix + " [+] Checking that request to add partnered user fails when not enough required parameters provided.."
    for wrongdata in req_params:
        context_message = "requesting add partnered user (not enough required parameters provided)."
        resp = send_http_request(req_url, 'post', context_message, headers=headers, data=wrongdata, suppress_output=True)
        if resp.status_code == 200:
            js = resp.json()
            print ERR_PrintPrefix + "attempt to add user '" + email + "' associated as partner with insuffissient parameter set did not return failure. Got response code", resp.status_code, "."
            dump_request_params(req_url, headers=headers, data=wrongdata)
            print ExtraInfo_PrintPrefix + "     ..response text:", resp.text
            sys.stdout.flush()
            if js:
                # on success reply is the same as for login & thus schema too
                validate_json_by_schema(js, accepted_logon_reply_schema, "accepted_logon_reply_schema",
                                        context_message=context_message + "API reported susccess.",
                                        suppress_output=False)
                FailReport = FinalFail_PrintPrefix + glob_test_name + "test failed: successful return for request to add partnered user with required parameters missing."
            else:
                FailReport = FinalFail_PrintPrefix + glob_test_name + "test failed: successful return for request to add partnered user with required parameters missing. Also bad json in response."
            db_conn.close()
            assert False, FailReport
            exit(253)
        else:
            js = resp.json()
            validate_json_by_schema(js, failed_AddPartnUser_reply_schema, "failed_AddPartnUser_reply_schema",
                                    context_message=context_message,
                                    suppress_output=True)  # suppress output by default
            # check that no such user in DB for non empty email
            email2check = False
            try:
                email2check = wrongdata['login']
            except KeyError:
                pass
            if email2check:
                if is_user_in_DB(db_conn, email2check, suppress_output=True):
                    dump_request_params(req_url, headers=headers, data=wrongdata)
                    print ERR_PrintPrefix + "found user '" + str(
                        email2check) + "' in DB that API reported as failed to add. Abort."
                    sys.stdout.flush()
                    db_conn.close()
                    FailReport = FinalFail_PrintPrefix + glob_test_name + "test failed: API reported failure adding user '" + email + "' , but user is present in the database."
                    assert False, FailReport
                    exit(253)  # shouldn't reach this

    logger.success("add partnered user fails if required parameters omitted.")

    req_params = [
        # correct set:
        #              {"name":name,
        #               "lastName":lastname,
        #               "url":url, # also empty or spacechar-filled
        #               "login": email,
        #               "password": passwd,
        #               'password_confirmation': passwd,
        #               'type':'individual' # use individual to avoid covering by requirement for Organisation field
        #              },

        ### FIXME: uncomment when https://tsystem.atlassian.net/browse/CHET-170 will be closed
        ## цифры в имени
        #              {"name":name + str(get_random_int_from_set()),
        #              "lastName":lastname,
        #              "url":url,
        #              "login": email,
        #              "password": passwd,
        #              'password_confirmation': passwd,
        #              'type':'individual' # use individual to avoid covering by requirement for Organisation field
        #             },
        ### FIXME: uncomment when https://tsystem.atlassian.net/browse/CHET-170 will be closed
        # цифры в фамилии
        #              {"name":name,
        #               "lastName":lastname + str(get_random_int_from_set()),
        #               "url":url,
        #               "login": email,
        #               "password": passwd,
        #               'password_confirmation': passwd,
        #               'type':'individual' # use individual to avoid covering by requirement for Organisation field
        #              },
        ### FIXME: uncomment when https://tsystem.atlassian.net/browse/CHET-170 will be closed
        # цифры в имени и фамилии
        #              {"name":name + str(get_random_int_from_set()),
        #               "lastName":lastname + str(get_random_int_from_set()) ,
        #               "url":url,
        #               "login": email,
        #               "password": passwd,
        #               'password_confirmation': passwd,
        #               'type':'individual' # use individual to avoid covering by requirement for Organisation field
        #              },
        ### FIXME: uncomment when https://tsystem.atlassian.net/browse/CHET-170 will be closed
        # смесь алфавитов в имени
        #              {"name":random.choice(["РусскийИEnglish","EnglishРусский"]),
        #               "lastName":lastname,
        #               "url":url,
        #               "login": email,
        #               "password": passwd,
        #               'password_confirmation': passwd,
        #               'type':'individual' # use individual to avoid covering by requirement for Organisation field
        #              },
        ### FIXME: uncomment when https://tsystem.atlassian.net/browse/CHET-170 will be closed
        # смесь алфавитов в фамилии
        #              {"name":name,
        #               "lastName":random.choice(["РусскийИEnglish","EnglishРусский"]),
        #               "url":url,
        #               "login": email,
        #               "password": passwd,
        #               'password_confirmation': passwd,
        #               'type':'individual' # use individual to avoid covering by requirement for Organisation field
        #              },
        ### FIXME: uncomment when https://tsystem.atlassian.net/browse/CHET-170 will be closed
        # смесь алфавитов в имени и фамилии
        #              {"name":random.choice(["РусскийИEnglish","EnglishРусский"]),
        #               "lastName":random.choice(["РусскийИEnglish","EnglishРусский"]),
        #               "url":url,
        #               "login": email,
        #               "password": passwd,
        #               'password_confirmation': passwd,
        #               'type':'individual' # use individual to avoid covering by requirement for Organisation field
        #              },
        # bad url
        {"name": name,
         "lastName": lastname,
         "url": random.choice(["РусскийИEnglish", "EnglishРусский", "not_an_url_formatted_string"]),
         "login": email,
         "password": passwd,
         'password_confirmation': passwd,
         'type': 'individual'  # use individual to avoid covering by requirement for Organisation field
         },
        # число вместо url
        {"name": name,
         "lastName": lastname,
         "url": get_random_int_from_set(),
         "login": email,
         "password": passwd,
         'password_confirmation': passwd,
         'type': 'individual'  # use individual to avoid covering by requirement for Organisation field
         },
        # 0 вместо url
        {"name": name,
         "lastName": lastname,
         "url": 0,
         "login": email,
         "password": passwd,
         'password_confirmation': passwd,
         'type': 'individual'  # use individual to avoid covering by requirement for Organisation field
         },
        # пустой name
        {"name": '',
         "lastName": lastname,
         "url": url,
         "login": email,
         "password": passwd,
         'password_confirmation': passwd,
         'type': 'individual'  # use individual to avoid covering by requirement for Organisation field
         },
        # пустой lastname
        {"name": name,
         "lastName": '',
         "url": url,
         "login": email,
         "password": passwd,
         'password_confirmation': passwd,
         'type': 'individual'  # use individual to avoid covering by requirement for Organisation field
         },
        # и name и lastname пустые
        {"name": '',
         "lastName": '',
         "url": url,
         "login": email,
         "password": passwd,
         'password_confirmation': passwd,
         'type': 'individual'  # use individual to avoid covering by requirement for Organisation field
         },
        ### FIXME: uncomment when https://tsystem.atlassian.net/browse/CHET-170 will be closed
        # цифры вместо имени
        #              {"name":get_random_int_from_set(),
        #               "lastName":lastname,
        #               "url":url,
        #               "login": email,
        #               "password": passwd,
        #               'password_confirmation': passwd,
        #               'type':'individual' # use individual to avoid covering by requirement for Organisation field
        #              },
        ### FIXME: uncomment when https://tsystem.atlassian.net/browse/CHET-170 will be closed
        # цифры вместо фамилии
        #              {"name":name,
        #               "lastName":get_random_int_from_set(),
        #               "url":url,
        #               "login": email,
        #               "password": passwd,
        #               'password_confirmation': passwd,
        #               'type':'individual' # use individual to avoid covering by requirement for Organisation field
        #              },
        ### FIXME: uncomment when https://tsystem.atlassian.net/browse/CHET-170 will be closed
        # 0 в name:
        #              {"name":0,
        #               "lastName":lastname,
        #               "url":url,
        #               "login": email,
        #               "password": passwd,
        #               'password_confirmation': passwd,
        #               'type':'individual' # use individual to avoid covering by requirement for Organisation field
        #              },
        # 0 в lastname
        #             {"name":name ,
        #              "lastName":0,
        #              "url":url,
        #              "login": email,
        #              "password": passwd,
        #              'password_confirmation': passwd,
        #              'type':'individual' # use individual to avoid covering by requirement for Organisation field
        #             },
        # 0 в email
        {"name": name,
         "lastName": lastname,
         "url": url,
         "login": 0,
         "password": passwd,
         'password_confirmation': passwd,
         'type': 'individual'  # use individual to avoid covering by requirement for Organisation field
         },
        # 0 в user type
        {"name": name,
         "lastname": lastname,
         "url": url,
         "login": email,
         "password": passwd,
         'password_confirmation': passwd,
         'type': 0
         },
        # 0 в password и password confirmation - меньше длины пароля + на 0
        {"name": name,
         "lastname": lastname,
         "url": url,
         "login": email,
         "password": 0,
         'password_confirmation': 0,
         'type': 'individual'  # use individual to avoid covering by requirement for Organisation field
         },
        # None вместо параметра = пустой параметр - библиотека requests не отправляет такие переменные,
        # так что все варианты с None эквиваленты отсутствию параметра,а это проверяется в другом месте - пропускаем
        # строка меньше 6ти символов в пароле, только цифры
        {"name": name,
         "lastName": lastname,
         "url": url,
         "login": email,
         "password": "12345",
         'password_confirmation': "12345",
         'type': 'individual'
         },
        # строка меньше 6ти символов в пароле без цифр
        {"name": name,
         "lastName": lastname,
         "url": url,
         "login": email,
         "password": "sdfgh",
         'password_confirmation': "sdfgh",
         'type': 'individual'
         },
        # несовпадающие строки в пароле и подтверждении
        {"name": name,
         "lastName": lastname,
         "url": url,
         "login": email,
         "password": "password",
         'password_confirmation': "assword",
         'type': 'individual'  # use individual to avoid covering by requirement for Organisation field
         },
        ### FIXME: uncomment when https://tsystem.atlassian.net/browse/CHET-170 will be closed
        # имя состоящее из одних пробельных символов
        #              {"name":get_random_spacechar_filled_string(),
        #               "lastName":lastname,
        #               "url":url,
        #               "login": email,
        #               "password": passwd,
        #               'password_confirmation': passwd,
        #               'type':'individual' # use individual to avoid covering by requirement for Organisation field
        #              },
        ### FIXME: uncomment when https://tsystem.atlassian.net/browse/CHET-170 will be closed
        # имя состоящее из комбинаций перевода строки
        #              {"name":random_crlf_combination,
        #               "lastName":lastname,
        #               "url":url,
        #               "login": email,
        #               "password": passwd,
        #               'password_confirmation': passwd,
        #               'type':'individual' # use individual to avoid covering by requirement for Organisation field
        #              },
        ### FIXME: uncomment when https://tsystem.atlassian.net/browse/CHET-170 will be closed
        # фамилия состоящая из одних пробелов
        #              {"name":name,
        #               "lastName":get_random_spacechar_filled_string(),
        #               "url":url,
        #               "login": email,
        #               "password": passwd,
        #               'password_confirmation': passwd,
        #               'type':'individual' # use individual to avoid covering by requirement for Organisation field
        #              },
        # фамилия состоящая из комбинаций перевода строки
        {"name": name,
         "lastName": random_crlf_combination,
         "url": url,
         "login": email,
         "password": passwd,
         'password_confirmation': passwd,
         'type': 'individual'  # use individual to avoid covering by requirement for Organisation field
         },
        # пробельные символы вместо login
        {"name": name,
         "lastName": lastname,
         "url": url,
         "login": get_random_spacechar_filled_string(),
         "password": passwd,
         'password_confirmation': passwd,
         'type': 'individual'  # use individual to avoid covering by requirement for Organisation field
         },
        # комбинация cr/lf вместо login
        {"name": name,
         "lastName": lastname,
         "url": url,
         "login": random_crlf_combination,
         "password": passwd,
         'password_confirmation': passwd,
         'type': 'individual'  # use individual to avoid covering by requirement for Organisation field
         },
        # пробелы вместо пароля и его подтверждения - видимо штатное поведение - уточню в CHET-170, FIXME: remove if not needed.
        #              {"name":name,
        #               "lastName":lastname,
        #               "url":url,
        #               "login":email,
        #               "password": random_spacechar_filled_string,
        #               'password_confirmation': random_spacechar_filled_string,
        #               'type':'individual' # use individual to avoid covering by requirement for Organisation field
        #              },
        # перевод строки в разных комбинациях вместо пароля и его подтверждения
        {"name": name,
         "lastName": lastname,
         "url": url,
         "login": email,
         "password": random_crlf_combination,
         'password_confirmation': random_crlf_combination,
         'type': 'individual'  # use individual to avoid covering by requirement for Organisation field
         },
        # пробелы вместо type
        {"name": name,
         "lastName": lastname,
         "url": url,
         "login": email,
         "password": passwd,
         'password_confirmation': passwd,
         'type': get_random_spacechar_filled_string()
         },
        # cr/lf комбинации вместо type
        {"name": name,
         "lastName": lastname,
         "url": url,
         "login": email,
         "password": passwd,
         'password_confirmation': passwd,
         'type': random_crlf_combination
         }
    ]

    # проверки только на некорректное содержимое параметров
    print AllOK_PrintPrefix + " [+] Checking that request to add partnered user fails when broken parameters provided.."
    context_message = "request to add partnered user using broken parameters."
    for wrongdata in req_params:
        resp = send_http_request(req_url, 'post', context_message, headers=headers, data=wrongdata)
        if resp.status_code == 200:
            js = resp.json()
            print ERR_PrintPrefix + "attempt to add user '" + email + "' associated as partner with bad data in parameters did not return failure. Got response code", resp.status_code, "."
            dump_request_params(req_url, headers=headers, data=wrongdata)
            print ExtraInfo_PrintPrefix + "     ..response text:", resp.text
            sys.stdout.flush()
            if js:
                # on success reply is the same as for login & thus schema too
                validate_json_by_schema(js, accepted_logon_reply_schema, "accepted_logon_reply_schema",
                                        context_message=context_message + "API reported susccess.",
                                        suppress_output=False, no_abort_on_exception=True)
                FailReport = FinalFail_PrintPrefix + glob_test_name + "test failed: successful return for request to add partnered user with bad data in parameters."
            else:
                FailReport = FinalFail_PrintPrefix + glob_test_name + "test failed: successful return for request to add partnered user with bad data in parameters. Also bad json in response."
            db_conn.close()
            logger.error("able to create partnered user using bad formed parameters.")
            assert False, FailReport
            exit(253)  # shouldn't reach this
        else:  # resp.status_code not 200
            FailMessage = FailReport = None
            context_message = "requesting add parntered user API with incorrect parameter set. API returned error."
            js = resp.json()
            js_valid_by_schema = validate_json_by_schema(js, failed_AddPartnUser_reply_schema,
                                                         "failed_AddPartnUser_reply_schema", context_message,
                                                         suppress_output=True)
            if not js_valid_by_schema:
                print ERR_PrintPrefix + "Validation error for reply schema."
                print ERR_PrintPrefix + "Reply failing validation:", resp.text
                FailMessage = " json in response for wrong request doesn't match schema 'failed_AddPartnUser_reply_schema'."
            # check that no such user in DB for non empty email
            email2check = False
            try:
                email2check = wrongdata['login']
            except KeyError:
                pass
            if email2check:
                if is_user_in_DB(db_conn, email2check, suppress_output=False):  # FIXME: suppress output
                    dump_request_params(req_url, headers=headers, data=wrongdata)
                    print ERR_PrintPrefix + "found user '" + str(email2check) + "' in DB that API reported as failed to add. Abort."
                    sys.stdout.flush()
                    db_conn.close()
                    if FailMessage:
                        FailMessage = FailMessage + " Also: API reported failure adding user '" + email + "' , but user is present in the database."
                    else:
                        FailMessage = "API reported failure adding user '" + email + "' , but user is present in the database."
            if FailMessage:
                FailReport = FinalFail_PrintPrefix + glob_test_name + "test failed:" + FailMessage
                assert False, FailReport
                exit(253)  # shouldn't reach this

    logger.success("cannot add partnered user w/ incorrectly formed parameters.")

    # FIXME: move this to security tests
    print AllOK_PrintPrefix + "     [+] sending API request to add partnered user with empty API key.."
    # empty key
    req_url = cfg_api_url + "/partner" + "?key=" + "''"
    headers = {'Authorization': 'Basic YXBhaGVyZWhjOjlzQmJPeTZk', 'key': ''}
    req_params = {"name": name,
                  "lastName": lastname,
                  "url": url,
                  "login": email,
                  "password": passwd,
                  'password_confirmation': passwd,
                  'type': 'individual'  # FIXME - random here
                  }
    context_message = "requesting add partnered user (using empty API key)."
    resp = send_http_request(req_url, 'post', context_message, headers=headers, data=req_params)
    if resp.status_code == 200:
        js = resp.json()
        dump_request_params(req_url, headers=headers, data=req_params)
        print ERR_PrintPrefix + "  .. API reported success adding partnered user '" + email + "', but we've used empty API key. Got response code", resp.status_code, "."
        print ExtraInfo_PrintPrefix + "     ..response text:", resp.text
        sys.stdout.flush()
        if js:
            # on success reply is the same as for login & thus schema too
            validate_json_by_schema(js, accepted_logon_reply_schema, "accepted_logon_reply_schema", context_message=context_message + "API reported susccess.", suppress_output=False)
        db_conn.close()
        FailReport = FinalFail_PrintPrefix + glob_test_name + "test failed: user reported as created with empty API key. Abort."
        assert False, FailReport
        exit(253)
    else:
        if not suppress_output:
            print AllOK_PrintPrefix + "Failed to add user '" + email + "' associated as partner using empty API key - it's OK. Got response code", resp.status_code, "."
        context_message = context_message + "API returned error."
        js = resp.json()
        js_valid_by_schema = validate_json_by_schema(js, no_key_reply_schema, "no_key_reply_schema", context_message, suppress_output=True)
        if not js_valid_by_schema:
            print ERR_PrintPrefix + "Validation error for reply schema."
            print ERR_PrintPrefix + "Reply failing validation:", resp.text
            FailReport = FinalFail_PrintPrefix + glob_test_name + "test failed: Validation error for reply schema (no_key_reply_schema) on attempt to use empty API key."
            assert False, FailReport
            exit(253)
    # no key
    print AllOK_PrintPrefix + "     [+] sending API request to add partnered user without API key.."
    req_url = cfg_api_url + "/partner"
    headers = {'Authorization': 'Basic YXBhaGVyZWhjOjlzQmJPeTZk'}
    req_params = {"name": name,
                  "lastName": lastname,
                  "url": url,
                  "login": email,
                  "password": passwd,
                  'password_confirmation': passwd,
                  'type': 'individual'  # FIXME - random here
                  }
    context_message = "request add partnered user (no API key)."
    resp = send_http_request(req_url, 'post', context_message, headers=headers, data=req_params)
    if resp.status_code == 200:
        print ERR_PrintPrefix + "Code", resp.status_code, "for add partnered user without API key!"
        js = resp.json()
        dump_request_params(req_url, headers=headers, data=req_param)
        print ERR_PrintPrefix + "  .. API reported success adding partnered user '" + email + "', but we didn't provide an API key. Got response code", resp.status_code, "."
        print ExtraInfo_PrintPrefix + "     ..response text:", resp.text
        sys.stdout.flush()
        if is_user_in_DB(db_conn, email):
            print ERR_PrintPrefix + "user", email, "also found in DB."
        else:
            print ExtraInfo_PrintPrefix + "Though, user", email, "not found in DB."
        if js:
            # on success reply is the same as for login & thus schema too
            validate_json_by_schema(js, accepted_logon_reply_schema, "accepted_logon_reply_schema", context_message=context_message + "API reported susccess.", suppress_output=False)
        FailReport = FinalFail_PrintPrefix + glob_test_name + "failed: user reported as 'created' when no API key given. Abort."
        db_conn.close()
        assert False, FailReport
        exit(253)
    else:
        if not suppress_output:
            print AllOK_PrintPrefix + "Failed to add user '" + email + "' associated as partner using empty API key - it's OK. Got response code", resp.status_code, "."
        context_message = context_message + "API returned error."
        js = resp.json()
        js_valid_by_schema = validate_json_by_schema(js, no_key_reply_schema, "no_key_reply_schema", context_message, suppress_output=True)
        if not js_valid_by_schema:
            print ERR_PrintPrefix + "Validation error for reply schema."
            print ERR_PrintPrefix + "Reply failing validation:", resp.text
            FailReport = FinalFail_PrintPrefix + glob_test_name + "failed: Validation error for reply schema (no_key_reply_schema) on attempt to omit API key."
            assert False, FailReport
            exit(253)
    # test for sql injection - FIXME: uncomment after rewrite
    # check_add_partnered_user_with_sql_injection(db_conn,suppress_output=suppress_output)
    return True


def request_add_partnered_user(db_conn, name, lastname, email, passwd, expect_error=False, usertype=False, url=False, suppress_output=False):
    """ делает запрос на добавление пользователя-партнера, возвращает пару из response_status,token при успехе или response_status,response при неудаче
         подразумевается использование только для корректных запросов, для игры с отсутствующими или некорректными параметрами используйте send_http_request() ."""
    global glob_test_result_state

    debug = False
    global glob_test_start_time
    req_url = cfg_api_url + "/partner" + "?key=" + cfg_api_key
    headers = {'Authorization': 'Basic YXBhaGVyZWhjOjlzQmJPeTZk', 'key': cfg_api_key}
    # параметры:
    # 'name' - обязательно
    # 'lastName' - обязательно
    # 'url' - не обязательное, должно быть url, может состоять из пробельных символов
    # 'login' - 'required|email|unique:v_user,email'
    # 'password' - 'required|min:6|confirmed'
    # 'password_confirmation' должен совпадать с password
    # 'type' - обязательное 'alpha|in:legal,individual'
    if not usertype in get_available_partnered_user_types():
        FailReport = FinalFail_PrintPrefix + glob_test_name + "autotes coder failure: partnered user type is REQUIRED parameter and must match get_available_partnered_user_types() response."
        assert False, FailReport
        exit(253)

    # FIXME: form req_params separately for type 'legal' when https://tsystem.atlassian.net/browse/CHET-169 will be closed.
    if url != '' and not url:  # нет необязательного url, в т.ч. путого
        if debug:
            print ExtraInfo_PrintPrefix + "url parameter is omitted."
        req_params = {"name": name,
                      "lastName": lastname,
                      "login": email,
                      "password": passwd,
                      'password_confirmation': passwd,
                      'type': usertype
                      }
    elif url == '' or url:
        if debug:
            print ExtraInfo_PrintPrefix + "all parameters have values."
        req_params = {"name": name,
                      "lastName": lastname,
                      "url": url,
                      "login": email,
                      "password": passwd,
                      'password_confirmation': passwd,
                      'type': usertype
                      }
    if not suppress_output:
        print AllOK_PrintPrefix + "     [+] sending API request to add partnered user.."
    if expect_error:
        context_message = "requesting add partnered user. Refuse to add expected."
    else:
        context_message = "requesting add partnered user. Successfull add expected."

    resp = send_http_request(req_url, 'post', context_message, headers=headers, data=req_params)
    if resp.status_code == 200:
        js = resp.json()
        if not suppress_output:
            if expect_error:
                print ERR_PrintPrefix + "  .. Got unexpected response: add user '" + email + "' associated as partner passed. Got response code", resp.status_code, "."
                dump_request_params(req_url, headers=headers, data=req_params)
            else:
                print AllOK_PrintPrefix + "  .. add user '" + email + "' associated as partner passed. Got response code", resp.status_code, "."
            sys.stdout.flush()
        # on success reply is the same as for login
        validate_json_by_schema(js, accepted_logon_reply_schema, "accepted_logon_reply_schema", context_message, suppress_output)
        if expect_error:
            print ERR_PrintPrefix + "      .. failed: user reported as created, but with parameters above we expect failure."
        else:
            if not suppress_output:
                print AllOK_PrintPrefix + "      .. passed: user reported as created.."
        check_db_for_partnered_user(db_conn, glob_test_start_time, email, name, lastname, usertype, url, suppress_output)
        if expect_error:
            db_conn.close()
            FailReport = FinalFail_PrintPrefix + glob_test_name + "test failed: API successfully added user when test expect failure adding partnered user."
            assert False, FailReport
            exit(253)  # shouldn't reach this
    else:  # here we go when failed to add partnered user due to some error
        if expect_error:
            context_message = "requesting add partnered user. API returned error (as expected) with status code " + str(resp.status_code)
        else:
            context_message = "requesting add partnered user API API returned unexpected error with status code " + str(resp.status_code)
        js = resp.json()
        if not expect_error:
            logger.error("Failed to add user '" + email + "' associated as partner . We excpected success. Got response code " + str(resp.status_code) + ".")
            dump_request_params(req_url, headers=headers, data=req_params)
        else:
            if not suppress_output:
                print AllOK_PrintPrefix + "Failed to add user '" + email + "' associated as partner (as excpected). Got response code", resp.status_code, "."
        validate_json_by_schema(js, failed_AddPartnUser_reply_schema, "failed_AddPartnUser_reply_schema", context_message, suppress_output=False)
        if email:
            if is_user_in_DB(db_conn, email, suppress_output):
                db_conn.close()
                FailReport = FinalFail_PrintPrefix + glob_test_name + "test failed: request to add partnered user returned failure, but user is found in DB."
                assert False, FailReport
                exit(253)  # shouldn't reach this
        if not expect_error:
            FailMessage = "Request to add partnered user returned failure, but we expected success."
            logger.finishFail(FailMessage)
            FailReport = FinalFail_PrintPrefix + glob_test_name + "test failed: " + FailMessage
            assert False, FailReport
            exit(253)  # shouldn't reach this
    return resp.status_code, resp


def check_add_partnered_user_with_sql_injection(db_conn, suppress_output=False):
    """ отправляет запросы на добавление пользователя-партнера с параметрами испорченными попытками сделать sql injection.
         Если получилось найти injection - валит тест. """
    global glob_test_result_state
    global glob_user2inject

    value1 = get_random_string(size=10, chars="АБВГДЕЖЗИКЛМНОПРСТУФХЧШЩЭЮЯЪЬабвгдеёжзиклмнийклмнопрстуфхчшщэюяьъ")
    value2 = get_random_string(size=12)
    name = random.choice([value1, value2])
    lastname = random.choice([value1, value2])
    url = random.choice(["http://", "https://"]) + get_random_string(size=6) + "." + get_random_string(size=6) + "." + get_random_string(
        size=3)
    headers = {'Authorization': 'Basic YXBhaGVyZWhjOjlzQmJPeTZk', 'key': cfg_api_key}
    email = get_random_string(size=10) + "@" + get_random_string(size=6) + "." + get_random_string(size=6) + "." + get_random_string(size=3)
    passwd = get_random_string(size=8)
    usertype = random.choice(get_available_partnered_user_types())  # 'individual' or 'legal'

    print AllOK_PrintPrefix + "     [+] sending API request to add partnered user with SQL injection inside one of parameters.."
    req_url = cfg_api_url + "/partner" + "?key=" + cfg_api_key
    req_params_list = []
    for str_with_injection in get_SQL_injection_strings(name, glob_user2inject):
        req_params = {"name": str_with_injection,
                      "lastName": lastname,
                      "url": url,
                      "login": email,
                      "password": passwd,
                      'password_confirmation': passwd,
                      'type': usertype
                      }
        req_params_list.append(req_params)
    for str_with_injection in get_SQL_injection_strings(lastname, glob_user2inject):
        req_params = {"name": name,
                      "lastName": str_with_injection,
                      "url": url,
                      "login": email,
                      "password": passwd,
                      'password_confirmation': passwd,
                      'type': usertype
                      }
        req_params_list.append(req_params)
    for str_with_injection in get_SQL_injection_strings(url, glob_user2inject):
        req_params = {"name": name,
                      "lastName": lastname,
                      "url": str_with_injection,
                      "login": email,
                      "password": passwd,
                      'password_confirmation': passwd,
                      'type': usertype
                      }
        req_params_list.append(req_params)
    for str_with_injection in get_SQL_injection_strings(email, glob_user2inject):
        req_params = {"name": name,
                      "lastName": lastname,
                      "url": url,
                      "login": str_with_injection,
                      "password": passwd,
                      'password_confirmation': passwd,
                      'type': usertype
                      }
        req_params_list.append(req_params)
    for str_with_injection in get_SQL_injection_strings(passwd, glob_user2inject):
        req_params = {"name": name,
                      "lastName": lastname,
                      "url": url,
                      "login": email,
                      "password": str_with_injection,
                      'password_confirmation': str_with_injection,
                      'type': usertype
                      }
        req_params_list.append(req_params)
    for str_with_injection in get_SQL_injection_strings(usertype, glob_user2inject):
        req_params = {"name": name,
                      "lastName": lastname,
                      "url": url,
                      "login": email,
                      "password": passwd,
                      'password_confirmation': passwd,
                      'type': str_with_injection
                      }
        req_params_list.append(req_params)

    print AllOK_PrintPrefix + "        there will be", len(req_params_list), "requests to check - this may take a few minutes."

    # Поскольку cтрока с injection вполнен может попасть в рамки ограничений для параметров,
    # мы не можем ожидать что каждый запрос будет fail'ить. Поэтому алгоритм таков:
    # внести injection_trigger в каждый парметр API, сделать запросы, проверить по БД что инъекции не получилось
    # Провести набор тестов в которых гарантированно получаем плохой имея injection_trigger
    # в одном из парметров, убедится что ответ по прежнему отрицательный (мы не можем проверять варианты с положительным ответом,
    # поскольку часть триггеров инъекций может не попадать в ограничения по одному или нескольким параметрам
    print AllOK_PrintPrefix + "Sending requests.",
    for req_params in req_params_list:
        resp = send_http_request(req_url, 'post', "request add partnered user (SQL injection in one of parameters).", headers=headers, data=req_params)
        if resp.status_code == 200:
            try:
                js = resp.json()
            except Exception as e:
                print ERR_PrintPrefix + "Exception when parsing response as json: ", e
                print "Response text:", resp.text
                pass
            # on success reply is the same as for login
            check_login_response_schema(js, True, suppress_output=True)  # FIXME: replace this function - it is obsolete, declaration removed
        else:
            json_okay = True
            try:
                js = resp.json()
            except Exception as e:
                print ERR_PrintPrefix + "Exception when parsing response as json: ", e
                print "Response text:", resp.text
                json_okay = False
                pass
            if json_okay:
                check_failedAddPartnUser_response_schema(js, suppress_output=True)
            else:
                FailReport = FinalFail_PrintPrefix + glob_test_name + "test failed: invalid json in response when trying to add partnered user with SQL injection in one of parameters."
                print ExtraInfo_PrintPrefix + "Request parameters: [ ",
                sys.stdout.softspace = False
                for key in req_params:
                    print  "'" + str(key) + "' => '", req_params[key], "'; ",
                sys.stdout.softspace = False
                print "]"
                sys.stdout.flush()
                if report_SQL_injection_status(db_conn, glob_user2inject):
                    db_conn.close()
                    FailReport = FinalFail_PrintPrefix + glob_test_name + "test failed: SQL injection detected (user " + glob_user2inject + "is found in DB), also invalid json in response when trying to add partnered user with SQL injection in one of parameters.Abort."
                assert False, FailReport
                exit(253)  # shouldn't reach this
        sys.stdout.softspace = False
        print ".",
    print "Done."

    # запросы с некорректными параметрами, проверяем, что с injection тоже отдадут ошибку
    req_params_list = []
    # корректные значения
    req_url = cfg_api_url + "/partner" + "?key=" + cfg_api_key
    ## комбинации корректных и некорректных значений
    # комбинация русского и английского в фамилии
    for str_with_injection in get_SQL_injection_strings(name, glob_user2inject):
        req_params = {"name": str_with_injection,
                      "lastName": "КомбинацияАлфавитовRussianEnglish",
                      "url": url,
                      "login": email,
                      "password": passwd,
                      'password_confirmation': passwd,
                      'type': usertype
                      }
        req_params_list.append(req_params)
    # комбинация русского и английского в имени
    for str_with_injection in get_SQL_injection_strings(lastname, glob_user2inject):
        req_params = {"name": "КомбинацияАлфавитовRussianEnglish",
                      "lastName": str_with_injection,
                      "url": url,
                      "login": email,
                      "password": passwd,
                      'password_confirmation': passwd,
                      'type': usertype
                      }
        req_params_list.append(req_params)
    # строка логина не в формате мыла
    for str_with_injection in get_SQL_injection_strings(url, glob_user2inject):
        req_params = {"name": name,
                      "lastName": lastname,
                      "url": str_with_injection,
                      "login": "строкаNotAnEmailFormat",
                      "password": passwd,
                      'password_confirmation': passwd,
                      'type': usertype
                      }
        req_params_list.append(req_params)
    # password less then 6 chars
    for str_with_injection in get_SQL_injection_strings(email, glob_user2inject):
        req_params = {"name": name,
                      "lastName": lastname,
                      "url": url,
                      "login": str_with_injection,
                      "password": '12345',
                      'password_confirmation': '12345',
                      'type': usertype
                      }
        req_params_list.append(req_params)
    for str_with_injection in get_SQL_injection_strings(passwd, glob_user2inject):
        req_params = {"name": name,
                      "lastName": lastname,
                      "url": url,
                      "login": email,
                      "password": str_with_injection,
                      'password_confirmation': str_with_injection,
                      'type': "ЛевыйUserType"
                      }
        req_params_list.append(req_params)
    for str_with_injection in get_SQL_injection_strings(usertype, glob_user2inject):
        req_params = {"name": name,
                      "lastName": lastname,
                      "url": url,
                      "login": str_with_injection,
                      "password": passwd,
                      'password_confirmation': passwd,
                      'type': str_with_injection,
                      }
        req_params_list.append(req_params)

    print AllOK_PrintPrefix + "Repeating requests w/ one wrong parameter and additionally one containing SQL injection attempt - checking if them still fail."
    print AllOK_PrintPrefix + "There will be", len(req_params_list), "requests to check that requests with wrong data still failing - this may take a few minutes."
    print AllOK_PrintPrefix + "Sending requests.",
    for req_params in req_params_list:
        resp = send_http_request(req_url, 'post',
                                 "requesting add partnered user (one of parameters with SQL injection attempt and one formed improperly).",
                                 headers=headers, data=req_params)
        if resp.status_code == 200:
            print ERR_PrintPrefix + "Got success code when using bad parameter in response to add partnered user request via url '" + req_url + "'. Response code", resp.status_code, ". Abort."
            json_okay = True
            try:
                js = resp.json()
            except Exception as e:
                print ERR_PrintPrefix + "Exception when parsing response as json: ", e
                print "Response text:", resp.text
                json_okay = False
                pass
            # on success reply is the same as for login
            FailReport = FinalFail_PrintPrefix + glob_test_name + "test failed: success code for bad request to add partnered user."
            if json_okay:
                check_login_response_schema(js, True, suppress_output=True)
            else:
                FailReport = FailReport + "Bad json in response from API."
            if report_SQL_injection_status(db_conn, glob_user2inject):
                FailReport = FailReport + "SQL injection detected (user " + glob_user2inject + " is found in DB)."
            assert False, FailReport
            exit(253)
        else:
            json_okay = True
            try:
                js = resp.json()
            except Exception as e:
                print ERR_PrintPrefix + "Exception when parsing response as json: ", e
                print "Response text:", resp.text
                json_okay = False
                pass
            if json_okay:
                check_failedAddPartnUser_response_schema(js, suppress_output=True)
            else:
                FailReport = FinalFail_PrintPrefix + glob_test_name + "test failed: invalid json in response when trying to add partnered user with SQL injection in one of parameters."
                print ExtraInfo_PrintPrefix + "Request parameters: [ ",
                sys.stdout.softspace = False
                for key in req_params:
                    print  "'" + str(key) + "' => '", req_params[key], "'; ",
                sys.stdout.softspace = False
                print "]"
                sys.stdout.flush()
                if report_SQL_injection_status(db_conn, glob_user2inject):
                    db_conn.close()
                    FailReport = FailReport + "SQL injection detected (user " + glob_user2inject + "is found in DB)."
                assert False, FailReport
                exit(253)  # shouldn't reach this
        sys.stdout.softspace = False
        print ".",
    print "Done."

    for str_with_injection in get_SQL_injection_strings(cfg_api_key, glob_user2inject):
        headers = {'Authorization': 'Basic YXBhaGVyZWhjOjlzQmJPeTZk', 'key': str_with_injection}
        resp = send_http_request(req_url, 'post', "requesting add partnered user (API key with SQL injection attempt).", headers=headers, data=req_params)
        if resp.status_code == 200:
            FailReport = FinalFail_PrintPrefix + glob_test_name + "test failed: request to add partnered user with incorerect API key containing SQL injection returned success code " + str(
                resp.status_code) + "."
            json_okay = True
            try:
                js = resp.json()
            except Exception as e:
                print ERR_PrintPrefix + "Exception when parsing response as json: ", e
                json_okay = False
                FailReport = FailReport + "Bad json in API response."
                pass
            print ERR_PrintPrefix + "attempt to add user '" + email + "' associated as partner with SQL injection in an API key did not return failure. Got response code", resp.status_code, "."
            print ExtraInfo_PrintPrefix + "Request parameters: [ ",
            sys.stdout.softspace = False
            for key in req_params:
                print  "'" + str(key) + "' => '", req_params[key], "'; ",
            sys.stdout.softspace = False
            print "]"
            print ExtraInfo_PrintPrefix + "     ..response text:", resp.text
            sys.stdout.flush()
            if report_SQL_injection_status(db_conn, glob_user2inject):
                db_conn.close()
                FailReport = FailReport + "SQL injection detected (user " + glob_user2inject + " is found in DB)."
                assert False, FailReport
                exit(253)  # shouldn't reach this.
            else:
                print ExtraInfo_PrintPrefix + "No SQL injection result detected in DB."
            if json_okay:
                # on success reply is the same as for login
                check_login_response_schema(js, True, suppress_output)
            else:
                FailReport = FailReport + "Invalid json in API response."
                db_conn.close()
                assert False, FailReport
                exit(253)  # shouldn't reach this
        else:  # non 200 status_code
            json_okay = True
            try:
                js = resp.json()
            except Exception as e:
                print ERR_PrintPrefix + "Exception when parsing response as json: ", e
                json_okay = False
                pass
            if json_okay:
                check_failedAddPartnUser_response_schema(js, suppress_output=True)
                if not suppress_output:
                    if cfg_show_response:
                        print ExtraInfo_PrintPrefix + "     ..response text:", resp.text
                        sys.stdout.flush()
            else:
                FailReport = FinalFail_PrintPrefix + glob_test_name + "test failed: invalid json in API response when using invalid key with SQL injection in it."
                print ExtraInfo_PrintPrefix + "Request parameters: [ ",
                sys.stdout.softspace = False
                for key in req_params:
                    print  "'" + str(key) + "' => '", req_params[key], "'; ",
                sys.stdout.softspace = False
                print "]"
                print ExtraInfo_PrintPrefix + "     ..response text:", resp.text
                # check that no such user in DB
                if is_user_in_DB(db_conn, email, suppress_output=True):
                    print ERR_PrintPrefix + "found user '" + str(email) + "' in DB that API reported as failed to add."
                    sys.stdout.flush()
                    db_conn.close()
                    FailReport = FailReport + "API reported failure adding user '" + email + "' , but user is present in the database."
                    assert False, FailReport
                    exit(253)  # shouldn't reach this
                sys.stdout.flush()
                db_conn.close()
                assert False, FailReport
                exit(253)  # shouldn't reach this

    # check that user in SQL injection trigger is not in DB
    if report_SQL_injection_status(db_conn, glob_user2inject):
        db_conn.close()
        FailReport = FinalFail_PrintPrefix + glob_test_name + "test failed: SQL injection detected (user" + glob_user2inject + " is found in DB)."
        assert False, FailReport
        exit(253)  # shouldn't reach this.
    # end of check_add_partnered_user_with_sql_injection()


def check_add_partnered_user(db_conn, glob_test_start_time, suppress_output=False):
    """ успешно добавить пользователя со всеми полями, FIXME: генерация всех значения полей случайным образом.
        убедиться что можно залогиниться под этим пользователем
        FIXME: добавить пользователя  без необязательных полей
        убедиться что можно залогиниться под этим пользователем
        FIXME: уточнить поведение при заведении пользователя партнёра (leagal):  это название организации визуально вот http://joxi.ru/MAjJN3wHl8D1Ae
  поле обязательно ести тип legal, то есть юр.лицо, по формату никаких ограничений програмно не установлено в базе соответствует полю name таблицы partners, для физ лиц там производная от фио
  в базе на нем VARCHAR(255)
        FIXME: добавить проверку что нельзя дважды добавить одного пользователя-партнера
        FIXME: убдиться что в БД появились нужные связи с таблицей партнеров
        FIXME: сделать запросы используя некорректные данные в значениях параметров.
        FIXME: повторить комбинируя отсутствие одного или нескольких необязательных параметров.
        FIXME: повторить с попытками sql инъекции в каждом из доступных параметров. """

    global glob_test_result_state

    debug = False
    passwd = get_random_string(size=8)
    for usertype in [
        "individual"]:  # FIXME: replace ["individual"] w/ ["individual","legal"] when https://tsystem.atlassian.net/browse/CHET-169 will be closed.
        #  for usertype in ["individual","legal"]:
        url2pass = "http://" + get_random_string(size=6) + "." + get_random_string(size=6) + "." + get_random_string(size=3)
        if debug:
            print ExtraInfo_PrintPrefix + "url: '" + str(url) + "' , usertype: '" + str(usertype) + "'"
        value1 = get_random_string(size=10, chars=u"АБВГДЕЖЗИКЛМНОПРСТУФХЧШЩЭЮЯЪЬабвгдеёжзиклмнийклмнопрстуфхчшщэюяьъ")
        value2 = unicode(get_random_string(size=12))
        name = random.choice([value1, value2])
        lastname = random.choice([value1, value2])
        email = get_random_string(size=10) + "@" + get_random_string(size=6) + "." + get_random_string(size=4) + "." + get_random_string(size=3)
        request_add_partnered_user(db_conn, name, lastname, email, passwd, usertype=usertype, url=url2pass, suppress_output=suppress_output, expect_error=False)
        state, data = lk_api_login(email, passwd, suppress_output=True)
        if not state:
            print ERR_PrintPrefix + "Unable to logon with just created partnered user. Abort."
            print ERR_PrintPrefix + "Got this error on logon request: ", json.dumps(data, indent=4, encoding='utf-8', sort_keys=True)
            sys.stdout.flush()
            db_conn.close()
            FailReport = FinalFail_PrintPrefix + glob_test_name + "test failed: user created, but not valid - login failure (login:", email, "password:", passwd, ")"
            assert False, FailReport
            exit(111)  # shouldn't reach this.
        else:  # login state is okay
            if not suppress_output:
                print AllOK_PrintPrefix + "       Able to login with just created partnered user email '" + email + "' ."
    print AllOK_PrintPrefix + "       API calls w/ full parameter set and w/o all or some optional parameters: passed."
    wrong_requests2add_partnered_user(db_conn, suppress_output=True)


# FIXME: move to common/common_string or similar
def is_cyr(unicode_char):
    """ returns True if unicode char is russian."""
    return 'CYRILLIC' in unicodedata.name(unicode_char)
    # end of is_cyr()


def check_db_for_partnered_user(db_conn, glob_test_start_time, email, name, lastname, usertype=False, url=False,
                                suppress_output=False):
    """ check also partnersUsers table for association w/ this login
        check for partner id used in partnersUsers table
        prove that dateRegister is within test execution time
        возвращает True если пользователь есть, False если нет, если пользователь не один такой или в БД нет корректных связей для него - валит тест.
     """
    global glob_test_result_state
    if usertype == False:
        assert False, "autotest coder error: user type is required parameter."
        exit(253)
    if (email == None) or (email == False or email == True):
        assert False, "autotest coder error: email is required for check_db_for_partnered_user() to work properly."
        exit(253)

    if not suppress_output:
        print AllOK_PrintPrefix + "     [+] Looking databse for partner user with login and email '" + email + "' .."
    query0 = "select `id` from v_user where email = \"" + email + "\"" + " and login = email ;"
    print AllOK_PrintPrefix + "query: '" + query0 + "'"
    try:
        db_cursor = db_conn.cursor(buffered=True)
        db_cursor.execute(query0)
    except exceptions.StandardError as e:
        print ERR_PrintPrefix + "Exception working w/ database using query '" + query0 + "' :"
        print e
        sys.stdout.flush()
        db_cursor.close()
        db_conn.close()
        FailReport = FinalFail_PrintPrefix + glob_test_name + "test failed: exception while working w/ database using query '" + query0 + "' . Abort."
        assert False, FailReport
        exit(253)
    if db_cursor.rowcount == 0:
        if not suppress_output:
            print AllOK_PrintPrefix + "      .. user '" + email + "' not found."
        db_cursor.close()
        return False
    elif db_cursor.rowcount != 1:
        print ERR_PrintPrefix + "unexpected number of results (", db_cursor.rowcount, ") for query  \"" + query0 + "\" - only 1 should appear as result. Abort."
        sys.stdout.flush()
        db_cursor.close()
        db_conn.close()
        FailReport = FinalFail_PrintPrefix + glob_test_name + "test failed: check DB and sctipt: unexpected row count in reply from DB."
        assert False, FailReport
        exit(253)  # shouldn't reach this.
    elif db_cursor.rowcount == 1:
        print AllOK_PrintPrefix + "      .. user '" + email + "' found."
        # name and lastname may appear either in nameRU & lastnameRU or in name and lastname in v_user view
        query1 = "select `name`,`lastname`,`nameRU`,`lastnameRU` from v_user where email = \"" + email + "\"" + " and login = email ;"
        try:
            db_cursor.execute(query1)
            if db_cursor.rowcount == 0:
                if not suppress_output:
                    logger.fail("query '" + query0 + "' has result when query '" + query1 + "' has none.")
                sys.stdout.flush()
                db_cursor.close()
                db_conn.close()
                FailReport = FinalFail_PrintPrefix + glob_test_name + "coder or database content error."
                assert False, FailReport
                exit(253)  # shouldn't reach this.
            elif db_cursor.rowcount == 1:
                row = db_cursor.fetchone()
                name_db = row[0];
                lastname_db = row[1];
                nameRU = row[2];
                lastnameRU = row[3]
            else:
                logger.fail("query '" + query1 + "' gave unexpected results.")
                sys.stdout.flush()
                db_cursor.close()
                db_conn.close()
                FailReport = FinalFail_PrintPrefix + glob_test_name + "coder or database content error."
                assert False, FailReport
                exit(253)  # shouldn't reach this.
        except exceptions.StandardError as e:
            print ERR_PrintPrefix + "Exception working w/ database using query '" + query1 + "' :"
            print e
            sys.stdout.flush()
            db_cursor.close()
            db_conn.close()
            FailReport = FinalFail_PrintPrefix + glob_test_name + "test failed: exception while working w/ database using query '" + query1 + "' . Abort."
            assert False, FailReport
            exit(253)
        # name/lastname may appear either in russian or in english, depending to that results are in different database fields
        if is_cyr(name.strip()[0]):
            if not nameRU == name:
                print ERR_PrintPrefix + "properties from database do not match properties provided at partnered user create API call."
                print ERR_PrintPrefix + "name provided:", name, "name in DB:", nameRU
                sys.stdout.flush()
                db_cursor.close()
                db_conn.close()
                FailReport = FinalFail_PrintPrefix + glob_test_name + "test failed: user" + email + "made via API doesn't match its parameters in DB (" + name + " != " + nameRU + ")."
                assert False, FailReport
                exit(253)  # shouldn't reach this
        else:
            if not name_db == name:
                print ERR_PrintPrefix + "properties from database do not match properties provided at partnered user create API call."
                print ERR_PrintPrefix + "name provided:", name, "name in DB:", nameRU
                sys.stdout.flush()
                db_cursor.close()
                db_conn.close()
                FailReport = FinalFail_PrintPrefix + glob_test_name + "test failed: user" + email + "made via API doesn't match its parameters in DB (" + name + " != " + name_db + ")."
                assert False, FailReport
                exit(253)  # shouldn't reach this
        if is_cyr(lastname.strip()[0]):
            if not lastnameRU == lastname:
                print ERR_PrintPrefix + "properties from database do not match properties provided at partnered user create API call."
                print ERR_PrintPrefix + "name provided:", name, "name in DB:", nameRU
                sys.stdout.flush()
                db_cursor.close()
                db_conn.close()
                FailReport = FinalFail_PrintPrefix + glob_test_name + "test failed: user" + email + "made via API doesn't match its parameters in DB (" + name + " != " + nameRU + ")."
                assert False, FailReport
                exit(253)  # shouldn't reach this
        else:
            if not lastname_db == lastname:
                print ERR_PrintPrefix + "properties from database do not match properties provided at partnered user create API call."
                print ERR_PrintPrefix + "name provided:", name, "name in DB:", nameRU
                sys.stdout.flush()
                db_cursor.close()
                db_conn.close()
                FailReport = FinalFail_PrintPrefix + glob_test_name + "test failed: user" + email + "made via API doesn't match its parameters in DB (" + name + " != " + name_db + ")."
                assert False, FailReport
                exit(253)  # shouldn't reach this

        name_from_email, dropvalue = email.split('@')
        if (not '@' in email) and email:
            logger.info("check_db_for_partnered_user used w/ incorrect email in email parameter (no '@')", logger.LOG_WARNING)
            name_from_email = email  # FIXME: review algorithm to make sure that this is better than skipping such steps
        query2 = "select `type`,`url`,`id` from partners where name = \"" + name_from_email + "\"" + ";"
        try:
            db_cursor.execute(query2)
            if db_cursor.rowcount == 1:
                row = db_cursor.fetchone()
                usertype_db = row[0];
                url_db = row[1];
                partnerid_sel1 = row[2];
            elif db_cursor.rowcount == 0:
                logger.info("No results for query '" + query2 + "'")
                return (False)  # FIXME: review this!
            else:
                logger.fail("Unexpected number of results for query '" + query2 + "'")
                sys.stdout.flush()
                db_cursor.close()
                db_conn.close()
                FailReport = FinalFail_PrintPrefix + glob_test_name + "coder or database content error."
                assert False, FailReport
                exit(253)  # shouldn't reach this.
        except exceptions.StandardError as e:
            print ERR_PrintPrefix + "Exception working w/ database using query '" + query2 + "' :"
            print e
            sys.stdout.flush()
            db_cursor.close()
            db_conn.close()
            FailReport = FinalFail_PrintPrefix + glob_test_name + "test failed: exception while working w/ database using query '" + query2 + "' . Abort."
            assert False, FailReport
            exit(253)

        if usertype:
            if usertype_db != usertype.decode('utf-8'):
                print ERR_PrintPrefix + "properties from database do not match properties provided at partnered user create API call."
                print ERR_PrintPrefix + "user type provided:", usertype, "usertype in DB:", usertype_db
                sys.stdout.flush()
                db_cursor.close()
                db_conn.close()
                FailReport = FinalFail_PrintPrefix + glob_test_name + "test failed: user" + email + "made via API doesn't match its parameters in DB (" + usertype + " != " + usertype_db + ")."
                assert False, FailReport
                exit(253)  # shouldn't reach this
        else:
            if usertype_db != None:
                print ERR_PrintPrefix + "properties from database do not match properties provided at partnered user create API call."
                print ERR_PrintPrefix + "user type was omitted in request, but user type in DB is not NULL: ", usertype_db
                sys.stdout.flush()
                db_cursor.close()
                db_conn.close()
                FailReport = FinalFail_PrintPrefix + glob_test_name + "test failed: user" + email + "made via API doesn't match its parameters in DB (" + usertype + " != " + usertype_db + ")."
                assert False, FailReport
                exit(253)  # shouldn't reach this

        if url:
            if url_db != url.decode('utf-8'):
                print ERR_PrintPrefix + "properties from database do not match properties provided at partnered user create API call."
                print ERR_PrintPrefix + "user url provided:", url, "user url in DB:", url
                sys.stdout.flush()
                db_cursor.close()
                db_conn.close()
                FailReport = FinalFail_PrintPrefix + glob_test_name + "test failed: user" + email + "made via API doesn't match its parameters in DB (" + url + " != " + url_db + ")."
                assert False, FailReport
                exit(253)  # shouldn't reach this
        else:
            if url_db != None:
                print ERR_PrintPrefix + "properties from database do not match properties provided at partnered user create API call."
                print ERR_PrintPrefix + "url was omitted in request, but url in DB is not NULL: ", url_db
                sys.stdout.flush()
                db_cursor.close()
                db_conn.close()
                FailReport = FinalFail_PrintPrefix + glob_test_name + "test failed: user" + email + "made via API doesn't match its parameters in DB (" + url + " != " + url_db + ")."
                assert False, FailReport
                exit(253)  # shouldn't reach this

        # now check  partnersUsers was linked w/ id from b_user (v_user is a view and has data from b_user):
        # id from v_user must have partner_id  in partnersUsers and this partner must have same properties as partner selected from partners in query1 above
        query = "select id from v_user where email = \"" + email + "\"" + " and login = email " + ";"
        try:
            db_cursor.execute(query)
            row = db_cursor.fetchone()
            userid = row[0]
        except exceptions.StandardError as e:
            print ERR_PrintPrefix + "Exception working w/ database using query '" + query + "' :"
            sys.stdout.flush()
            print e
            sys.stdout.flush()
            db_cursor.close()
            db_conn.close()
            FailReport = FinalFail_PrintPrefix + glob_test_name + "test failed: exception while working w/ database using query '" + query + "' . Abort."
            assert False, FailReport
            exit(253)
        query = "select partnerid from partnersUsers where  userid = " + str(userid) + ";"
        try:
            db_cursor.execute(query)
            if db_cursor.rowcount == 0:
                print ERR_PrintPrefix + "Error: user is added but not linked as partner in partnersUsers table."
                print ExtraInfo_PrintPrefix + "query '" + query + "' returned 0 elements."
                sys.stdout.flush()
                db_cursor.close()
                db_conn.close()
                FailReport = FinalFail_PrintPrefix + glob_test_name + "test failed: user '" + email + "' is added but not linked as partner in partnersUsers table."
                assert False, FailReport
                exit(253)
            else:
                row = db_cursor.fetchone()
                partnerid_sel2 = row[0];
                if partnerid_sel2 != partnerid_sel1:
                    print ERR_PrintPrefix + "Error: user is added but linked with wrong partner."
                    print ExtraInfo_PrintPrefix + "partner id from query '" + query1 + "' doesn't match partner id from query '" + query + "'."
                    sys.stdout.flush()
                    db_cursor.close()
                    db_conn.close()
                    FailReport = FinalFail_PrintPrefix + glob_test_name + "test failed: user '" + email + "' is added but linked with wrong partner. Abort."
                    assert False, FailReport
                    exit(253)
        except exceptions.StandardError as e:
            print ERR_PrintPrefix + "Exception working w/ database using query '" + query + "' :"
            print e
            sys.stdout.flush()
            db_cursor.close()
            db_conn.close()
            FailReport = FinalFail_PrintPrefix + glob_test_name + "test failed: exception while working w/ database using query '" + query + "' . Abort."
            assert False, FailReport
            exit(253)

        # prove the user was created within test execution time
        query = "select date_register from b_user where email = \"" + email + "\"" + " and login = email " + ";"
        try:
            db_cursor.execute(query)
            row = db_cursor.fetchone()
            date_created = row[0];
        except exceptions.StandardError as e:
            print ERR_PrintPrefix + "Exception working w/ database using query '" + query + "' :"
            print e
            sys.stdout.flush()
            db_cursor.close()
            db_conn.close()
            FailReport = FinalFail_PrintPrefix + glob_test_name + "test failed: exception while working w/ database using query '" + query + "' . Abort."
            assert False, FailReport
            exit(253)
        time_created = mktime(strptime(str(date_created), "%Y-%m-%d %H:%M:%S"))
        now = time()
        if (int(time_created) < int(glob_test_start_time)) or (
            int(time_created) > int(now)):  # use int() - ignore differences less then second - time may be not in sync
            print ExtraInfo_PrintPrefix + "user is present in DB, correctly linked as partnered, but its creation time is not within test execution time (via query '" + query + "')."
            print ExtraInfo_PrintPrefix + "time_created:", time_created
            print ExtraInfo_PrintPrefix + "test start time", glob_test_start_time
            print ExtraInfo_PrintPrefix + "time compared:", now
            print "Make sure that local and remote time are in sync, use timeserver to check, i.e. 'ntpdate ntp4.stratum2.ru' ."
            sys.stdout.flush()
            db_cursor.close()
            db_conn.close()
            FailReport = FinalFail_PrintPrefix + glob_test_name + "test failed: user found, correctly linked, but creation time is not within test exection time."
            assert False, FailReport
            exit(253)
        # now all DB checks pass
        return True
    # end of check_db_for_partnered_user()


def check_partnercount_api(db_conn, suppress_output=False):
    """ Проверка отчета о количестве зарегистрированных в системе партнеров.
                *. Запросить к-во в БД
                *. Запросить API, свалидировав по схеме ответ
                *. Сравнить результат запросов."""

    global glob_test_result_state

    countindb = get_partnercount_from_db(db_conn, suppress_output)
    countinapi = get_partnercount_from_api()
    if countindb != countinapi:
        print ERR_PrintPrefix + "Count from database:", countindb, ", but count reported by API:", countinapi
        sys.stdout.flush()
        db_conn.close()
        FailReport = FinalFail_PrintPrefix + glob_test_name + "test failed: partner count API call returns value that doesn't match one in database."
        assert False, FailReport
        exit(111)  # shouldn't reach this.

    # now check that fails w/ bad/empty api keys
    print AllOK_PrintPrefix + " [+] Checking that no access w/ wrong API key.."
    req_url = cfg_api_url + "/partner/count"
    headers = {'Authorization': 'Basic YXBhaGVyZWhjOjlzQmJPeTZk'}
    resp = send_http_request(req_url, 'get', "requesting partner count (no API key).", headers=headers)
    if resp.status_code == 200:
        json_okay = True
        try:
            js = resp.json()
        except Exception as e:
            print ERR_PrintPrefix + "Exception when parsing response as json: ", e
            json_okay = False
        print ERR_PrintPrefix + "Got success code without access key requesting partner count via url '" + url + "'. Response code", resp.status_code, ". Abort."
        print ERR_PrintPrefix + "Response text:", resp.text
        sys.stdout.flush()
        db_conn.close()
        if json_okay:
            FailReport = FinalFail_PrintPrefix + glob_test_name + "test failed: succeess code in reply for partner count request without access key."
            check_partnercount_response_schema(js, suppress_output)
        else:
            FailReport = FinalFail_PrintPrefix + glob_test_name + "test failed: succeess code in reply for partner count request without access key + invalid json in API response."
        assert False, FailReport
        exit(111)
    else:
        js = resp.json()
        check_nokey_response_schema(js, suppress_output=True)
    print AllOK_PrintPrefix + "   .. passed."

    print AllOK_PrintPrefix + " [+] Checking that no access w/ wrong API key containing SQL injection attempt. "
    for fake_api_key in glob_fake_keys:
        req_url = cfg_api_url + "/partner/count?key=" + fake_api_key
        headers = {'Authorization': 'Basic YXBhaGVyZWhjOjlzQmJPeTZk', 'key': fake_api_key}
        resp = send_http_request(req_url, 'get', "requesting partner count (using API key w/ SQL injection attempt).",
                                 headers=headers)
        if resp.status_code == 200:
            print ERR_PrintPrefix + "Got success code when using bad access key in response to partner count request via url '" + req_url + "'. Response code", resp.status_code, ". Abort."
            report_SQL_injection_status(db_conn, glob_user2inject)
            print ERR_PrintPrefix + "Response text:", resp.text
            sys.stdout.flush()
            db_conn.close()
            FailReport = FinalFail_PrintPrefix + glob_test_name + "test failed: succeess code in reply for partner count request with bad access key."
            assert False, FailReport
            exit(111)
    else:
        js = resp.json()
        check_nokey_response_schema(js, suppress_output=True)

    # after all attempts make sure the SQL injection code had no impact
    print "Checking SQL injection didn't happen.."
    if report_SQL_injection_status(db_conn, glob_user2inject):
        FailReport = FinalFail_PrintPrefix + glob_test_name + "test failed: successfull SQL injection detected: ", glob_user2inject, "used in injected SQL statement is found in the database in b_user table."
        db_conn.close()
        assert False, FailReport
        exit(111)  # shouldn't reach this.
    print AllOK_PrintPrefix + "  .. passed."


def std_logon_checks(db_conn, suppress_output=False):
    """ набор проверок для API авторизации:
                *. нельзя зайти с случайными логином и паролем
                *. нельзя зайти с случайными email и паролем
                *. нельзя зайти с случайными email и паролем имеющегося пользователя + аналогично без API key
                *. нельзя зайти с неверным паролем от правильного пользователя
                *. нельзя зайти с пустым именем пользователя, но правильным паролем одного из пользователей
                *. нельзя зайти с пустым паролем для существующего пользователя
                *. нельзя зайти с пустым паролем для отсутствующего пользователя
                *. нельзя зайти с пустым паролем и пустым пользователем
                *. ответы соответствуют json схемам для успешного входа и для отказа во входе
                *. можно зайти с правильным логином и паролем
                *. без API key войти не получится имея правильные login/pass, аналогично с неверным API key
                *. можно зайти под email вместо логина при корректном пароле
                *. повтор проверок выше с использованием отсутсвующего и неверного ключа и с попытками сделать SQL инъекцию."""

    global glob_test_result_state

    if not suppress_output:
        print AllOK_PrintPrefix + "The standard logon checks will take a few minutes: there will be more than", 9 * (
        len(glob_fake_keys) + 2), "logon attempts made."

    # *. нельзя зайти с случайными логином и паролем
    state, string = lk_api_login(fake_user, fake_passwd, suppress_output)
    if state:
        db_conn.close()
        FailReport = FinalFail_PrintPrefix + glob_test_name + "test failed: able to login w/ random user/password pair: '" + fake_user + "' / '" + fake_passwd + "'"
        assert False, FailReport
        exit(111)  # shouldn't reach this.
    else:
        if not suppress_output:
            print AllOK_PrintPrefix + "   .. passed: bad logon attempt rejected."
        pass

    # *. нельзя зайти с случайными email и паролем
    state, string = lk_api_login(glob_fake_email, fake_passwd, suppress_output)
    if state:
        db_conn.close()
        FailReport = FinalFail_PrintPrefix + glob_test_name + "test failed: able to login w/ random email/password pair: '" + fake_user + "' / '" + fake_passwd + "'"
        assert False, FailReport
        exit(111)  # shouldn't reach this.
    else:
        if not suppress_output:
            print AllOK_PrintPrefix + "   .. passed: bad logon attempt rejected."
        pass

    # *. нельзя зайти с случайными email и паролем имеющегося пользователя
    state, string = lk_api_login(glob_fake_email, cfg_admin_user_passwd, suppress_output=suppress_output)
    if state:
        db_conn.close()
        FailReport = FinalFail_PrintPrefix + glob_test_name + "test failed: able to login w/ random email '" + glob_fake_email + "' and password from valid user '" + cfg_admin_user + "'"
        assert False, FailReport
        exit(111)  # shouldn't reach this.
    else:
        if not suppress_output:
            print AllOK_PrintPrefix + "   .. passed: bad logon attempt rejected."
        pass
    # аналогично без API key
    try_login_no_key(db_conn, glob_fake_email, cfg_admin_user_passwd, suppress_output=suppress_output)

    #         *. нельзя зайти с неверным паролем от правильного пользователя
    state, string = lk_api_login(cfg_admin_user, fake_passwd, suppress_output)
    if state:
        db_conn.close()
        FailReport = FinalFail_PrintPrefix + glob_test_name + "test failed: able to login w/ wrong password for valid user: '" + cfg_admin_user + "' / '" + fake_passwd + "'"
        assert False, FailReport
        exit(111)  # shouldn't reach this.
    else:
        if not suppress_output:
            print AllOK_PrintPrefix + "   .. passed: bad logon attempt rejected."
        pass
    # аналогично без API key
    try_login_no_key(db_conn, cfg_admin_user, fake_passwd, suppress_output=suppress_output)
    if not suppress_output:
        print AllOK_PrintPrefix + "   .. passed: bad logon and no key attempt rejected."
    # аналогично с неправильным API key и SQL инъекции в нём не влияют на результат.
    for badkey in glob_fake_keys:
        try_login_no_key(db_conn, cfg_admin_user, fake_passwd, badkey, suppress_output=suppress_output)
        if not suppress_output:
            print AllOK_PrintPrefix + "   .. passed: bad logon with wrong key attempt rejected."

    # *. нельзя зайти с пустым именем пользователя, но правильным паролем одного из пользователей
    state, string = lk_api_login("", cfg_admin_user_passwd, suppress_output)
    if state:
        db_conn.close()
        FailReport = FinalFail_PrintPrefix + glob_test_name + "test failed: able to login w/ empty user / random password pair: '' / '" + fake_passwd + "'"
        assert False, FailReport
        exit(111)  # shouldn't reach this.
    else:
        if not suppress_output:
            print AllOK_PrintPrefix + "   .. passed: bad logon attempt rejected."
        pass
    # аналогично без API key
    try_login_no_key(db_conn, "", cfg_admin_user_passwd, suppress_output=suppress_output)
    if not suppress_output:
        print AllOK_PrintPrefix + "   .. passed: bad logon and no key attempt rejected."
    # аналогично с неправильным API key и SQL инъекции в нём не влияют на результат.
    for badkey in glob_fake_keys:
        try_login_no_key(db_conn, "", cfg_admin_user_passwd, badkey, suppress_output=suppress_output)
        if not suppress_output:
            print AllOK_PrintPrefix + "   .. passed: bad logon with wrong key attempt rejected."

    # *. нельзя зайти с пустым паролем для существующего пользователя
    state, string = lk_api_login(cfg_admin_user, "", suppress_output)
    if state:
        db_conn.close()
        FailReport = FinalFail_PrintPrefix + glob_test_name + "test failed: able to login w/ valid user / empty password pair: '" + cfg_admin_user + "' / ''"
        assert False, FailReport
        exit(111)  # shouldn't reach this.
    else:
        if not suppress_output:
            print AllOK_PrintPrefix + "   .. passed: bad logon attempt rejected."
        pass
    # аналогично без API key
    try_login_no_key(db_conn, "", cfg_admin_user_passwd, suppress_output=suppress_output)
    if not suppress_output:
        print AllOK_PrintPrefix + "   .. passed: bad logon and no key attempt rejected."
    # аналогично с неправильным API key и SQL инъекции в нём не влияют на результат.
    for badkey in glob_fake_keys:
        try_login_no_key(db_conn, "", cfg_admin_user_passwd, badkey, suppress_output=suppress_output)
        if not suppress_output:
            print AllOK_PrintPrefix + "   .. passed: bad logon with wrong key attempt rejected."

    # *. нельзя зайти с пустым паролем для отсутствующего пользователя
    state, string = lk_api_login(fake_user, "", suppress_output)
    if state:
        db_conn.close()
        FailReport = FinalFail_PrintPrefix + glob_test_name + "test failed: able to login w/ random user / empty password pair: '" + fake_user + "' / ''"
        assert False, FailReport
        exit(111)  # shouldn't reach this.
    else:
        if not suppress_output:
            print AllOK_PrintPrefix + "   .. passed: bad logon attempt rejected."
        pass
    # аналогично без API key
    try_login_no_key(db_conn, fake_user, "", suppress_output=suppress_output)
    if not suppress_output:
        print AllOK_PrintPrefix + "   .. passed: bad logon and no key attempt rejected."
    # аналогично с неверным API key, тут же проверки на SQL injection в API key
    for badkey in glob_fake_keys:
        try_login_no_key(db_conn, fake_user, "", badkey, suppress_output)
        if not suppress_output:
            print AllOK_PrintPrefix + "   .. passed: bad logon with wrong key attempt rejected."

    # *. нельзя зайти с пустым паролем и пустым пользователем
    state, string = lk_api_login("", "", suppress_output)
    if state:
        db_conn.close()
        FailReport = FinalFail_PrintPrefix + glob_test_name + "test failed: able to login w/ empty user / empty password pair: '" + fake_user + "' / ''"
        assert False, FailReport
        exit(111)  # shouldn't reach this.
    else:
        if not suppress_output:
            print AllOK_PrintPrefix + "   .. passed: bad logon attempt rejected."
        pass
    # аналогично без API key
    try_login_no_key(db_conn, "", "", suppress_output=suppress_output)
    if not suppress_output:
        print AllOK_PrintPrefix + "   .. passed: bad logon and no key attempt rejected."
    # аналогично с неверным API key, тут же проверки на SQL injection в API key
    for badkey in glob_fake_keys:
        try_login_no_key(db_conn, "", "", badkey, suppress_output)
        if not suppress_output:
            print AllOK_PrintPrefix + "   .. passed: bad logon with wrong key attempt rejected."

    # *. можно зайти с правильным логином и паролем
    state, string = lk_api_login(cfg_admin_user, cfg_admin_user_passwd, suppress_output)
    if not state:
        db_conn.close()
        FailReport = FinalFail_PrintPrefix + glob_test_name + "test failed: failed to login w/ predefined user/password pair available in DB: '" + cfg_admin_user + "' / '" + cfg_admin_user_passwd + "'"
        assert False, FailReport  # shouldn't reach this codepoint.
        exit(111)  # shouldn't reach this.
    else:
        if not suppress_output:
            print AllOK_PrintPrefix + "   .. passed: good login attempt accepted."
        pass

    # без API key войти не получится имея правильные login/pass
    try_login_no_key(db_conn, cfg_admin_user, cfg_admin_user_passwd, suppress_output=suppress_output)
    if not suppress_output:
        print AllOK_PrintPrefix + "   .. passed: bad logon and no key attempt rejected."
    # с некорректным API key войти не получится имея правильные login/pass , тут же проверяется SQL injection
    for badkey in glob_fake_keys:
        try_login_no_key(db_conn, cfg_admin_user, cfg_admin_user_passwd, badkey, sqlinjuser=glob_user2inject,
                         suppress_output=suppress_output)
        if not suppress_output:
            print AllOK_PrintPrefix + "   .. passed: bad logon with wrong key attempt rejected."

    cfg_admin_user_email = get_user_email_from_DB(db_conn, cfg_admin_user)
    if cfg_admin_user_email:
        #         *. можно войти под email пользователя вместо его имени (правильным логином и паролем)
        state, string = lk_api_login(cfg_admin_user_email, cfg_admin_user_passwd, suppress_output)
        if not state:
            db_conn.close()
            FailReport = FinalFail_PrintPrefix + glob_test_name + "test failed: failed to login w/ email/password pair available in DB: '" + cfg_admin_user + "' / '" + cfg_admin_user_passwd + "'"
            assert False, FailReport  # shouldn't reach this codepoint.
            exit(111)  # shouldn't reach this.
        else:
            if not suppress_output:
                print AllOK_PrintPrefix + "   .. passed: good logon attempt using user email as login accepted."
            pass

        # без API key войти не получится имея правильные email/pass
        try_login_no_key(db_conn, cfg_admin_user_email, cfg_admin_user_passwd, suppress_output=suppress_output)
        if not suppress_output:
            print AllOK_PrintPrefix + "   .. passed: good logon and no key attempt rejected."

        # с некорректным API key войти не получится имея правильные email/pass , тут же проверяется SQL injection
        for badkey in glob_fake_keys:
            try_login_no_key(db_conn, cfg_admin_user_email, cfg_admin_user_passwd, badkey, suppress_output)
        if not suppress_output:
            print AllOK_PrintPrefix + "   .. passed: good logon with wrong key attempt rejected."
    else:
        print Warn_PrintPrefix + "admin user '" + cfg_admin_user + "' has no email in DB, omitting email checks."

    # now after all attempts make sure the SQL injection code had no impact
    if report_SQL_injection_status(db_conn, glob_user2inject):
        FailReport = FinalFail_PrintPrefix + glob_test_name + "test failed: successfull SQL injection detected: ", glob_user2inject, "used in injected SQL statement is found in the database in b_user table."
        db_conn.close()
        assert False, FailReport
        exit(111)  # shouldn't reach this.

    # repeat once just to get 'string' to return with
    state, string = lk_api_login(cfg_admin_user_email, cfg_admin_user_passwd, suppress_output)
    if not state:
        db_conn.close()
        FailReport = FinalFail_PrintPrefix + glob_test_name + "test failed: failed to login w/ email/password pair available in DB: '" + cfg_admin_user + "' / '" + cfg_admin_user_passwd + "'"
        assert False, FailReport  # shouldn't reach this codepoint.
        exit(111)  # shouldn't reach this.
    return string
    # end of std_logon_checks()


def password_recovery_and_check(db_conn, user, key, suppress_output=False):
    """ вызывает смену пароля для username + доп. проверки результата .
        в качестве user может быть либо user либо email от тестового пользователя testuser ,
        поскольку check_testuser_password_changed вызываемый внутри заточен на них."""

    global glob_test_result_state

    # вставить тестового пользователя с заведомо известным паролем
    mk_test_user(db_conn, testuser, glob_email)

    # запросить восстановление пароля, проверить ответы
    start_mail_check_time = datetime.datetime.now()
    resp = request_password_recovery(db_conn, user, key=cfg_api_key)
    resp.encoding = 'utf-8'
    js = resp.json()  # safety is already verified inside request_password_recovery(..)
    if resp.status_code == 200:
        check_authrec_response_schema(js, False, suppress_output)
    else:
        check_authrec_response_schema(js, True, suppress_output)

    if not check_testuser_password_changed(db_conn, testuser):
        print ERR_PrintPrefix + "Found entry with the same password as injected for test."
        sys.stdout.flush()
        db_conn.close()
        assert False, "User password was not changed after request for password recovery."
        exit(253)  # shouldn't reach this.

    # *. нельзя зайти используя старый пароль с email пользователя
    print AllOK_PrintPrefix + " [+] Trying to logon w/ old password..",
    state, string = lk_api_login(glob_email, cfg_admin_user_passwd, suppress_output=True)
    if state:
        print ERR_PrintPrefix + "Got token '" + string + "' from remote: logged in w/ OLD  login/password pair:", testuser, " / ", cfg_admin_user_passwd, " after passing request to change password."
        sys.stdout.flush()
        db_conn.close()
        FailReport = FinalFail_PrintPrefix + glob_test_name + "test failed: able to login w/ old password after passing request to change password. Abort."
        assert False, FailReport
        exit(111)  # shouldn't reach this.

    # *. нельзя зайти используя старый пароль с логином пользователя
    state, string = lk_api_login(testuser, cfg_admin_user_passwd, suppress_output=True)
    if state:
        print ERR_PrintPrefix + "Got token '" + string + "' from remote: logged in w/ OLD  login/password pair:", testuser, " / ", cfg_admin_user_passwd, " after passing request to change password."
        sys.stdout.flush()
        db_conn.close()
        FailReport = FinalFail_PrintPrefix + glob_test_name + "test failed: able to login w/ old password after passing request to change password. Abort."
        assert False, FailReport
        exit(111)  # shouldn't reach this.
    print "  .. passed: old password unusable (via both login name and email)."

    # удалить тестового пользователя
    rm_user(db_conn, testuser)

    # check mail w/ password change notify
    if use_tempmail:
        print AllOK_PrintPrefix + "   [+] Checking email sent by remote on password change is OK."
        check_mail_contents(glob_email, start_mail_check_time, u'auth_recovery', "Acceptance test")
        print AllOK_PrintPrefix + "    .. passed."


def request_password_recovery(db_conn, username, key=False, suppress_output=False):
    """ делает запрос на смену пароля для username, возвращает полученный response """
    global glob_test_result_state
    if key != False:
        if key == '':
            req_url = cfg_api_url + "/user/recovery?key=''"
            headers = {'Authorization': 'Basic YXBhaGVyZWhjOjlzQmJPeTZk', 'key': ''}
        else:
            req_url = cfg_api_url + "/user/recovery?key=" + key
            headers = {'Authorization': 'Basic YXBhaGVyZWhjOjlzQmJPeTZk', 'key': key}

        if not suppress_output:
            print AllOK_PrintPrefix + "  [+] Trying to request password change for user '" + username + "'."
        else:
            if not suppress_output:
                print AllOK_PrintPrefix + "  [+] Trying to request password change for user '" + username + "' without key."
    else:
        req_url = cfg_api_url + "/user/recovery"
        headers = {'Authorization': 'Basic YXBhaGVyZWhjOjlzQmJPeTZk'}
        if key == cfg_api_key:
            if not suppress_output:
                print AllOK_PrintPrefix + "  [+] Trying to request password change for user '" + username + "'."
        else:
            if not suppress_output:
                print AllOK_PrintPrefix + "  [+] Trying to request password change for user '" + username + "' using bad key."

    req_params = {"emailOrLogin": username,}
    resp = send_http_request(req_url, 'post', "requesting password change.", headers=headers, data=req_params)
    # verify json is accessible (we don't need return value here)
    resp.json()
    return resp


def mk_test_user(db_conn, username, email):
    """ вставляет в базу запись с тестовым пользователем username и мылом email """
    u_name = 'TestChangePass';
    u_last_name = 'TestChangePass'
    query1 = "insert into b_user (LOGIN,PASSWORD,CHECKWORD,ACTIVE,NAME,LAST_NAME,EMAIL,LID,DATE_REGISTER) " \
             "VALUES ('" + username + "','<J3czR4|c8226ba3c0a3a21050da1bd4806c9984', " \
                                      "'gdUXcVMD60f0335bf8a249d400d818e74e6fe191', " \
                                      "'Y','" + u_name + "', '" + u_last_name + "','" + email + "','s2',NOW());"
    query2 = "select id from b_user where login = '" + username + "';"

    print AllOK_PrintPrefix + "     [+] inserting test user " + username + " to replace password for into database.. '"
    try:
        db_cursor = db_conn.cursor(buffered=True)
        db_cursor.execute(query1)
        # db_conn.commit()  # since autocommit set we 've no need in this anymore
    # Владимир Падалец:
    # там схема такая, нужно сначала insert в b_user, получить id вставленной записи и потом вставить в таблицу  b_uts_user поле вида
    # VALUE_ID => ид_от_b_user
    # UF_NAME => null или 'Тест'
    # UF_LASTNAME => null или 'Тест'
    # UF_SECONDNAME => null или 'Тест'
    # UF_ACTIV => null или 1 - для пользователей покупателей это флаг подтверждения для рассылки, чтобы письма в спам не шли, что-то в этом духе, для партнеров не используется, но любой партнер может стать покупателем и в его ЛК покупателя будет висеть просьба активировать аккаунт если UF_ACTIV не равно 1
    # UF_COMPANY => null - поле заполняется только для полькователей страховых компаний
    except exceptions.StandardError as e:
        print ERR_PrintPrefix + "exception while inserting test user w/ query \"" + query1 + "\" :"
        print e
        sys.stdout.flush()
        db_cursor.close()
        db_conn.close()
        FailReport = FinalFail_PrintPrefix + glob_test_name + "test failed: exception while inserting into DB using query \"" + query1 + "\""
        assert False, FailReport
        exit(253)

    userid = None
    try:
        db_cursor.execute(query2)
        if db_cursor.rowcount == 1:
            userid = db_cursor.fetchone()[0]
        else:
            print ERR_PrintPrefix + "Count of results from query \"" + query2 + "\" is not 1. Unexpected results from DB."
    except exceptions.StandardError as e:
        print ERR_PrintPrefix + "exception while selecting id with query '" + query2 + "' :"
        print e
        sys.stdout.flush()
        db_cursor.close()
        db_conn.close()
        FailReport = FinalFail_PrintPrefix + glob_test_name + "test failed: exception while operating database using query \"" + query2 + "\""
        assert False, FailReport
        exit(253)
    if not userid:
        db_conn.close()
        FailReport = FinalFail_PrintPrefix + glob_test_name + "test failed: exception while operating database using query \"" + query2 + "\""
        FailReport = "Unable to get user id from previous insert statement \"" + query1 + "\". Error operating database."
        assert False, FailReport
        exit(253)

    query3 = "insert into b_uts_user (VALUE_ID, UF_NAME, UF_LASTNAME, UF_SECONDNAME, UF_ACTIV, UF_COMPANY) " \
             "VALUES (" + str(userid) + ",'" + u_name + "','" + u_last_name + "',NULL,NULL,NULL);"
    try:
        db_cursor.execute(query3)
        # db_conn.commit()  # since autocommit set we 've no need in this anymore
    except exceptions.StandardError as e:
        print ERR_PrintPrefix + "exception while executing '" + query3 + "' :"
        print e
        sys.stdout.flush()
        db_cursor.close()
        db_conn.close()
        FailReport = FinalFail_PrintPrefix + glob_test_name + "test failed: exception while operating database using query " + query3
        assert False, FailReport
        exit(253)
    db_cursor.close()
    print AllOK_PrintPrefix + "      .. passed.'"
    # end of mk_test_user()


def check_testuser_password_changed(db_conn, username, suppress_output=False):
    """ проверяет что у пользователя username пароль отличается от того с которым пользователь создавался и возвращает True, False если это не так.
    """
    query = "select id from b_user where login = '" + username + "'" + " and password='<J3czR4|c8226ba3c0a3a21050da1bd4806c9984';"

    if not suppress_output:
        print AllOK_PrintPrefix + "      .. checking test user password has been changed in DB.."
    try:
        db_cursor = db_conn.cursor(buffered=True)
        db_cursor.execute(query)
    except exceptions.StandardError as e:
        print ERR_PrintPrefix + "Exception while executing '" + query + "' :"
        print e
        sys.stdout.flush()
        db_cursor.close()
        db_conn.close()
        FailReport = FinalFail_PrintPrefix + glob_test_name + "test failed: exception while operating database using query " + query
        assert False, FailReport
        exit(253)
    if db_cursor.rowcount == 0:
        db_cursor.close()
        return True
    else:
        db_cursor.close()
        return False


def rm_user(db_conn, username, suppress_output=False):
    """ удаляет пользователя username из таблицы b_user в БД и линк на него в b_uts_user, если такого пользователя нет - возвращает  False иначе True
    """
    query2 = "select id from b_user where login = '" + username + "';"
    try:
        db_cursor = db_conn.cursor(buffered=True)
        db_cursor.execute(query2)
        if db_cursor.rowcount == 0:
            if not suppress_output:
                print AllOK_PrintPrefix + "      .. user'" + username + "' not found."
            db_cursor.close()
            return False
        else:
            userid = db_cursor.fetchone()[0]
    except exceptions.StandardError as e:
        print ERR_PrintPrefix + "exception while executing '" + query2 + "' :"
        print e
        sys.stdout.flush()
        db_cursor.close()
        db_conn.close()
        FailReport = FinalFail_PrintPrefix + glob_test_name + "test failed: exception while operating database using query " + query2
        assert False, FailReport
        exit(253)

    query = "delete from b_user where LOGIN='" + username + "';"
    print AllOK_PrintPrefix + "     [+] deleting test user " + username + " from database after tests.. '"
    try:
        db_cursor = db_conn.cursor(buffered=True)
        db_cursor.execute(query)
        # db_conn.commit()  # since autocommit set we 've no need in this anymore
    except exceptions.StandardError as e:
        print ERR_PrintPrefix + "Exception while executing '" + query + "' :"
        print e
        sys.stdout.flush()
        db_cursor.close()
        db_conn.close()
        FailReport = FinalFail_PrintPrefix + glob_test_name + "test failed: exception while operating database using query " + query
        assert False, FailReport
        exit(253)

    query3 = "delete from b_uts_user where VALUE_ID = " + str(userid) + ";"
    print AllOK_PrintPrefix + "     [+] deleting links for test user " + username + " in b_uts_user table from database after tests.. '"
    try:
        db_cursor = db_conn.cursor(buffered=True)
        db_cursor.execute(query)
        # db_conn.commit()  # since autocommit set we 've no need in this anymore
    except exceptions.StandardError as e:
        print ERR_PrintPrefix + "Exception while executing '" + query3 + "' :"
        print e
        sys.stdout.flush()
        db_cursor.close()
        db_conn.close()
        FailReport = FinalFail_PrintPrefix + glob_test_name + "test failed: exception while operating database using query " + query
        assert False, FailReport
        exit(253)

    db_cursor.close()
    return True


def confirm_no_apikey_in_DB(db_conn, key):
    """ возвращает True если ключа нет в apiKeys в БД, иначе валит тест.
    """
    # abort if we passed value w/ injection to our DB related function
    if has_sql_sensitive(key):
        FailReport = "Unsafe test - programmer error. Please fix."
        db_conn.close()
        assert False, FailReport
        exit(253)
    # make sure that there's no such key in DB
    query = "select id from apiKeys where `key`='" + key + "';"
    try:
        db_cursor = db_conn.cursor(buffered=True)
        db_cursor.execute(query)
    except exceptions.StandardError as e:
        print ERR_PrintPrefix + "Exception working w/ database using query '" + query + "' :"
        print e
        sys.stdout.flush()
        db_cursor.close()
        db_conn.close()
        FailReport = FinalFail_PrintPrefix + glob_test_name + "test failed: exception while working w/ database using query '" + query + "' . Abort."
        assert False, FailReport
        exit(253)
    if db_cursor.rowcount == 0:
        db_cursor.close()
        return True
    else:
        print ERR_PrintPrefix + "Unexpected situation: our random autogenerated fake key", key, "matched exactly one in the database."
        print ERR_PrintPrefix + "Either database misconfigured or random generator is broken."
        print ERR_PrintPrefix + "Please fix script or database. Abort."
        sys.stdout.flush()
        db_cursor.close()
        db_conn.close()
        FailReport = "Script misconfigured: the fake API access key has been found in apiKeys table in DB."
        assert False, FailReport
        exit(253)  # shouldn't reach this.


def check_change_auth_api(db_conn, email, suppress_output=False):
    """ Действия для запроса смены пароля:
        вставить тестового пользователя с заведомо известным паролем
        запросить восстановление пароля, проверить ответы
        удалить тестового пользователя
        вставить тестового пользователя с заведомо известным паролем
        попытаться cделать sql инъекции при запросе восстановления пароля, убедится, что ответ как при ошибке
        убедиться что в БД нет артифакта-вставки из sql инъекции
    """
    global glob_test_result_state

    # this must fail - no key
    resp = request_password_recovery(db_conn, testuser)
    resp.encoding = 'utf-8'
    js = resp.json()  # safety is already verified inside request_password_recovery(..)
    if resp.status_code == 200:
        print ERR_PrintPrefix + "Without access key the change authorisation request for user '" + testuser + "'has been passed. Got response code", resp.status_code, "."
        print ERR_PrintPrefix + "Response json:", js
        sys.stdout.flush()
        db_conn.close()
        assert False, "Able to request password recovery without key."
        exit(111)  # shouldn't reach this
    else:
        check_nokey_response_schema(js, suppress_output)
        if not suppress_output:
            print AllOK_PrintPrefix + "  .. passed: key is required, json reply is valid."

    # this must fail - wrong key
    if not suppress_output:
        print AllOK_PrintPrefix + " [+] Trying to request password change w/ invalid API key.."
    for badkey in glob_fake_keys:
        resp = request_password_recovery(db_conn, testuser, key=badkey)
        resp.encoding = 'utf-8'
        js = resp.json()  # safety is already verified inside request_password_recovery(..)
        if resp.status_code == 200:
            print ERR_PrintPrefix + "With bad access key the change authorisation request for user '" + testuser + "'has been passed. Got response code", resp.status_code, "."
            print ERR_PrintPrefix + "Response json:", js
            report_SQL_injection_status(db_conn, glob_user2inject)
            sys.stdout.flush()
            db_conn.close()
            FailReport = "Able to request password recovery with wrong key."
            assert False, FailReport
            exit(111)  # shouldn't reach this
        else:
            check_nokey_response_schema(js, suppress_output)
    if not suppress_output:
        print AllOK_PrintPrefix + "  .. passed: incorrect key doesn't work, json reply is valid."

    for request_for in testuser, email:
        print AllOK_PrintPrefix + " [+] Trying to request password change for", request_for, ".."
        password_recovery_and_check(db_conn, request_for, cfg_api_key, suppress_output)
        print AllOK_PrintPrefix + "   .. passed."

    print AllOK_PrintPrefix + " [+] Trying to request password change with invalid username.."
    resp = request_password_recovery(db_conn, fake_user, key=cfg_api_key)
    resp.encoding = 'utf-8'
    js = resp.json()  # safety is already verified inside request_password_recovery(..)
    if resp.status_code == 200:
        print ERR_PrintPrefix + "Password change API returned successfull response code for random username '" + fake_user + "' ."
        sys.stdout.flush()
        check_authrec_response_schema(js, False, suppress_output)
        db_conn.close()
        FailReport = FinalFail_PrintPrefix + glob_test_name + "test failed: successfull responce for password change request for random (thus - not present in DB) user."
        assert False, FailReport
        exit(111)  # shouldn't reach this.
    else:
        check_authrec_response_schema(js, True, suppress_output)
    print AllOK_PrintPrefix + "  .. passed."

    print AllOK_PrintPrefix + " [+] Trying to request password change with invalid username and no key.."
    resp = request_password_recovery(db_conn, fake_user)
    resp.encoding = 'utf-8'
    js = resp.json()  # safety is already verified inside request_password_recovery(..)
    if resp.status_code == 200:
        print ERR_PrintPrefix + "Password change API returned successfull response code for random username '" + fake_user + "' and no access key ."
        sys.stdout.flush()
        db_conn.close()
        check_authrec_response_schema(js, False, suppress_output)
        FailReport = FinalFail_PrintPrefix + glob_test_name + "test failed: successfull responce for password change request for random (thus - not present in DB) user and without access key."
        assert False, FailReport
        exit(111)  # shouldn't reach this.
    else:
        check_nokey_response_schema(js, suppress_output)
    print AllOK_PrintPrefix + "  .. passed."

    print AllOK_PrintPrefix + " [+] Trying to request password change with invalid username and wrong key.."
    for badkey in glob_fake_keys:
        resp = request_password_recovery(db_conn, fake_user, key=badkey)
        resp.encoding = 'utf-8'
        js = resp.json()  # safety is already verified inside request_password_recovery(..)
        if resp.status_code == 200:
            print ERR_PrintPrefix + "Password change API returned successfull response code for random username '" + fake_user + "' and random access key ."
            report_SQL_injection_status(db_conn, glob_user2inject)
            sys.stdout.flush()
            check_authrec_response_schema(js, False, suppress_output)
            db_conn.close()
            FailReport = FinalFail_PrintPrefix + glob_test_name + "test failed: successfull responce for password change request for random (thus - not present in DB) user and with random access key."
            assert False, FailReport
            exit(111)  # shouldn't reach this.
        else:
            check_nokey_response_schema(js, suppress_output)
    print AllOK_PrintPrefix + "  .. passed."

    ## FIXME: get back this block when https://tsystem.atlassian.net/browse/CHEB-1013 will be fixed or sqlinj_ch_auth_checks will have workaround for it.
    #  sqlinj_ch_auth_checks(db_conn,testuser,email)

    # убедиться что в БД нет артифакта-вставки из sql инъекции (помимо закоментированного строкой выше инъекции ещё в попытках с кривыми API key)
    if report_SQL_injection_status(db_conn, glob_user2inject):
        FailReport = FinalFail_PrintPrefix + glob_test_name + "test failed: successfull SQL injection detected: ", glob_user2inject, "used in injected SQL statement is found in the database in b_user table."
        db_conn.close()
        assert False, FailReport
        exit(111)  # shouldn't reach this.


def sqlinj_ch_auth_checks(db_conn, testuser, email, suppress_output=False):
    ## FIXME: make workaround for https://tsystem.atlassian.net/browse/CHEB-1013 (as fixing it is long term job)

    global glob_test_result_state

    print AllOK_PrintPrefix + " [+] Trying to make SQL injection while requesting password change.."
    # вставить тестового пользователя с заведомо известным паролем
    mk_test_user(db_conn, testuser, glob_email)

    # попытаться cделать sql инъекции при запросе восстановления пароля, убедится, что ответ как при ошибке
    users_with_injection = get_SQL_injection_strings(testuser, glob_user2inject)
    if not suppress_output:
        print AllOK_PrintPrefix + "     .. there will be", len(users_with_injection), "attempts for this.."
    attempt = 1
    for user in users_with_injection:
        if not suppress_output:
            print AllOK_PrintPrefix + "     ..  [ + ] username: '" + user + "' (attempt ", attempt, ").. ",
        resp = request_password_recovery(db_conn, user, suppress_output=True)
        resp.encoding = 'utf-8'
        js = resp.json()  # safety is already verified inside request_password_recovery(..)
        if check_testuser_password_changed(db_conn, testuser, suppress_output=True):
            print ERR_PrintPrefix + "Password has changed in DB, but we 've sent username altered w/ SQL injection:"
            print ERR_PrintPrefix + "Username was \"" + user + "\" and password was changed for user '" + testuser + "'."
            report_SQL_injection_status(db_conn, glob_user2inject)
            print ExtraInfo_PrintPrefix + "Last response from remote API:\n------cut-------\n", resp.text, "\n------cut-------\n"
            sys.stdout.flush()
            db_conn.close()
            FailReport = FinalFail_PrintPrefix + glob_test_name + "test failed: user password was changed after request for password recovery with usernames containing SQL injection code."
            assert False, FailReport
            exit(253)  # shouldn't reach this.

        if resp.status_code == 200:
            print ERR_PrintPrefix + "      .. failed: password change API returned successfull response code for bad username '" + user + "' ."
            sys.stdout.flush()
            check_authrec_response_schema(js, False, suppress_output=False)
            db_conn.close()
            FailReport = FinalFail_PrintPrefix + glob_test_name + "test failed: successfull responce for password change request for user '" + user + "' that cannot exist in DB as is."
            assert False, FailReport
            exit(111)  # shouldn't reach this.
        else:
            check_authrec_response_schema(js, True, suppress_output=True)
        if not suppress_output:
            print ".. passed. "
        attempt = attempt + 1
    print


def check_logon_api(db_conn, suppress_output=False):
    """ Полный набор проверок авторизации:
               *. все проверки из std_logon_checks()
               *. подстановка SQL выражений в поля пользователя и пароля не влияют на вышеперечисленные проверки
               *. SQL сущность из подстановок предыдущего пункта не появляется в БД (no sql injection)
        возвращает token string для cfg_admin_user (который задаётся в config.json и всегда есть в базе), либо валит тест если проверки не прошли"""

    global glob_test_result_state
    admin_logged_in_token = std_logon_checks(db_conn)
    check_tokens_are_unique()
    ## FIXME: move to security pull, enable when this block when https://tsystem.atlassian.net/browse/CHEB-1013 will be fixed
    #  # try to make sql injection
    #  sqlinj_logon_checks(db_conn)
    #
    #  print AllOK_PrintPrefix + "[+] Repeating same common checks after attempt to breaking w/ sql injection.."
    #  # repeat same checks silently to make sure attempts to make sql injection made no damage.
    #  std_logon_checks(db_conn,suppress_output=True)
    #  print AllOK_PrintPrefix + "  .. passed."
    ### end of function check_logon_api()


def try_login_no_key(db_conn, user, passwd, key=False, sqlinjuser=False, suppress_output=False):
    """ получает на вход параметры пользователя, проверяет ответ на валидность согласно json схеме, если вдруг вход удачен - валит тест
        Возвращает True если авторизация не удалась
    """
    global glob_test_result_state

    if key != False:
        # trap for improper use.
        if key == cfg_api_key:
            db_conn.close()
            assert False, "Script misconfigured. Correct key shouldn't ever appear here."
            exit(111)  # shouldn't reach this.
        if key == '':
            req_url = cfg_api_url + "/token?key=''"
            headers = {'Authorization': 'Basic YXBhaGVyZWhjOjlzQmJPeTZk', 'key': ''}
        else:
            req_url = cfg_api_url + "/token?key=" + key
            headers = {'Authorization': 'Basic YXBhaGVyZWhjOjlzQmJPeTZk', 'key': key}
    else:
        req_url = cfg_api_url + "/token"
        headers = {'Authorization': 'Basic YXBhaGVyZWhjOjlzQmJPeTZk'}

    req_params = {"login": user,
                  "password": passwd
                  }
    resp = send_http_request(req_url, 'post', "requesting login API (using wrong or missing or empty API key).", headers=headers, data=req_params, suppress_output=True)
    js = resp.json()
    if resp.status_code == 200:
        if key == '' or key:
            print ERR_PrintPrefix + "With wrong access key '" + key + "' login for user '" + user + "' w/ password '" + passwd + "'has been passed. Got response code", resp.status_code, "."
        else:
            print ERR_PrintPrefix + "Without access key login for user '" + user + "' w/ password '" + passwd + "'has been passed. Got response code", resp.status_code, "."
        print ERR_PrintPrefix + "Request url:", req_url
        print ERR_PrintPrefix + "Response text:", resp.text
        report_SQL_injection_status(db_conn, glob_user2inject)
        if key == '' or key:
            db_conn.close()
            assert False, "Able to logon with wrong key."
            exit(253)
        else:
            db_conn.close()
            assert False, "Able to logon without key."
            exit(111)  # shouldn't reach this.
    else:
        if not suppress_output:
            print AllOK_PrintPrefix + "    .. login for user '" + user + "' w/ password '" + passwd + "' failed with incorrect key. Got response code", resp.status_code, "."
            sys.stdout.flush()
            if cfg_show_response:
                print AllOK_PrintPrefix + "     ..response text:", resp.text
                sys.stdout.flush()
    # если вдруг отдаст ответ как при success с статус отличным от 200 - свалится тут на проверке схемы.
    check_nokey_response_schema(js, suppress_output)
    return True


################################################################################
#### конфигурация/настройки начинаются тут
################################################################################
# статус прохода теста
glob_test_result_state = True

glob_test_start_time = None  # инициализация глобальной переменной
# имя теста,в частности должна быть во всех FailReport
glob_test_name = "lk_api_check"
# показывать ответ сервера при запросах
cfg_show_response = config[u'verbosity'][u'print_server_responses']
cfg_api_url = config[u'host'][u'apiUrl'].encode('utf-8')
cfg_api_key = config[u'host'][u'key'].encode('utf-8')
cfg_admin_user = config[u'personal_cabinet'][u'adm_user'].encode('utf-8')
cfg_admin_user_passwd = config[u'personal_cabinet'][u'adm_user_password'].encode('utf-8')
environment = config[u'system'][u'env_name'].encode('utf-8')
# when checking tokens are unique collect tokens from this login count:
retry_logon = 100  # FIXME - move this into config
# generate fakes: user,password,API_key
userlength = random.choice([8, 12, 15, 50])  # FIXME: add testing for sizes more than length of DB field (50)
fake_user = get_random_string(size=userlength)
rnd_pass_length = random.choice([6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 129, 254])
fake_passwd = get_random_string(size=rnd_pass_length)
glob_fake_key = get_random_string(size=len(cfg_api_key))
# username used in SQL injection attempts.
glob_user2inject = "sinj" + get_random_string(size=userlength - 4)
if glob_user2inject == fake_user:
    # try to regen
    glob_user2inject = "sinj" + get_random_string(size=userlength - 4)
    if glob_user2inject == fake_user:
        print ERR_PrintPrefix + "two times we have same random string. Cannot continue w/ bad random data."
        FailReport = FinalFail_PrintPrefix + glob_test_name + "test failed: random number generator failure - cannot continue."
        assert False, FailReport
        exit(254)

userlength = random.choice([8, 12, 15, 50])
# this one is used for push/pop operations w/ DB + API requests use it.
testuser = get_random_string(size=userlength)
if testuser == fake_user:
    # try to regen
    testuser = get_random_string(size=userlength)
    if testuser == fake_user:
        print ERR_PrintPrefix + "two times we have same random string. Cannot continue w/ bad random data."
        FailReport = FinalFail_PrintPrefix + glob_test_name + "test failed: random number generator failure - cannot continue."
        assert False, FailReport
        exit(254)
# generate fakes: email
random_base = get_random_string()
random_suffix = get_random_string(size=2)
random_domain = random_base + '.' + random_suffix
glob_fake_email = "fakemail@" + random_domain
cfg_email = config[u'buyer'][u'email']
if cfg_email != u'':
    glob_email = cfg_email
    print Warn_PrintPrefix + "Skipping temp-mail.ru related checks: buyer email from config.json is not empty."
    use_tempmail = False
    print AllOK_PrintPrefix + "Using email from configuration file '", email, "' as buyer email."
else:
    use_tempmail = True
    try:
        tm = TempMail()
        glob_email = tm.get_email_address()
    except requests.exceptions.ConnectionError as e:
        print Warn_PrintPrefix + "temp-mail.ru is failing. Got exception initializing temp-mail: ", e
        print Warn_PrintPrefix + "Skipping temp-mail.ru related checks: temp-mail.ru service is not working."
        random_base2 = get_random_string()
        random_suffix2 = get_random_string(size=2)
        random_domain2 = random_base2 + '.' + random_suffix2
        email = "nosuchmail@" + random_domain2
        print Warn_PrintPrefix + "Will use", email, "as email."
        use_tempmail = False
## generate fake keys array w/ SQL injection attempts and one fake key 
# direct utf8 seem to be not supported by requests.post(), so quote 1st.
glob_fake_keys = get_SQL_injection_strings(cfg_api_key, glob_user2inject)
for index, item in enumerate(glob_fake_keys):
    glob_fake_keys[index] = urllib.quote(item)
glob_fake_keys.append(glob_fake_key)
glob_fake_keys.append('')


################################################################################
###  if being run directly
################################################################################
if __name__ == '__main__':
    lk_api_check()

