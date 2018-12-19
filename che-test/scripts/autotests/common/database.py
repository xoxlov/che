#!/usr/bin/env python3
# -*- coding: utf-8; -*-
import mysql.connector
import common.logger as logger
import common.config_module as config_module
from common.check_verify import is_equal


class CheDb(object):
    def __init__(self, db_config=None, verbose=False):
        db_config = db_config or config_module.load()["database"]
        self.host = db_config["host"]
        self.port = db_config["port"]
        self.database = db_config["database"]
        self.username = db_config["username"]
        self.password = db_config["password"]
        self.connection = self.open_validate_mysql_connection(verbose=verbose)

    def open_validate_mysql_connection(self, verbose=False):
        try:
            conn = mysql.connector.connect(host=self.host, port=self.port, database=self.database, user=self.username, password=self.password)
            conn.autocommit = True
            if verbose:
                logger.success("DB connected successfully")
            return conn
        except mysql.connector.Error as e:
            logger.fail("DB connection failure %s" % e)
            tabspace = "\n" + " " * 19
            logger.info("Connection parameters:{t}host = '{h}';{t}port = '{p}';{t}database = '{d}';{t}user = '{u}';{t}password = '{w}'".format(
                t=tabspace, h=self.host, p=self.port, d=self.database, u=self.username, w=self.password))
            raise e

    def __del__(self):
        self.connection.close()

    def __enter__(self):
        return self

    def __exit__(self, ttype, value, traceback):
        self.__del__()

    def destroy(self):
        self.__del__()

    def get_disabled_companies_for_partner_id(self, partner_id):
        cursor = self.connection.cursor()
        query = "select distinct cast(propValue as unsigned) from partnerProperties " \
                "where propName='disabled_company' and partnerId='%s';" % partner_id
        try:
            cursor.execute(query)
            company_ids = [company_id[0] for company_id in cursor]
            if company_ids:
                return company_ids
            return False
        finally:
            cursor.close()

    def is_company_blocked(self, company_id):
        cursor = self.connection.cursor()
        query = "select isBlocked from companies where id='%s';" % company_id
        try:
            cursor.execute(query)
            blocked_state = [is_blocked[0] for is_blocked in cursor]
            return bool(blocked_state[0])
        finally:
            cursor.close()

    def get_company_id_by_name(self, company_name):
        cursor = self.connection.cursor()
        query = "select `id` from companies where name='%s';" % company_name
        try:
            cursor.execute(query)
            company_id = [company_id[0] for company_id in cursor]
            return company_id[0] if company_id else False
        finally:
            cursor.close()

    def get_key_for_partner_id(self, partner_id):
        cursor = self.connection.cursor()
        query = "select `key` from apiKeys where partnerId='%s';" % partner_id
        try:
            cursor.execute(query)
            partner_keys = [key[0] for key in cursor]
            return partner_keys[0] if partner_keys else False
        finally:
            cursor.close()

    def get_key_for_partner_code(self, company_code):
        cursor = self.connection.cursor()
        query = "select `key` from apiKeys where partnerId = (select id from partners where code = '%s');" % company_code
        try:
            cursor.execute(query)
            key = [key[0] for key in cursor]
            return key[0] if key else False
        finally:
            cursor.close()

    def get_insurance_companies_list(self, disabled=None):
        cursor = self.connection.cursor()
        try:
            selection = "where isBlocked={0}".format(disabled) if disabled == 1 or disabled == 0 else ""
            cursor.execute("select code, name from companies {0}".format(selection))
            return {code: name for (code, name) in cursor}
        finally:
            cursor.close()

    def get_countries_list(self, enabled=None):
        cursor = self.connection.cursor()
        try:
            selection = "where isInsurable={0}".format(enabled) if enabled == 1 or enabled == 0 else ""
            cursor.execute("select code from countries {0}".format(selection))
            return [code[0] for code in cursor]
        finally:
            cursor.close()

    def get_countries_names(self):
        cursor = self.connection.cursor()
        try:
            cursor.execute("select code, name from countries")
            return {code: name for (code, name) in cursor}
        finally:
            cursor.close()

    def get_dollar_exchange_rate(self):
        cursor = self.connection.cursor()
        try:
            cursor.execute("select rate from currencyRate where dateRate=CURDATE() and code='USD'")
            result = [float(decimal[0]) for decimal in cursor]
            return result[0] if result else 0.0
        finally:
            cursor.close()

    def get_euro_exchange_rate(self):
        cursor = self.connection.cursor()
        try:
            cursor.execute("select rate from currencyRate where dateRate=CURDATE() and code='EUR'")
            result = [float(decimal[0]) for decimal in cursor]
            return result[0] if result else 0.0
        finally:
            cursor.close()

    def verify_policy_data_in_database_by_task_id(self, task_id, price, check_parent_task_only=False):
        operation_name = "Check task for policy and price in database"
        logger.start(operation_name)
        if task_id is None:
            return self.finish_skip(operation_name + " (Task id was not received)")
        total_summ = 0.0
        try:
            # check if parent task exists in database
            self.find_task_id(task_id)
            logger.success("The parent task '%s' found in database" % task_id)
            if check_parent_task_only:
                logger.warning("Policy creation is in progress, no need to check any further")
                return self.finish_success(operation_name)
            # get child task that created policy for parent task
            for child_task_id in self.get_task_id_list_to_create_policy(task_id):
                logger.success("The child task '%s' to create policy found in database" % child_task_id)
                # verify that database has records about created policy
                for policy_id in self.get_policy_ids_by_task_id(child_task_id):
                    logger.success("The policy '%s' made by task '%s' found in database" % (policy_id, child_task_id))
                # check the calculations for task were successfully made
                for calculation_id in self.get_policy_calculation_by_task_id(child_task_id):
                    logger.success("The calculation '%s' for created policy found in database" % calculation_id)
                    # get prices for selected calculation and calculate total summ
                    for db_price in self.get_policy_price_by_calculation_id(calculation_id):
                        logger.success("The calculated price '%.2f' found in database" % db_price)
                        total_summ += db_price
            return self.finish_success(operation_name) \
                if self.is_price_equal_total_summ(total_summ, price) \
                else self.finish_fail(operation_name)
        except ValueError:
            logger.warning("Check supervisor status on remote host and restart it if needed ('sudo service supervisor restart')")
            return self.finish_fail(operation_name)

    def verify_avia_policy_data_in_database_by_task_id(self, task_id, calc_id):
        operation_name = "Check task for avia policy and price in database"
        logger.start(operation_name)
        if task_id is None:
            return self.finish_skip(operation_name + " (Task id was not received)")
        try:
            # check if parent task exists in database
            self.find_task_id(task_id)
            logger.success("The parent task '%s' found in database" % task_id)
            calculation_code_in_database = \
                self.execute_query("select uuid from tasks where id='%s'" % task_id)[0][0]
            is_equal(calculation_code_in_database, calc_id, "Calculation code for task '%s'" % task_id)
            # get child task that created policy for parent task
            for child_task_id in self.get_task_id_list_to_create_avia_policy(task_id):
                logger.success("The child task '%s' to create policy found in database" % child_task_id)
                # verify that database has records about created policy
                for policy_id in self.get_policy_ids_by_task_id(child_task_id):
                    logger.success("The policy '%s' made by task '%s' found in database" % (policy_id, child_task_id))
            return self.finish_success(operation_name)
        except ValueError:
            logger.warning("Check supervisor status on remote host and restart it if needed ('sudo service supervisor restart')")
            return self.finish_fail(operation_name)

    def verify_policies_payment_system_by_task_id(self, task_id, payment_system, check_parent_task_only):
        operation_name = "Check payment system for policies"
        logger.start(operation_name)
        if task_id is None:
            return self.finish_skip(operation_name + " (Task id was not received)")
        try:
            # check if parent task exists in database
            self.find_task_id(task_id)
            logger.success("The parent task '%s' found in database" % task_id)
            if check_parent_task_only:
                logger.warning("Policy creation is in progress, no need to check any further")
                return self.finish_success(operation_name)
            logger.info("Expected payment system: '%s'" % self.get_payment_system_name_by_code(payment_system))
            logger.info("Expected payment system id: '%s'" % self.get_payment_system_id_by_code(payment_system))

            # get child task that created policy for parent task
            result = True
            for child_task_id in self.get_task_id_list_to_create_policy(task_id):
                logger.success("The child task '%s' to create policy found in database" % child_task_id)
                # verify that database has records about created policy
                for policy_id in self.get_policy_ids_by_task_id(child_task_id):
                    logger.success("The policy '%s' made by task '%s' found in database" % (policy_id, child_task_id))
                    result = is_equal(actual_value=self.get_policy_payment_system_id_by_policy_id(policy_id),
                                      expected_value=self.get_payment_system_id_by_code(payment_system),
                                      value_name="Policy transaction payment system") \
                             and result
            return self.finish_success(operation_name) \
                if result \
                else self.finish_fail(operation_name)
        except ValueError:
            logger.warning("Check supervisor status on remote host and restart it if needed ('sudo service supervisor restart')")
            return self.finish_fail(operation_name)

    def verify_policy_payment_system(self, policy_id, payment_system):
        query = "select paymentSystemId from transactions where id=select transactionId from policiesTransactions where policyId=%s" % policy_id
        cursor = self.connection.cursor()
        try:
            cursor.execute(query)
            paymentSystemId = [psid for psid in cursor]
            if len(paymentSystemId) != 1:
                msg = "Payment System for policy '%s'" % policy_id
                logger.fail(msg + " is found in database")
                raise ValueError("No " + msg + " is found in database")
            if paymentSystemId[0] == payment_system:
                return True
            return False
        finally:
            cursor.close()

    def find_task_id(self, task_id):
        cursor = self.connection.cursor()
        try:
            cursor.execute("select id from tasks where id='%s'" % task_id)
            tasks = [ids[0] for ids in cursor]
            if len(tasks) != 1:
                msg = "Task with id '%s'" % task_id
                logger.fail(msg + " is found in database")
                raise ValueError("No " + msg + " is found in database")
            return tasks
        finally:
            cursor.close()

    def get_task_id_list_to_create_policy(self, task_id):
        try:
            cursor = self.connection.cursor()
            cursor.execute("select id from tasks where code in ('CreatePolicy', 'CreateConfirmPolicy') and taskId='%s'" % task_id)
            tasks_to_create_policy = [ids[0] for ids in cursor]
            if not tasks_to_create_policy:
                msg = "Task to create policy with parent task_id '%s' (code 'CreatePolicy' or 'CreateConfirmPolicy')" % task_id
                logger.fail(msg + " is found in database")
                raise ValueError("No " + msg + " is found in database")
            return tasks_to_create_policy
        finally:
            cursor.close()

    def get_task_id_list_to_create_avia_policy(self, task_id):
        try:
            cursor = self.connection.cursor()
            cursor.execute("select id from tasks where code in ('CreateSingleAviaPolicy') and taskId='%s'" % task_id)
            tasks_to_create_policy = [ids[0] for ids in cursor]
            if len(tasks_to_create_policy) == 0:
                msg = "Task to create policy with parent task_id '%s' (code 'CreateSingleAviaPolicy')" % task_id
                logger.fail(msg + " is found in database")
                raise ValueError("No " + msg + " is found in database")
            return tasks_to_create_policy
        finally:
            cursor.close()

    def get_policy_ids_by_task_id(self, task_id):
        try:
            cursor = self.connection.cursor()
            cursor.execute("select id from policies where taskId='%s'" % task_id)
            policy_id_created = [ids[0] for ids in cursor]
            if len(policy_id_created) == 0:
                msg = "Policy for task '%s'" % task_id
                logger.fail(msg + " is found in database")
                raise ValueError("No " + msg + " is found in database")
            return policy_id_created
        finally:
            cursor.close()

    def get_policy_calculation_by_task_id(self, task_id):
        try:
            cursor = self.connection.cursor()
            cursor.execute("select calculationId from policies where taskId='%s'" % task_id)
            calculation_id_list = [ids[0] for ids in cursor]
            if len(calculation_id_list) == 0:
                msg = "Calculations for task '%s'" % task_id
                logger.fail(msg + " were found in database")
                raise ValueError("No " + msg + " were found in database")
            return calculation_id_list
        finally:
            cursor.close()

    def get_policy_price_by_calculation_id(self, calculation_id):
        try:
            cursor = self.connection.cursor()
            cursor.execute("select price from calculations where id=%s" % calculation_id)
            price_calculated = [float(prices[0]) for prices in cursor]
            if len(price_calculated) == 0:
                msg = "Calculated price for calculation '%s'" % calculation_id
                logger.fail(msg + " is found in database")
                raise ValueError("No " + msg + " is found in database")
            return price_calculated
        finally:
            cursor.close()

    def get_countries_from_euro_zone(self):
        try:
            cursor = self.connection.cursor()
            query = "SELECT c.code FROM countryGroups cg " \
                    "LEFT JOIN countriesCountryGroups ccg ON ccg.countryGroupId = cg.id " \
                    "LEFT JOIN countries c ON c.id = ccg.countryId " \
                    "WHERE cg.`code` = 'europe'"
            cursor.execute(query)
            return [code[0] for code in cursor]
        finally:
            cursor.close()

    def is_price_equal_total_summ(self, total_summ, price):
        if price is None:
            return logger.warning("Check policy price with expected value (Price was not received): Skipped") and False
        msg = "The policy price in database (%.2f) is equal to expected (%.2f)" % (total_summ, price)
        if total_summ == price:
            return logger.success(msg) or True
        elif abs(total_summ - price) <= 0.5:
            # Calculation accuracy depends on the companies rules, so final values can be rounded for database.
            # Acceptable difference between calculated and finally processed price is taken as 0.50 Rub.
            logger.success(msg)
            return logger.warning("The price in database is not equal to the calculated price (difference = %s)"
                                  % round(abs(total_summ - price), 2)) or True
        else:
            return logger.fail(msg) and False

    def finish_success(self, message):
        logger.finishSuccess(message)
        logger.print_empty_line()
        return True

    def finish_fail(self, message):
        logger.finishFail(message)
        logger.print_empty_line()
        return False

    def finish_skip(self, message):
        logger.finishSkipped(message)
        logger.print_empty_line()
        return True

    def get_sport_name_by_code(self, code, competition=False):
        cursor = self.connection.cursor()
        try:
            cursor.execute("select * from sports where code='%s' and isCompetition=%s" % (code, int(competition)))
            sport_name = [sport[1] for sport in cursor]
            return sport_name[0] if sport_name else None
        finally:
            cursor.close()

    def get_country_group_by_code(self, code):
        cursor = self.connection.cursor()
        try:
            cursor.execute("select * from countryGroups where code='%s'" % code)
            group_name = [group[2] for group in cursor]
            return group_name[0] if group_name else None
        finally:
            cursor.close()

    def get_country_by_code(self, code):
        cursor = self.connection.cursor()
        try:
            cursor.execute("select * from countries where code='%s'" % code)
            group_name = [group[2] for group in cursor]
            return group_name[0] if group_name else None
        finally:
            cursor.close()

    def is_user_in_database(self, username, verbose=False):
        if verbose:
            logger.info("Looking database for user with login '%s' .." % username)
        query = "select id from users where login='%s';" % username
        cursor = self.connection.cursor()
        try:
            cursor.execute(query)
            user_id_list = [user[0] for user in cursor]
            if len(user_id_list) == 0:
                if verbose:
                    logger.success("User '%s' is not found in database" % username)
                return False
            elif len(user_id_list) == 1:
                if verbose:
                    logger.success("User '%s' is found in database" % username)
                return True
            else:
                logger.error("Unexpected number of results (%s) for query \"%s\": only 1 should appear as result"
                             % (len(user_id_list), query))
                raise ValueError("Unexpected query result while checking user in database")
        finally:
            cursor.close()

    def get_valid_partner_keys(self):
        cursor = self.connection.cursor()
        try:
            cursor.execute("select apiKeys.key from apiKeys;")
            api_keys = [api_key[0] for api_key in cursor]
            return api_keys if api_keys else None
        finally:
            cursor.close()

    def execute_query(self, query):
        cursor = self.connection.cursor()
        try:
            cursor.execute(query)
            result = [x for x in cursor]
            return result if result else []
        finally:
            cursor.close()

    def get_payment_system_id_by_code(self, code):
        cursor = self.connection.cursor()
        try:
            cursor.execute("select id from paymentSystems where code='%s'" % code)
            output = [result[0] for result in cursor]
            return output[0]
        finally:
            cursor.close()

    def get_payment_system_name_by_code(self, code):
        cursor = self.connection.cursor()
        try:
            cursor.execute("select name from paymentSystems where code='%s'" % code)
            output = [result[0] for result in cursor]
            return output[0]
        finally:
            cursor.close()

    def get_policy_payment_system_id_by_policy_id(self, policy_id):
        query = "select t.paymentSystemId from policies as p " \
                "left join policiesTransactions as pt on p.id = pt.policyId " \
                "left join transactions as t on t.id = pt.transactionId " \
                "where p.id = '%s'" % policy_id
        cursor = self.connection.cursor()
        try:
            cursor.execute(query)
            payment_system_id = [x[0] for x in cursor]
            return payment_system_id[0] if payment_system_id else -1
        finally:
            cursor.close()

    def get_blocked_companies(self):
        query = "select id from cherehapa_funk.companies where isBlocked=1"
        cursor = self.connection.cursor()
        try:
            cursor.execute(query)
            return [x[0] for x in cursor]
        finally:
            cursor.close()


if __name__ == "__main__":  # self check
    db = CheDb(config_module.load()["database"])
    del db
