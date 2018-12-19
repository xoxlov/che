# -*- coding: utf-8; -*-
import os
import random
import re
import json

import common.config_module as config_module
import common.logger as logger
from common.database import CheDb


class PolicyRulesGenerator(object):
    def __init__(self, rules_limitations=None):
        self.name = "Policies data generation"
        generator_config = config_module.load("config/acceptance_vzr.json")["generator"]
        self.data_file_name = generator_config["data_file_name"]
        self.special_file_name = generator_config["special_data_file_name"]
        self.prepare_data_catalog(generator_config["data_catalog"])
        self.rules_dir = config_module.get_dir_by_suffix(generator_config["rules_dir"])
        rules_limitations_default = [
            "ENABLED_COUNTRY_ONLY",
            "NOT_EMPTY_CALCULATION",
            "DOLLAR_IN_EURO_ZONE_DISABLED",
            "ENABLED_OPTIONS_ONLY"
        ]
        self.rules_limitations = rules_limitations or rules_limitations_default

        with CheDb(db_config=config_module.load()["database"], verbose=False) as db:
            self.enabled_companies = db.get_insurance_companies_list(disabled=0)
            self.disabled_countries = db.get_countries_list(enabled=0)
            self.euro_zone_countries = db.get_countries_from_euro_zone()
        self.companies_list = list(filter(lambda x: x in self.enabled_companies, os.listdir(self.rules_dir)))

        self.all_rules = []
        self.special_rules = []

    @property
    def condition_currency_dollar_in_company(self):
        return bool(list(filter(lambda x: x["currency"].upper() == "USD", self.company_policies_list)))

    @property
    def condition_currency_euro_in_company(self):
        return bool(list(filter(lambda x: x["currency"].upper() == "EUR", self.company_policies_list)))

    @property
    def condition_service_abroad_in_company(self):
        return bool(list(filter(lambda x: "abroad" in x["service"].keys(), self.company_policies_list)))

    @property
    def condition_service_foreign_in_company(self):
        return bool(list(filter(lambda x: x["service"].get("foreign"), self.company_policies_list)))

    @property
    def condition_service_multipolicy_in_company(self):
        return bool(list(filter(lambda x: x["service"].get("multipolicy"), self.company_policies_list)))

    @property
    def countries_used_in_company_policies(self):
        country_no_group_list = list(filter(lambda x: isinstance(x.get("country"), str), self.company_policies_list))
        return set([x.get("country") for x in country_no_group_list])

    @property
    def countries_available_for_policies(self):
        return set([x.get("country") for x in self.all_rules])

    @property
    def is_country_list_too_small(self):
        # number of different countries for company should be greater than half of policies amount
        return 2*len(self.countries_used_in_company_policies) <= len(self.company_policies_list)

    def prepare_data_catalog(self, data_catalog_name):
        data_catalog = os.path.abspath(os.path.join(os.getcwd(), data_catalog_name))
        if not os.path.exists(data_catalog):
            os.mkdir(data_catalog)

    def generate_policy_data_list(self):
        logger.start(self.name)
        MANDATORY_POLICIES_AMOUNT = 4
        self.policies_list = []
        for company in self.companies_list:
            self.current_company = company
            logger.info("Generate policy data for '%s'.." % self.enabled_companies[company])
            self.company_policies_list = []
            self.read_all_rules_from_file()
            self.read_current_config_from_file()
            insured_days_list = self.make_list_of_days_to_insure(self.current_config["insuredDays"], MANDATORY_POLICIES_AMOUNT)
            traveller_age_list = self.make_list_of_days_to_insure(self.current_config["age"], MANDATORY_POLICIES_AMOUNT)

            # add scenario for 'abroad' option if possible or add any valid scenario
            self.add_policy_for_abroad() or self.add_policy_for_any_option(insured_days_list[0])
            # add scenario for 'foreign' option if possible or add any valid scenario
            self.add_policy_for_foreign(traveller_age_list[1]) or self.add_policy_for_any_option(insured_days_list[1])
            # add scenario for 'multipolicy' option if possible or add any valid scenario
            self.add_policy_for_multipolicy(insured_days_list[2], traveller_age_list[2]) or self.add_policy_for_any_option(insured_days_list[2])
            # if dollar is not used as currency in scenarios set - then add scenario for dollar
            self.add_policy_for_dollar()
            # if euro is not used as currency in scenarios set - then add scenario for dollar
            self.add_policy_for_euro()
            # if valid scenario for travellers group exists for company - then add scenario for travellers list
            self.add_policy_for_travellers_list()
            # check if number of scenarios is less than MANDATORY_POLICIES_AMOUNT, if so - add another one
            while len(self.company_policies_list) < MANDATORY_POLICIES_AMOUNT:
                if not bool(self.add_policy_for_medicine_only(insured_days_list[3])):
                    break
            # if number of different countries for company less or equal to the half of policies amount - add another scenario
            self.add_policy_for_another_country()
            # add scenario for pair of countries if possible
            self.add_policy_for_country_pair()
            # add scenario for terrritory (country group) if possible
            self.add_policy_for_territory()

            self.policies_list.extend(self.company_policies_list)
            logger.success("Policy data for '%s' generated successfully (%s scenarios)"
                           % (self.enabled_companies[company], len(self.company_policies_list)))

        self.set_cashless_payment_scenarios()
        self.assign_ids_to_policies()
        self.save_policies_list_to_file()
        self.make_report_for_policies_data_conditions()
        logger.finishSuccess(self.name)
        logger.print_empty_line()
        return self.policies_list

    def read_all_rules_from_file(self):
        def read_rules_from_file_to_list(file_name):
            rules_list = []
            rules_file = os.path.join(self.rules_dir, self.current_company, "tests", file_name)
            if os.path.exists(rules_file):
                for single_rule in open(rules_file, "r"):
                    policy = eval(re.findall("'(.*)': {[.]*", single_rule)[0])
                    policy["expected_calculation"] = eval(re.findall("}': ({.*})", single_rule)[0])
                    rules_list.append(policy)
            return rules_list

        self.all_rules = read_rules_from_file_to_list(self.data_file_name)
        self.filter_all_rules()
        self.special_rules = read_rules_from_file_to_list(self.special_file_name)
        self.filter_special_rules()

    def filter_all_rules(self):
        if "ENABLED_COUNTRY_ONLY" in self.rules_limitations:
            self.all_rules = list(filter(lambda x: x["country"] not in self.disabled_countries, self.all_rules))
        if "NOT_EMPTY_CALCULATION" in self.rules_limitations:
            self.all_rules = list(filter(lambda x: x["expected_calculation"] != {}, self.all_rules))
        if "DOLLAR_IN_EURO_ZONE_DISABLED" in self.rules_limitations:
            self.all_rules = list(filter(
                lambda x: not (x["country"] in self.euro_zone_countries)
                          and x["currency"].lower() == "usd", self.all_rules))
        if "ENABLED_OPTIONS_ONLY" in self.rules_limitations:
            insuredDays_enabled_options = list(range(0, 366))
            medicine_enabled_options = [0, 30000, 35000, 40000, 50000, 100000, None]
            accident_enabled_options = [0, 1000, 3000, 5000, 10000, None]
            cargo_enabled_options = [0, 500, 1000, 1500, 2000, None]
            tripCancel_enabled_options = [0, 500, 1000, 1500, 2000, 2500, 3000, 3500, 4000, 4500, 5000, None]
            civilLiability_enabled_options = [0, 10000, 30000, 50000, None]
            pregnancy_enabled_options = [0, 12, 24, 31, None]
            self.all_rules = list(filter(
                lambda x: int(x.get("insuredDays")) in insuredDays_enabled_options
                          and x["service"].get("medicine") in medicine_enabled_options
                          and x["service"].get("accident") in accident_enabled_options
                          and x["service"].get("cargo") in cargo_enabled_options
                          and x["service"].get("tripCancel") in tripCancel_enabled_options
                          and x["service"].get("civilLiability") in civilLiability_enabled_options
                          and x["service"].get("pregnancy") in pregnancy_enabled_options,
                self.all_rules))

    def filter_special_rules(self):
        if "NOT_EMPTY_CALCULATION" in self.rules_limitations:
            self.special_rules = list(filter(lambda x: x["expected_calculation"] != {}, self.special_rules))
        if "ENABLED_COUNTRY_ONLY" in self.rules_limitations:
            # make list of scenarios with countries only
            list_with_countries = [x for x in self.special_rules if x.get("country")]
            list_of_scenarios_to_remove = []
            for rule in list_with_countries:
                # make list of disabled countries from current rule
                disabled_countries_from_rule = [x for x in rule.get("country") if x in self.disabled_countries]
                if disabled_countries_from_rule:
                    list_of_scenarios_to_remove.append(rule)
            # remove scenarios with disabled countries from the original list
            for rule in list_of_scenarios_to_remove:
                self.special_rules.remove(rule)

    def read_current_config_from_file(self):
        config_rules = {}
        enabled_keys = ["age", "dateStart", "insuredDays"]
        for line in open(os.path.join(self.rules_dir, self.current_company, "tests", "config.yml"), "r"):
            line = line.rsplit("\n")[0].lstrip().rsplit(":")
            # line has value like "['insuredDays', ' [1, 16, 30, 31, 60, 90, 180, 366]']" or "['currency', ' [EUR, USD]']"
            if line[0] in enabled_keys:
                config_rules[line[0]] = eval(line[1])
        self.current_config = config_rules

    def make_list_of_days_to_insure(self, original_list, amount):
        new_list = original_list[:]
        if len(new_list) >= amount:
            random.shuffle(new_list)
            return new_list[0:amount]
        while len(new_list) < amount:
            r = random.choice(original_list)
            new_list.append(r)
        return new_list

    def add_policy_for_any_option(self, days):
        rules_list = list(filter(
            lambda x: x["insuredDays"] == days
                      and len(x["service"].keys()) > 1
                      and not x["service"].get("abroad")
                      and not x["service"].get("foreign")
                      and not x["service"].get("multipolicy"),
                            self.all_rules))
        return self.add_single_policy_data_to_the_list(rules_list)

    def add_policy_for_medicine_only(self, days):
        rules_list = list(filter(
            lambda x: x["insuredDays"] == days
                      and len(x["service"].keys()) == 1
                      and x["service"].get("medicine"),
            self.all_rules))
        return self.add_single_policy_data_to_the_list(rules_list)

    def add_policy_for_abroad(self):
        if self.condition_service_abroad_in_company:
            return True
        rules_list = list(filter(lambda x: bool(x["service"].get("abroad")), self.all_rules))
        return self.add_single_policy_data_to_the_list(rules_list)

    def add_policy_for_foreign(self, age):
        if self.condition_service_foreign_in_company:
            return True
        rules_list = list(filter(
            lambda x: bool(x["service"].get("foreign")) and x["age"] == age,
            self.all_rules))
        return self.add_single_policy_data_to_the_list(rules_list)

    def add_policy_for_multipolicy(self, days, age):
        if self.condition_service_multipolicy_in_company:
            return False
        rules_list = list(filter(
            lambda x: bool(x["service"].get("multipolicy"))
                      and x["insuredDays"] == days
                      and x["age"] == age,
            self.all_rules))
        return self.add_single_policy_data_to_the_list(rules_list)

    def add_policy_for_dollar(self):
        if self.condition_currency_dollar_in_company:
            return True
        rules_list = list(filter(lambda x: x["currency"].upper() == "USD", self.all_rules))
        return self.add_single_policy_data_to_the_list(rules_list)

    def add_policy_for_euro(self):
        if self.condition_currency_euro_in_company:
            return
        rules_list = list(filter(lambda x: x["currency"].upper() == "EUR", self.all_rules))
        self.add_single_policy_data_to_the_list(rules_list)

    def add_policy_for_another_country(self):
        while self.is_country_list_too_small:
            countries_to_add = list(filter(lambda x: x not in self.countries_used_in_company_policies, self.countries_available_for_policies))
            if not countries_to_add:
                return
            country = random.choice(countries_to_add)
            rules_list = list(filter(lambda x: x["country"] == country, self.all_rules))
            self.add_single_policy_data_to_the_list(rules_list)

    def add_single_policy_data_to_the_list(self, rules_list):
        if len(rules_list) == 0:
            return None
        policy_data = random.choice(rules_list)
        policy_data["company"] = self.current_company
        self.company_policies_list.append(policy_data)
        return True

    def add_policy_for_travellers_list(self):
        MAX_ATTEMPT_COUNT = 10
        travellers_amount = random.choice([2, 3, 4])
        all_rules = list(filter(
            lambda x: len(x["service"].keys()) == 1
                      and x["service"].get("medicine")
                      and x["country"] not in self.disabled_countries,
            self.all_rules))
        for _ in range(0, MAX_ATTEMPT_COUNT):
            days = self.make_list_of_days_to_insure(self.current_config["insuredDays"], 1)
            country = all_rules and random.choice(list(set([x.get("country") for x in all_rules])))
            currency = random.choice(["USD", "EUR"])
            medicine = all_rules and random.choice(list(set([x["service"].get("medicine") for x in all_rules])))
            rules_list = list(filter(
                lambda x: x["insuredDays"] == days[0]
                          and x["country"] == country
                          and x["dateStart"] == 10
                          and x["currency"] == currency
                          and x["service"]["medicine"] == medicine
                          and x["expected_calculation"] != {},
                all_rules))
            if len(rules_list) >= travellers_amount:
                break
        else:  # this 'else' works if no breaks occurs in loop
            return False
        ages_list = []
        calculation_list = []
        policy_data = {}
        for _ in range(0, travellers_amount):
            policy_data = random.choice(rules_list)
            ages_list.append(policy_data["age"])
            calculation_list.append(policy_data["expected_calculation"])
            rules_list.remove(policy_data)
        policy_data["age"] = ages_list
        policy_data["expected_calculation"] = self.calculate_products_expected_prices(calculation_list)
        policy_data["company"] = self.current_company
        self.company_policies_list.append(policy_data)
        return policy_data

    def calculate_products_expected_prices(self, calculation_list):
        result_dict = {}
        for list_item in calculation_list:
            for dict_key in list_item.keys():
                if dict_key in result_dict.keys():
                    result_dict[dict_key] += list_item[dict_key]
                else:
                    result_dict[dict_key] = list_item[dict_key]
                result_dict[dict_key] = round(result_dict[dict_key], 4)  # prevent values like 125.23500000000001
        return result_dict

    def add_policy_for_country_pair(self):
        list_with_countries = [x for x in self.special_rules if isinstance(x.get("country"), list)]
        if list_with_countries:
            policy_data = random.choice(list_with_countries)
            policy_data["company"] = self.current_company
            self.company_policies_list.append(policy_data)

    def add_policy_for_territory(self):
        list_with_territories = [x for x in self.special_rules if not x.get("country")]
        if list_with_territories:
            policy_data = random.choice(list_with_territories)
            policy_data["company"] = self.current_company
            self.company_policies_list.append(policy_data)

    def assign_ids_to_policies(self):
        for count, policy in enumerate(self.policies_list):
            policy["id"] = count

    def save_policies_list_to_file(self):
        data_file = config_module.get_dir_by_suffix("che-test/scripts/autotests/data/vzr_data.json")
        logger.info("Saving generated data to the file '%s'" % data_file)
        with open(data_file, "w") as file:
            file.write(json.dumps(self.policies_list, indent=4, sort_keys=True))
        logger.success("Saved generated data successfully (%s scenarios generated)" % len(self.policies_list))

    def make_report_for_policies_data_conditions(self):
        report = {"!companies_amount": len(self.enabled_companies),
                  "!companies_list": self.enabled_companies,
                  "!scenarios_amount": len(self.policies_list),
                  "!all_scenarios_for_dollar": len(list(
                      filter(lambda x: x["currency"].upper() == "USD",
                             self.policies_list))),
                  "!all_scenarios_for_euro": len(list(
                      filter(lambda x: x["currency"].upper() == "EUR",
                             self.policies_list))),
                  "!all_scenarios_for_abroad": len(list(
                      filter(lambda x: bool(x["service"].get("abroad")),
                             self.policies_list))),
                  "!all_scenarios_for_foreign": len(list(
                      filter(lambda x: bool(x["service"].get("foreign")),
                             self.policies_list))),
                  "!all_scenarios_for_multipolicy": len(list(
                      filter(lambda x: bool(x["service"].get("multipolicy")),
                             self.policies_list))),
                  "!all_scenarios_for_cashless_payment": len(list(
                      filter(lambda x: x.get("cashless_payment"),
                             self.policies_list))),
                  "!all_scenarios_for_travellers_group": len(list(
                      filter(lambda x: isinstance(x["age"], list),
                             self.policies_list))),
                  "!all_scenarios_for_sport": len(list(
                      filter(lambda x: x.get("sport"), self.policies_list))),
                  "!all_scenarios_for_pair_of_countries": len(list(
                      filter(lambda x: isinstance(x.get("country"), list),
                             self.policies_list))),
                  "!all_scenarios_for_countryGroup": len(list(
                      filter(lambda x: x.get("countryGroup"),
                             self.policies_list))), "!all_sport_list": list(
                set([x.get("sport") for x in self.policies_list if
                     x.get("sport")]))}
        country_no_group_list = list(filter(lambda x: isinstance(x.get("country"), str), self.policies_list))
        report["!all_countries_amount"] = len(set([x.get("country") for x in country_no_group_list]))
        report["!all_countries_list"] = list(set([x.get("country") for x in country_no_group_list]))
        for company in self.enabled_companies.keys():
            self.current_company = company
            subreport = {}
            self.company_policies_list = list(filter(lambda x: x.get("company") == company, self.policies_list))
            subreport["scenarios_amount"] = len(self.company_policies_list)
            subreport["scenarios_ids"] = [x.get("id") for x in self.company_policies_list]
            subreport["countries_amount"] = len(self.countries_used_in_company_policies)
            subreport["countries_list"] = list(self.countries_used_in_company_policies)
            subreport["scenario_for_dollar"] = self.condition_currency_dollar_in_company
            subreport["scenario_for_euro"] = self.condition_currency_euro_in_company
            subreport["scenario_for_abroad"] = self.condition_service_abroad_in_company
            subreport["scenario_for_foreign"] = self.condition_service_foreign_in_company
            subreport["scenario_for_multipolicy"] = self.condition_service_multipolicy_in_company
            subreport["scenario_for_cashless_payment"] = bool(list(filter(lambda x: x.get("cashless_payment"), self.company_policies_list)))
            subreport["scenario_for_travellers_group"] = bool(list(filter(lambda x: isinstance(x["age"], list), self.company_policies_list)))
            subreport["scenario_for_sport"] = bool(list(filter(lambda x: x.get("age"), self.company_policies_list)))
            subreport["scenario_for_countryGroup"] = bool(list(filter(lambda x: x.get("countryGroup"), self.company_policies_list)))
            subreport["scenario_for_pair_of_countries"] = bool(list(filter(lambda x: isinstance(x.get("country"), list), self.company_policies_list)))
            report[company] = subreport
        report_file = config_module.get_dir_by_suffix("che-test/scripts/autotests/data/vzr_scenarios.json")
        logger.info("Saving generated data to the file '%s'" % report_file)
        with open(report_file, "w") as file:
            file.write(json.dumps(report, indent=4, sort_keys=True))
        logger.success("Saved report for generated data successfully")

    def set_cashless_payment_scenarios(self):
        amount = int(config_module.get_value_from_config("['generator']['cashless_payment_amount']", "config/acceptance_vzr.json"))
        amount = min(amount, len(self.policies_list))
        # set default value for cashless payment
        for policy in self.policies_list:
            policy["cashless_payment"] = False
        # filter scenarios to keep regular only, shuffle and select required amount
        #   and store filtered list separately for not to break original policies list
        cashless_available_list = list(filter(lambda x: not isinstance(x["age"], list), self.policies_list))
        random.shuffle(cashless_available_list)
        cashless_available_list = cashless_available_list[0:amount]
        # set cashless payment for selected scenaios
        for scenario in cashless_available_list:
            index = self.policies_list.index(scenario)
            self.policies_list[index]["cashless_payment"] = True


if __name__ == '__main__':
    gen = PolicyRulesGenerator()
    my_list = gen.generate_policy_data_list()
