# -*- coding: utf-8; -*-
import json
import jsonschema
import common.logger as logger


def validate_json_schema(schema_name):
    """Validate the JSON schema defined in test.

    :param schema_name: string to name the schema, name is coincident with the schema definition file name
    :return: True if validation is successful or on exception print exception report and fail the test
    """
    file_name = 'schemas/%s.json' % schema_name
    file_handler = open(file_name)
    schema_to_validate = json.load(file_handler)
    jsonschema.Draft4Validator.check_schema(schema_to_validate)
    validator = jsonschema.Draft4Validator(schema_to_validate)
    return validator


def validate_json_by_schema(json_data, schema_name, abort_on_exception=False, message_on_exception=True):
    """Validate json data with schema

    :param json_data: json to validate
    :param schema_name: name of schema to validate json on
    :param abort_on_exception: optional, if True then print exception report in case of validation failure and abort .
    :param message_on_exception: optional, if True then message printed on any exception or failure, message is not printed otherwise
    :return: True on success or False otherwise or on exception print exception report and fail the test
    """
    # prepare the validator
    validator = validate_json_schema(schema_name)
    filename = 'schemas/%s.json' % schema_name
    with open(filename) as schema_file:
        schema_json = json.load(schema_file)
    # validate json
    try:
        validator.validate(json_data)
        return True
    except jsonschema.exceptions.ValidationError as e:
        if message_on_exception:
            logger.fail("Validate JSON with schema '%s'" % schema_name)
            logger.debug("The schema '%s' is:\n %s\n" % (schema_name, schema_json))
            logger.debug("Actual JSON:\n %s\n" % json_data)
            logger.debug("The following validation errors found:\n")
            errors = sorted(validator.iter_errors(json_data), key=lambda k: k.path)
            for error in errors:
                for suberror in sorted(error.context, key=lambda k: k.schema_path):
                    logger.debug("%s, %s" % (list(suberror.schema_path), suberror.message))
            logger.debug("Exception text: %s" % e)
        if abort_on_exception:
            assert False, e
        return False
