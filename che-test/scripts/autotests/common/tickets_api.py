# -*- coding: utf-8; -*-
import urllib.parse
import datetime
import os
import tempfile
import shutil
import zipfile

import common.logger as logger
from common.request import send_request_api_partner, download_file_by_url
from common.json_functions import validate_json_by_schema
from common.config_module import load, get_value_from_config
from common.system import function_name
from common.database import CheDb
from common.check_verify import is_equal

# substitution parameters for tickets api calculation request
calc_subst = {
    "key": "key",
    "action": "action",
    "method": "method",
    "date_start": "if[date_start]",
    "date_end": "if[date_end]",
    "company": "if[company]",
    "imputed_avia_cargo": "if[imputed.avia_cargo]",
    "imputed_delay_regular": "if[imputed.delay_regular]",
    "imputed_cancel_travel": "if[imputed.cancel_travel]",
    "imputed_avia_accident": "if[imputed.avia_accident]",
    "imputed_delay_dock": "if[imputed.delay_dock]",
    "params_price_imputed_avia_cargo": "if[params][price][imputed.avia_cargo]",
    "params_price_imputed_delay_regular": "if[params][price][imputed.delay_regular]",
    "params_price_imputed_cancel_travel": "if[params][price][imputed.cancel_travel]",
    "params_price_imputed_avia_accident": "if[params][price][imputed.avia_accident]",
    "params_price_imputed_delay_dock": "if[params][price][imputed.delay_dock]",
    "tourists": "if[tourists]",
    "tourist_birthday": "ord[tourists][0][birthDay]",
    "tourist_lastname": "ord[tourists][0][lastName]",
    "tourist_firstname": "ord[tourists][0][firstName]",
    "buyer_email": "ord[buyer][email]",
    "buyer_lastname": "ord[buyer][lastName]",
    "buyer_firstname": "ord[buyer][firstName]",
    "refid": "refid"
}
# substitution parameters for tickets api confirmation request
conf_subst = {
    "key": "key",
    "calculation_code": "calculationCode",
    "confirm_action": "confirm_action",
    "action": "action",
    "method": "create_params[method]",
    "date_start": "create_params[if][date_start]",
    "date_end": "create_params[if][date_end]",
    "company": "create_params[if][company]",
    "imputed_avia_cargo": "create_params[if][imputed.avia_cargo]",
    "imputed_delay_regular": "create_params[if][imputed.delay_regular]",
    "imputed_cancel_travel": "create_params[if][imputed.cancel_travel]",
    "imputed_avia_accident": "create_params[if][imputed.avia_accident]",
    "imputed_delay_dock": "create_params[if][imputed.delay_dock]",
    "params_price_imputed_avia_cargo": "create_params[if][params][price][imputed.avia_cargo]",
    "params_price_imputed_delay_regular": "create_params[if][params][price][imputed.delay_regular]",
    "params_price_imputed_cancel_travel": "create_params[if][params][price][imputed.cancel_travel]",
    "params_price_imputed_avia_accident": "create_params[if][params][price][imputed.avia_accident]",
    "params_price_imputed_delay_dock": "create_params[if][params][price][imputed.delay_dock]",
    "tourists": "create_params[if][tourists]",
    "tourist_birthday": "create_params[ord][tourists][0][birthDay]",
    "tourist_lastname": "create_params[ord][tourists][0][lastName]",
    "tourist_firstname": "create_params[ord][tourists][0][firstName]",
    "buyer_email": "create_params[ord][buyer][email]",
    "buyer_lastname": "create_params[ord][buyer][lastName]",
    "buyer_firstname": "create_params[ord][buyer][firstName]",
    "refid": "create_params[refid]"
}


