# -*- coding: utf-8; -*-
import common.logger as logger
from common.randomize import get_random_string
from common.config_module import get_value_from_config
from common.database import CheDb
from common.system import function_name


# base the injection is constructed with
trigger_injections = [
    "'\'';CUSTOM_USER_INJECTION --' ",
    "'--",
    "/*comment*/",
    "(1=1) OR ",
    "(1=1) AND ",
    " ORDER BY 2/*",
    " login like 'CUSTOM_ADMIN_USER'",
    chr(0xbf) + chr(0x27),
    chr(0xbf) + chr(0x27) + ' AND (CUSTOM_USER_INJECTION) /*',
    chr(0xbf) + chr(0x27) + ' OR (CUSTOM_USER_INJECTION) /*',
    chr(0xbf) + chr(0x27) + ' AND 1=1 /*',
    chr(0xbf) + chr(0x27) + "' union select 1,2/*'",
    chr(0xbf) + chr(0x27) + "' OR username = 'CUSTOM_ADMIN_USER' /*';",
    chr(0xbf) + chr(0x27) + ' OR login = login /*',
    chr(0xbf) + chr(0x27) + ' OR username = login /*',
    '%' + chr(0xbf) + chr(0x27),
    chr(0xbf) + chr(0x27) + "' and login like 'CUSTOM_ADMIN_USER'",
    ";",
    " LIKE '%';",
    " AND 1=1;",
    " UNION ALL SELECT ",
    " AND 1=2;",
]


def get_sql_injection_strings(base_string, user_to_inject):
    """Returns array of strings based on 'base_string' with SQL statement
    inserted at the beginning and added to the end of 'base_string' (those
    common for SQL injection attempts).

    Restriction:
     - if current environment is 'production' return array with base_string
       without modifications.

    :param base_string: string for injection construction
    :param user_to_inject: username to be injected on successful SQL injection
    """
    cfg_admin_user = \
        get_value_from_config("['adm_user']", "config/personal_cabinet.json")
    if base_string == user_to_inject or base_string == cfg_admin_user:
        raise Exception("Wrong use of function %s: initial string for "
                        "injection has restricted value" % function_name())
    if user_to_inject == cfg_admin_user:
        raise Exception("Wrong use of function %s: user to inject cannot be "
                        "same as admin user" % function_name())

    cfg_environment = \
        get_value_from_config("['laravel-api-config']['detectEnvironment']['env']")
    cfg_allow_sql_injection_on_production = \
        get_value_from_config("['allow_sql_injection_on_production']", "config/production.json")
    if cfg_environment == 'production' and not cfg_allow_sql_injection_on_production:
        logger.warning("Executing dangerous SQL injection module on production should be avoided.")
        logger.warning("%s: parameter 'base_string' will be returned as is." % function_name())
        return [base_string]

    inj_password = "<J3czR4|c8226ba3c0a3a21050da1bd4806c9984"
    inj_checkword = "gdUXcVMD60f0335bf8a249d400d818e74e6fe191"
    inj_email = "sql_injection_flag@" + get_random_string(size=6) + "." \
                + get_random_string(size=6) + "." + get_random_string(size=3)
    user_injection = "INSERT INTO users " \
                     "(login, password, checkword, " \
                     "active, name, last_name, email, lid, date_register) " \
                     "VALUES ('%s', '%s', '%s', " \
                     "'Y', 'Test', 'Test1', %s, 's2', NOW());" \
                     % (user_to_inject, inj_password, inj_checkword, inj_email)
    injection_list = [trigger.replace("CUSTOM_USER_INJECTION", user_injection)
                      for trigger in trigger_injections]
    injection_list = [trigger.replace("CUSTOM_ADMIN_USER", cfg_admin_user)
                      for trigger in injection_list]
    result = injection_list[:]
    result += [base_string + trigger for trigger in injection_list]
    result += [trigger + base_string for trigger in injection_list]
    return result


def is_sql_injection_successful_by_user(user_from_injection):
    """Report SQL injection status by checking DB for injected user, if
    successful SQL injection found - returns True, else returns False.

    :param user_from_injection: user to be checked in database.
    """
    error_msg = "Successful SQL injection detected: %s used in injected " \
                "SQL statement is found in the database in users table" \
                % user_from_injection
    fail_msg = "No SQL injection detected within DB"
    with CheDb() as db:
        if db.is_user_in_database(user_from_injection):
            logger.error(error_msg)
            logger.fail(fail_msg)
            return True
    logger.success(fail_msg)
    return False
