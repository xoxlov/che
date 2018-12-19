# -*- coding: utf-8; -*-
import requests
import urllib.request

import common.logger as logger
import common.check_verify as check_verify
from common.json_functions import validate_json_by_schema
from common.config_module import get_value_from_config


http_response_ok = 200


def dump_request_params(req_url, headers=None, data=None):
    """Print request parameters.

    :param req_url: url (string)
    :param headers: json with request headers
    :param data: json with request data
    :return: True
    """
    logger.info("Request details: ")
    logger.info("  URL: %s" % req_url)
    if headers:
        msg_headers = "Headers: [ "
        for key in headers:
            msg_headers = msg_headers + "'" + str(key) + "' => '", headers[key], "'; "
        msg_headers = msg_headers + "]"
        logger.info("  " + msg_headers)
    if data:
        msg_data = "Parameters: [ "
        for key in data:
            msg_data = msg_data + "'" + str(key) + "' => '", data[key], "'; "
        msg_data = msg_data + "]"
        logger.info("  " + msg_data)
    return True


def send_http_request(req_url, method, data=None, headers=None):
    """Return response from requests http library or on exception - print exception,
    request parameters (data and headers) and then fail the test.

    :param req_url: request URL to get response
    :param method: one of http methods to process the request
    :param data: parameter given to 'requests' to get response
    :param headers: parameter given to 'requests' to get response
    :return: 'response' - an object returned from requests http library call or assertion on fail
    """
    supported = {"get": requests.get, "post": requests.post, "delete": requests.delete}
    if method not in supported:
        raise ValueError("Incorrect use of send_http_request(): Method '%s' is not supported" % method)
    if method == "get" and data:
        raise ValueError("Incorrect use of send_http_request(): GET doesn't use request data")
    response = supported[method](req_url, data=data, headers=headers)
    response.encoding = 'utf-8'
    return response


def send_request_api_partner(request_list, schema_for_success=None, schema_for_error=None):
    """Send API request and analyse the response for correct response code and correct json.

    :param request_list: list of requests, each item should consist of (short legend, http-request, expected response)
    :param schema_for_success: json schema name to validate response schema when the response is successful
    :param schema_for_error: json schema name to validate response schema when the response is failed
    :return: tuple (result, response)
    """
    result_send_request = True
    response_json = False
    for (context, request, expected_response) in request_list:
        # print header, send request and get the response
        logger.info("Request description: %s" % context)
        response = send_http_request(request, "get")

        # if response doesn't contain any valid data then notify and continue loop
        #   (too large response, that cannot be proceeded)
        if len(response.text) == 0:
            logger.warning("Warning: Cannot get response for request, possibly too much data")
            logger.info("Request URL: %s" % request)
            result_send_request = False
            continue
        logger.success("The response data is valid")

        # the response is received, so prepare it for processing
        response_json = get_json_from_response(response, request)

        # verify response.status_code is equal to expected response code
        if not check_verify.is_equal(response.status_code, expected_response, "HTTP response code"):
            # request may contain symbols that require encoding before printing
            logger.info("Request URL: %s" % request)
            logger.info("Response: %s" % response.text)
            result_send_request = False

        # validate the json received if the schema is set and json was decoded from response
        json_schema = schema_for_success if response.status_code == 200 else schema_for_error
        if schema_for_success and schema_for_error and response_json:
            if not validate_json_by_schema(response_json, json_schema, context):
                # request may contain symbols that require encoding before printing
                logger.info("Request URL: %s" % request)
                logger.info("Response: %s" % response.text)
                result_send_request = False

        # if json was not decoded successfully then print error and set function result to False
        if not response_json:
            logger.warning("JSON cannot be decoded from response:\n%s" % response.text)
            result_send_request = False
        logger.print_empty_line()
    return result_send_request, response_json


def download_file_by_url(url, destination, file_description="File",
                         abort_on_exception=False):
    """Download file from URL.

    :param url: url of file to download
    :param destination: destination catalogue to store the file
    :param file_description: brief description of target file
    :param abort_on_exception: optional, if True then only print
     exception report in case of validation failure and return
    :return: True if ok, assertion or False if not ok
    """
    try:
        urllib.request.urlretrieve(url, destination)
        logger.success("%s was downloaded successfully" % file_description)
        return True
    except Exception as e:
        logger.error("Attempt to download %s from '%s' failed"
                     % (file_description, url))
        if abort_on_exception:
            raise
        logger.info("Exception when downloading from '%s': %s" % (url, str(e)))
        return False


def get_json_from_response(response, url, data=None, headers=None, abort_on_exception=False):
    """Get and return the json from given response. On exception while json
    decoding print exception report and return False or optionally re-raise.

    :param response: an object returned from requests http library call
    :param url: request URL
    :param data: parameter given to 'requests' to get response
    :param headers: parameter given to 'requests' to get response
    :param abort_on_exception: optional, if True then only print exception report
           in case of validation failure and return False
    :return: response.json() or False on exception print exception report and False
    """
    try:
        return response.json()
    except ValueError as e:
        logger.error("ValueError exception when parsing response as json: %s" % e)
        dump_request_params(url, headers=headers, data=data)
        logger.info("Response text:\n%s" % response.text)
        if abort_on_exception:
            raise
        return False


def make_headers(key=False):
    headers = {
        "Authorization": get_value_from_config("['authorization']", "config/api.json"),
    }
    if key:
        headers["key"] = get_value_from_config("['api']['key']")
    return headers