def construct_tickets_api_request(**kwargs):
    """Construct the tickets api request with given parameters. Can be used for both calculation and confirmation request type.

    :param kwargs: named parameters corresponding to the keys from substitution dictionaries
    :return: string that represents the tickets api request with given parameters
    """
    http = "http:" + get_value_from_config("[u'api'][u'url']").replace("/v2", "/v1") + "/imputed.json"
    if "http" in kwargs.keys():
        http = kwargs.pop("http")

    # check if "tourist_list" list is present
    additional_tourists = []
    if "tourist_list" in kwargs.keys() and isinstance(kwargs["tourist_list"], list):
        additional_tourists = kwargs.pop("tourist_list")

    # Config values are taken from external config
    config = load("config/tickets.json")
    options = {
        "key": urllib.parse.unquote(config[u'request_key']),  # key may be already in quoted format, so fix it
        "confirm_action": None,
        "calculation_code": None,
        "action": "new",
        "method": "imputed",
        "date_start": "default",
        "date_end": "default",
        "company": "independence",
        "tourists": 1,
        "imputed_avia_accident": None,
        "imputed_avia_cargo": None,
        "imputed_cancel_travel": None,
        "imputed_delay_dock": None,
        "imputed_delay_regular": None,
        "params_price_imputed_avia_accident": None,
        "params_price_imputed_avia_cargo": None,
        "params_price_imputed_cancel_travel": None,
        "params_price_imputed_delay_dock": None,
        "params_price_imputed_delay_regular": None,
        "tourist_birthday": config[u'tourist_birthday'],
        "tourist_lastname": config[u'tourist_lastname'],
        "tourist_firstname": config[u'tourist_firstname'],
        "buyer_email": config[u'buyer_email'],
        "buyer_lastname": config[u'buyer_lastname'],
        "buyer_firstname": config[u'buyer_firstname'],
        "refid": config[u'refid']
    }

    if "special" in kwargs.keys():
        if kwargs["special"] == "url_without_parameters":
            return http
        elif kwargs["special"] == "url_with_key_only":
            return http + "?key=" + options["key"]
        elif not kwargs["special"]:
            pass
        else:
            raise ValueError("%s: incorrect function use, no valid parameter 'special' given" % function_name())

    # replace default values in the parameters dict
    for item in kwargs:
        if item not in options.keys():
            logger.warning("%s: parameter '%s' cannot be evaluated as request parameter, skipped" % (function_name(), item))
            continue
        options[item] = str(kwargs[item])

    # set start date and end date equal to empty value if requested
    if options["date_start"] == False:
        options["date_start"] = ""
    if options["date_end"] == False:
        options["date_end"] = ""

    # if start date is default then set start date to '+10 days' from today
    if options["date_start"] == "default":
        options["date_start"] = (datetime.date.today()+datetime.timedelta(days=10)).strftime("%d.%m.%Y")
    # if end date is default then set end date to '+10 days' from date_start or
    #     if start date is not in valid format then set end date to '+20 days' from today
    if options["date_end"] == "default":
        try:
            options["date_end"] = (datetime.datetime.strptime(options["date_start"], "%d.%m.%Y") + datetime.timedelta(days=10)).strftime("%d.%m.%Y")
        except Exception:
            options["date_end"] = (datetime.date.today() + datetime.timedelta(days=20)).strftime("%d.%m.%Y")

    # clear the dict from missing values
    options = {key: options[key] for key in options.keys() if options[key] not in [None, "None"]}

    # translate parameters names into request names
    if "calculation_code" not in options.keys():
        # create calculation request
        options = {calc_subst[key]:options[key] for key in options}
    else:
        # create confirmation request
        options = {conf_subst[key]: options[key] for key in options}
        options.update({"create_params[action]": options["action"]})
        options["action"] = options["confirm_action"]
        options.pop("confirm_action")

    # if additional tourists list given - check and add them to the perameters list
    if additional_tourists:
        for index, tourist in enumerate(additional_tourists):
            if not isinstance(tourist, dict):
                logger.warning("Parameter 'tourist_list' should be the list in format: "
                               "[{\"lastname\":\"LName\", \"firstname\":\"FName\", \"birthday\":\"DD.MM.YYYY\"}, ...]")
                raise ValueError("%s: incorrect value of 'tourist_list' parameter is used." % function_name())
            person = {"create_params[ord][tourists][%s][lastName]" % str(index + 1): tourist.get("lastname"),
                      "create_params[ord][tourists][%s][firstName]" % str(index + 1): tourist.get("firstname"),
                      "create_params[ord][tourists][%s][birthDay]" % str(index + 1): tourist.get("birthday")}
            options.update(person)

    # return full URL
    request = http + "?" + urllib.parse.urlencode(options)
    return request


def execute_tickets_api_policy_creation(tc_name, **kwargs):
    """Execute tickets api algorythm for policy creation. See for reference and
    algorythm description http://docs.cherehapa.ru/private/policy/ticketsCreate.

    :param tc_name: test case name
    :param kwargs: named parameters corresponding to the keys from substitution dictionaries
    :return: True if the policy was created and downloaded successfully or False otherwise
    """
    request_data = {"calculation request": construct_tickets_api_request(**kwargs)}
    request_data["calculation response"] = \
        send_calculation_request_and_get_response(tc_name, request_data["calculation request"])
    if not request_data["calculation response"]:
        return False

    # if calculation was successful - construct and send confirmation request
    calculation_code = request_data["calculation response"].get("calculationCode")
    kwargs.update({"calculation_code": calculation_code, "confirm_action": "confirm"})
    request_data["confirmation request"] = construct_tickets_api_request(**kwargs)
    request_data["first confirmation response"] = \
        send_first_confirmation_request_and_get_response(tc_name,
                                                         request_data["confirmation request"])
    if not request_data["first confirmation response"]:
        print_tickets_api_dict_info(request_data)
        return False

    # if first confirmation response was successful then make second confirmation request
    request_data["second confirmation response"] = \
        send_second_confirmation_request_and_get_response(tc_name,
                                                          request_data["confirmation request"])
    if not request_data["second confirmation response"]:
        print_tickets_api_dict_info(request_data)
        return False

    # confirmation was successful - check database
    with CheDb() as db:
        db.verify_avia_policy_data_in_database_by_task_id(
            task_id=request_data["second confirmation response"].get("orderId"),
            calc_id=calculation_code
        )

    # download and store policy archive
    if not download_and_verify_policy_archive(request_data["second confirmation response"]):
        return False

    logger.success("Successfully processed orderId=%s with Tickets API"
                   % request_data["second confirmation response"].get("orderId"))
    return True


