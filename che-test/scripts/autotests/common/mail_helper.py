# -*- coding: utf-8; -*-
import tempmail
import dns.resolver
import smtplib
from smtplib import SMTPException
import socket
import json
import datetime
import time

import common.logger as logger
import common.config_module as config_module

SMTP_REPLY_CODE_354 = 354  # RFC5321: "Start mail input; end with <CRLF>.<CRLF>", biggest valid code


class MailHelper(object):

    def __init__(self, app, address=None):
        self.name = "Email check for created policy"
        self.app = app
        self.start_mail_check_time = datetime.datetime.now()
        self.use_tempmail = self.app.policy_data.use_tempmail
        self.do_not_skip_mail_check = address is not None

        tempmail_config = self.read_tempmail_config()
        self.set_mailbox(address)
        self.set_timeouts_from_config(tempmail_config["timeouts"])
        self.set_expected_message_format(tempmail_config["message"])

    def read_tempmail_config(self):
        tempmail_config = config_module.get_dir_by_suffix("che-test/scripts/autotests/config/tempmail.json")
        return config_module.load(tempmail_config)

    def set_mailbox(self, address):
        self.email = address or self.app.policy_data.buyer.email
        self.username, self.email_domain = self.email.split('@')
        self.mailbox = tempmail.TempMail(login=self.username, domain='@' + self.email_domain)

    def set_timeouts_from_config(self, tempmail_config):
        self.mail_delivery_max_wait_time = tempmail_config["mail_delivery_max_wait_time"]
        self.delay_between_mail_check_retry = tempmail_config["delay_between_mail_check_retry"]

    def set_expected_message_format(self, tempmail_config):
        self.skip_subjects = tempmail_config["skip_subjects"]
        self.expected_in_from = tempmail_config["expected_in_from"]
        # self.expect_in_to = tempmail_config["expect_in_to"]  # temp-mail.ru doesn't show 'To' in reply
        self.expected_in_subject = tempmail_config["expected_in_subject"]
        self.expected_in_body = tempmail_config["expected_in_body"]

    @property
    def skipped(self):
        if self.do_not_skip_mail_check:
            return False
        if self.app.policy_data.check_parent_task_only \
                or self.app.policy_data.price is None \
                or self.app.policy_data.task_id is None \
                or not self.use_tempmail:
            return True
        return False

    def check_email_matches_expected_format_and_contents(self):
        def finish_email_was_skipped():
            logger.finishSkipped(self.name)
            logger.print_empty_line()
            return True

        def finish_email_was_successfull():
            logger.success("Email message for '%s' was successfully received" % self.email)
            logger.finishSuccess(self.name)
            logger.print_empty_line()
            return True

        logger.start(self.name)
        if self.skipped:
            return finish_email_was_skipped()

        self.app.set_email_service_tested(True)

        end_mail_check_time = datetime.datetime.now() + datetime.timedelta(seconds=self.mail_delivery_max_wait_time)
        email_is_good = self.does_email_matches_format_and_contents()
        if email_is_good:
            return finish_email_was_successfull()
        while not email_is_good and datetime.datetime.now() < end_mail_check_time:
            if not self.app.webdriver:
                return finish_email_was_skipped()
            logger.info("Mail check was not successfull, will retry in %s seconds.." % self.delay_between_mail_check_retry)
            time.sleep(self.delay_between_mail_check_retry)
            email_is_good = self.does_email_matches_format_and_contents()
            if email_is_good:
                return finish_email_was_successfull()

        mail_count_after_purchase = self.get_mail_count_from_tempmail()
        if mail_count_after_purchase == 0:
            if self.is_mail_exchange_server_available():
                logger.warning("Email messages were NOT received within check time!")
            else:
                logger.warning("Email was NOT delivered, destination Mail Exchange server problem for %s" % self.email)
        else:
            logger.warning("There are %s email messages received for '%s', but none of them match completely" % (mail_count_after_purchase, self.email))
        return finish_email_was_skipped()

    def does_email_matches_format_and_contents(self):
        mail_messages = self.get_mail_messages_from_mailbox()
        for mail in mail_messages:
            if self.is_mail_too_old(mail) or self.check_nose_framework_limitations(mail):
                continue
            if self.is_field_value_from_mail_valid(mail, "mail_from", self.expected_in_from, "From:") and \
                    self.is_field_value_from_mail_valid(mail, "mail_subject", self.expected_in_subject, "Subject:") and \
                    self.is_field_value_from_mail_valid(mail, "mail_text_only", self.expected_in_body, "Body"):
                return True
        return False

    def is_mail_too_old(self, mail):
        return True if datetime.datetime.fromtimestamp(mail.get("mail_timestamp")) < self.start_mail_check_time else False

    def check_nose_framework_limitations(self, mail):
        for matchstr in self.skip_subjects:
            if matchstr in mail.get("mail_subject"):
                # nose framework has a regression bug with unicode chars. Just avoiding unicode in the debug output is
                # an easiest workaround. See https://github.com/nose-devs/nose/issues/680
                # so this should be enabled only if debugging outside of nose
                logger.info("skipping mail matching " + str(matchstr.encode('utf-8')) + "..")
                return True
        return False

    def is_field_value_from_mail_valid(self, mail, field, expected_values, field_name):
        actual_value = mail.get(field)
        if not actual_value:
            logger.warning("Mail message doesn't have '%s'. Raw mail:\n%s"
                           % (field, json.dumps(mail, indent=4, encoding='utf-8', sort_keys=True)))
            return False
        return all([exp in actual_value for exp in expected_values])

    def get_mail_count_from_tempmail(self):
        return len(self.get_mail_messages_from_mailbox())

    def get_mail_messages_from_mailbox(self):
        mailbox_response = self.mailbox.get_mailbox(self.email)
        if isinstance(mailbox_response, dict):
            # dict with 'error' key if mail box is empty
            return self.extract_mail_messages_from_json_dict(mailbox_response)
        if isinstance(mailbox_response, list):
            # list of emails for given email address
            return self.extract_mail_messages_from_json_list(mailbox_response)
        # no valid response from mail server
        logger.error("Error from mail service temp-mail.ru: API returned bad json")
        logger.info("Raw response:\n'%s'" % mailbox_response)
        return []

    def extract_mail_messages_from_json_dict(self, mailbox_response):
        error_no_mail = u"There are no emails yet"
        if mailbox_response.get("error") != error_no_mail:
            self.print_error_from_tempmail(mailbox_response, mailbox_response.get("error"))
        return []

    def extract_mail_messages_from_json_list(self, mailbox_response):
        mail_messages = []
        for response in mailbox_response:
            try:
                if response.get("mail_id"):
                    mail_messages.append(response)
            except KeyError:
                pass
        if not mail_messages:
            self.print_error_from_tempmail(mailbox_response, "API returned bad json")
        return mail_messages

    def print_error_from_tempmail(self, mailbox_response, error):
        logger.error("Error from mail service temp-mail.ru: %s" % error)
        logger.info("Raw response:\n%s" % json.dumps(mailbox_response, indent=4, encoding='utf-8', sort_keys=True))

    def is_mail_exchange_server_available(self):
        try:
            dns_response = dns.resolver.query(self.email_domain, 'MX')
        except dns.exception.DNSException as e:
            logger.warning(e)
            return False
        mx_records_list = [x.exchange.to_text() for x in dns_response]
        count_mx_processed_ok = sum([self.try_to_connect_to_smtp_host(mx_record) for mx_record in mx_records_list])
        if count_mx_processed_ok == 0:
            logger.warning("No email messages delivered for domain '%s'; no working MX hosts found at %s" %
                           (self.email_domain, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            return False
        return True

    def try_to_connect_to_smtp_host(self, host):
        try:
            smtp_connection = smtplib.SMTP(host=host)
            code, message = smtp_connection.noop()
            smtp_connection.quit()
            if code > SMTP_REPLY_CODE_354:
                logger.debug("Mail Exchange server '%s' refused connection: %s" % (host, message))
                return False
            else:
                logger.debug("Mail Exchange server '%s' is okay, got reply %s: %s" % (host, code, message))
                return True
        except (SMTPException, socket.error):
            logger.debug("Mail Exchange server '%s' is inaccessible" % host)
            return False