def send_calculation_request_and_get_response(req_name, calculation_request):
    request_name = "'%s' tickets calculation request" % req_name
    result, response = send_request_api_partner(
        [(request_name, calculation_request, 200)],
        schema_for_success="tickets_api_calculation_success_schema",
        schema_for_error="api_error_without_description")
    if not result:
        logger.fail(request_name)
        return False
    return response


def send_first_confirmation_request_and_get_response(req_name, confirmation_request):
    # first confirmation request should return json {'success': False},
    # policy has been already created by this moment
    request_name = "'%s' tickets first confirmation request" % req_name
    result, response = send_request_api_partner(
        [(request_name, confirmation_request, 200)],
        schema_for_success="false_only_json",
        schema_for_error="api_error_without_description")
    if not result:
        logger.fail(request_name)
        return False
    return response


def send_second_confirmation_request_and_get_response(req_name, confirmation_request):
    # maximum number of attempts to try to get correct response after confirmation request
    MAX_ATTEMPT = 10
    request_name = "'%s' tickets second confirmation request" % req_name
    for attempt in range(MAX_ATTEMPT):
        # second confirmation request should return succesful json with link to the document
        result, response = send_request_api_partner(
            [("%s, attempt %s" % (request_name, attempt + 1), confirmation_request, 200)],
            schema_for_success=None,
            schema_for_error=None)
        # try to get correct json
        if validate_json_by_schema(json_data=response,
                                   schema_name="tickets_api_confirmation_success_schema",
                                   abort_on_exception=False, message_on_exception=False):
            return response
    logger.fail("%s: Failed to get valid policy after %s attempts"
                % (request_name, MAX_ATTEMPT))
    return False


def print_tickets_api_dict_info(print_dict):
    """Function used to print requests and responses for tickets API.

    :param print_dict: dictionary of keys and values to be printed
    """
    for key in sorted(print_dict.keys()):
        logger.info("Tickets API %s: %s" % (key, print_dict[key]))
    return True


def download_and_verify_policy_archive(response_data):
    policy_dir = tempfile.NamedTemporaryFile().name
    os.makedirs(policy_dir)
    url = response_data["policy"]["download"]
    destination = os.path.join(policy_dir, "%s.zip" % response_data["orderId"])
    result = verify_policy_can_be_downloaded(url, destination) \
             and verify_file_size_not_zero(destination) \
             and verify_zip_format_is_correct(destination) \
             and verify_archive_contents(task_id=response_data["orderId"],
                                         destination=destination)
    if result:
        shutil.rmtree(policy_dir, ignore_errors=True)
    else:
        logger.debug("Files available for manual inspection: %s" % destination)
    return result


def verify_policy_can_be_downloaded(url, destination):
    if not download_file_by_url(url, destination,
                                file_description="Policy archive"):
        logger.fail("Tickets API policy archive can be downloaded")
        return False
    return True


def verify_file_size_not_zero(destination):
    if not os.path.getsize(destination):
        logger.fail("Tickets API policy archive has correct size")
        return False
    return True


def verify_zip_format_is_correct(destination):
    if not zipfile.is_zipfile(destination):
        logger.fail("Tickets API policy archive has correct format")
        return False
    return True


def verify_archive_contents(task_id, destination):
    with zipfile.ZipFile(destination) as policy_archive:
        actual_documents_list = [file.filename
                                 for file in policy_archive.filelist]
    with CheDb() as db:
        query = "select policies.code from tasks " \
                "left join policies on policies.taskId = tasks.id " \
                "where tasks.taskId='%s' " \
                "and tasks.`code`='CreateSingleAviaPolicy'" % task_id
        codes_list = db.execute_query(query)
        expected_documents_list = [name[0] + ".pdf" for name in codes_list]
    return is_equal(sorted(actual_documents_list),
                    sorted(expected_documents_list),
                    "Documents list in archive and expected from database")
