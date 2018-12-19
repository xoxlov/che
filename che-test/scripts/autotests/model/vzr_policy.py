# -*- coding: utf-8; -*-
import datetime
from dateutil.relativedelta import relativedelta
from requests.exceptions import ConnectionError
import tempmail

import common.logger as logger
import common.config_module as config_module


class Traveller(object):
    def __init__(self, policy, fname=None, lname=None, age=None, bday=None):
        self.traveller_first_name = fname
        self.traveller_last_name = lname
        self.traveller_age = age
        self.traveller_birthday = bday or (policy.date_start - relativedelta(years=self.traveller_age)).strftime("%d.%m.%Y")
        # special case to avoid error when filling traveller data
        self.traveller_birthday = (datetime.datetime.today() - relativedelta(days=1)).strftime("%d.%m.%Y") if age == 0 else self.traveller_birthday

    def __getitem__(self, item):
        """return object['new_key'] or None if key is not defined"""
        return self.__dict__[item] if item in self.__dict__ else None

    def __str__(self):
        return "{\n" + ",\n".join("    {0}: '{1}'".format(d, self.__getitem__(d)) for d in self.__dict__) + "\n}\n"

    def __repr__(self):
        return "{" + ", ".join("{0}: '{1}'".format(d, self.__getitem__(d)) for d in self.__dict__) + "}"


class Buyer(object):
    def __init__(self, buyer_data):
        self.first_name = buyer_data.get("first_name")
        self.middle_name = buyer_data.get("middle_name")
        self.last_name = buyer_data.get("last_name")
        self.first_name_rus = buyer_data.get("first_name_rus")
        self.middle_name_rus = buyer_data.get("middle_name_rus")
        self.last_name_rus = buyer_data.get("last_name_rus")
        self.phone = buyer_data.get("phone")
        self.email = buyer_data.get("email")
        self.birthday = buyer_data.get("birthday")
        self.full_name = \
            " ".join(filter(lambda x: x is not None, [self.first_name, self.middle_name, self.last_name]))
        self.full_name_rus = \
            " ".join(filter(lambda x: x is not None, [self.first_name_rus, self.middle_name_rus, self.last_name_rus]))

    def __str__(self):
        return "Policy buyer: {n} ({ph}; {e})".format(n=self.full_name, ph=self.phone, e=self.email)


class BankingCard(object):
    def __init__(self, number, holder, month, year, cvv=None):
        self.holder = holder
        self.number = number
        self.cvv = cvv
        self.month = month
        self.year = year

    def __str__(self):
        return "Card #{n}: {h}, valid through {m}/{y}".format(n=int(self.number), h=self.holder, m=self.month, y=self.year)


class Policy(object):
    def set_policy_default_values(self):
        self.__dict__.clear()  # reset all values
        config_name = config_module.get_dir_by_suffix("che-test/scripts/autotests/config/acceptance_vzr.json")
        config = config_module.load(config_name)

        self.set_insurance_data_from_dict(config[u'insurance'])
        self.set_traveller_data_from_dict(config[u'traveller'])
        self.set_buyer_data_from_dict(config[u'buyer'])
        self.set_card_data_from_dict(config[u'card'])
        self.policy_price = None
        self.check_parent_task_only = False

    def set_insurance_data_from_dict(self, cfg_insurance):
        # list is used because there can be a list of countries to travel
        self.country_to_travel = [cfg_insurance.get("country")]
        self.country_group_to_travel = []
        self.currency = cfg_insurance.get("currency")
        self.service_medicine = cfg_insurance.get("service").get("medicine")
        self.insured_days = cfg_insurance.get("insuredDays")
        self.days_from_now_to_start = cfg_insurance.get("days_from_now_to_start")
        self.date_start = datetime.date.today() + datetime.timedelta(days=self.days_from_now_to_start)
        self.date_end = self.date_start + datetime.timedelta(days=self.insured_days - 1)

    def set_traveller_data_from_dict(self, cfg_traveller):
        first_name = cfg_traveller.get("first_name")
        last_name = cfg_traveller.get("last_name")
        age = cfg_traveller.get("age") or None
        # list of travellers is used because there can be a list of people
        self.traveller_list = [Traveller(self, fname=first_name, lname=last_name, age=age)]
        self.traveller_ages_list = [x.traveller_age for x in self.traveller_list]

    def set_buyer_data_from_dict(self, cfg_buyer):
        buyer = {"first_name": cfg_buyer.get("first_name"),
                 "middle_name": cfg_buyer.get("middle_name"),
                 "last_name": cfg_buyer.get("last_name"),
                 "first_name_rus": cfg_buyer.get("first_name_rus"),
                 "middle_name_rus": cfg_buyer.get("middle_name_rus"),
                 "last_name_rus": cfg_buyer.get("last_name_rus"),
                 "buyer_birthday_delta_years": cfg_buyer.get(
                     "buyer_birthday_delta_years") or 0}
        year = datetime.datetime.today().year - buyer["buyer_birthday_delta_years"]
        buyer["birthday"] = datetime.datetime.today().replace(year=year).strftime("%d.%m.%Y")
        buyer["phone"] = cfg_buyer.get("phone")
        buyer["email"] = cfg_buyer.get("email")
        self.buyer = Buyer(buyer_data=buyer)
        self.buyer.email = self.generate_tempmail_address(self.buyer.email)
        self.use_tempmail = self.get_tempmail_service_status(self.buyer.email)
        logger.info("Using {} email for buyer".format(self.buyer.email))
        logger.print_empty_line()

    def generate_tempmail_address(self, email):
        if bool(email):
            return email
        MAX_COUNT = 10
        for i in range(MAX_COUNT):
            email = self.get_temp_address_from_tempmail_service()
            if not email:  # connection or mail service error
                break
            if self.get_tempmail_service_status(email):
                return email
        return "tempmailnotavailable@email.address"

    def get_tempmail_service_status(self, email):
        return str(email).endswith("@p33.org")

    def get_temp_address_from_tempmail_service(self):
        try:
            tm = tempmail.TempMail()
            generated_email = tm.get_email_address()
            del tm
            return generated_email
        except (ConnectionError, Exception):
            return False

    def set_card_data_from_dict(self, cfg_card):
        number = cfg_card.get("number")
        holder = cfg_card.get("holder")
        month = cfg_card.get("month")
        year = cfg_card.get("year")
        cvv = cfg_card.get("cvv")
        self.banking_card = BankingCard(number=number, holder=holder, month=month, year=year, cvv=cvv)

    def load_values_from_structure(self, policy):
        def process_services(service):
            service_map = {
                "abroad": self.set_service_abroad,
                "accident": self.set_service_accident,
                "alcoholAssistance": self.set_service_alcohol_assistance,
                "aviaAccident": self.set_service_avia_accident,
                "aviaCancel": self.set_service_avia_cancel,
                "aviaCargo": self.set_service_avia_cargo,
                "aviaMiss": self.set_service_avia_miss,
                "auto": self.set_service_auto,
                "charterDelay": self.set_service_charter_delay,
                "chronicArresting": self.set_service_chronic_arresting,
                "civilLiability": self.set_service_civil_liability,
                "document": self.set_service_document,
                "delayCargo": self.set_service_delay_cargo,
                "disasterAssistance": self.set_service_disaster_assistance,
                "dockDelay": self.set_service_dock_delay,
                "durationCoeffs100t3": self.set_service_duration_coeffs_100t3,
                "durationCoeffs100t4": self.set_service_duration_coeffs_100t4,
                "durationCoeffst135": self.set_service_duration_coeffs_t135,
                "equipment": self.set_service_equipment,
                "foreign": self.set_service_foreign,
                "hotelCargo": self.set_service_hotel_cargo,
                "insuredEscortLiving": self.set_service_insured_escort_living,
                "insuredEscortReturn": self.set_service_insured_escort_return,
                "insuredLiving": self.set_service_insured_living,
                "insurerTemporaryReturn": self.set_service_insurer_temporary_return,
                "legal": self.set_service_legal,
                "medicine": self.set_service_medicine,
                "medicineCoeffsMultyt1": self.set_service_medicine_coeffs_multy_t1,
                "multipolicy": self.set_service_multipolicy,
                "pregnancy": self.set_service_pregnancy,
                "property": self.set_service_property,
                "regularDelay": self.set_service_regular_delay,
                "relativeIllReturn": self.set_service_relative_ill_return,
                "sunburnAssistance": self.set_service_sunburn_assistance,
                "terrorAssistance": self.set_service_terror_assistance,
                "thirdPartyTransportation": self.set_service_third_party_transportation,
                "tripCancel": self.set_service_trip_cancel,
                "visaCancel": self.set_service_visa_cancel,
                "work": self.set_service_work
            }
            for service_key in service.keys():
                if service_key in service_map.keys():
                    service_map[service_key](service[service_key])
                else:
                    logger.error("Cannot process value from internal data: policy['service']['%s'] = '%s']" % (service_key, policy["service"][service_key]))
            return

        policy_map = {
            "age": self.set_policy_age,
            "company": self.set_policy_company,
            "country": self.set_policy_country_to_travel,
            "countryGroup": self.set_policy_country_group_to_travel,
            "currency": self.set_policy_currency,
            "dateStart": self.set_policy_days_from_now,
            "expected_calculation": self.set_expected_calculation,
            "insuredDays": self.set_policy_insured_days,
            "service": process_services,
            "sport": self.set_policy_sport,
            "id": self.set_scenario_id,
            "cashless_payment": self.set_cashless_payment
        }
        for key in policy.keys():
            if key in policy_map.keys():
                policy_map[key](policy[key])
            else:
                logger.error("Cannot process value from internal data: policy['%s'] = '%s'" % (key, policy[key]))

    def __str__(self):
        return "{\n" + "\n".join("\t{0}: {1}".format(d, self.__getitem__(d)) for d in self.__dict__) + "\n}\n"

    def __getitem__(self, item):
        """return object['new_key'] or None if key is not defined"""
        return self.__dict__[item] if item in self.__dict__ else None

    def __getattr__(self, item):
        """return object.new_key or None if key is not defined"""
        return self.__dict__[item] if item in self.__dict__ else None

    def __setitem__(self, key, value):
        """object['new_key'] = new_value"""
        self.__dict__[key] = value

    def __setattr__(self, key, value):
        """object.new_key = new_value"""
        self.__dict__[key] = value

    # -------------------- main policy options --------------------
    def set_policy_age(self, age):
        del (self.traveller_ages_list[:])  # clear list
        if isinstance(age, int):
            self.traveller_ages_list = [age]
        elif isinstance(age, list):
            self.traveller_ages_list = age[:]  # make deep copy
        # save data from default values to temporary variable before processing
        temp_traveller = self.traveller_list[0]
        del (self.traveller_list[:])  # clear list
        self.traveller_list = [Traveller(self, fname=temp_traveller.traveller_first_name, lname=temp_traveller.traveller_last_name, age=a)
                               for a in self.traveller_ages_list]

    def set_policy_company(self, company):
        self.company = company

    def set_policy_country_to_travel(self, country):
        del (self.country_group_to_travel[:])  # clear list if country groups
        del (self.country_to_travel[:])  # clear list
        if isinstance(country, str):
            self.country_to_travel = [country]
        elif isinstance(country, list):
            self.country_to_travel = country[:]  # make deep copy

    def set_policy_country_group_to_travel(self, countryGroup):
        del (self.country_to_travel[:])  # clear list of countries
        del (self.country_group_to_travel[:])  # clear list
        if isinstance(countryGroup, str):
            self.country_group_to_travel = [countryGroup]
        elif isinstance(countryGroup, list):
            self.country_group_to_travel = countryGroup[:]  # make deep copy

    def set_policy_currency(self, currency):
        self.currency = currency

    def set_policy_days_from_now(self, days):
        self.days_from_now_to_start = days
        self.date_start = datetime.date.today() + datetime.timedelta(days=self.days_from_now_to_start)
        self.date_end = self.date_start + datetime.timedelta(days=self.insured_days - 1)

    def set_policy_insured_days(self, days):
        self.insured_days = days
        self.date_end = self.date_start + datetime.timedelta(days=self.insured_days - 1)

    def set_policy_sport(self, sport):
        self.sport = sport

    def set_scenario_id(self, scen_id):
        self.id = scen_id

    def set_cashless_payment(self, cashless_payment):
        self.cashless_payment = cashless_payment

    # -------------------- services --------------------
    def set_service_abroad(self, abroad):
        self.service_abroad = abroad

    def set_service_accident(self, accident):
        self.service_accident = accident

    def set_service_alcohol_assistance(self, alcohol_assistance):
        self.service_alcohol_assistance = alcohol_assistance

    def set_service_avia_accident(self, avia_accident):
        self.service_avia_accident = avia_accident

    def set_service_avia_cancel(self, avia_cancel):
        self.service_avia_cancel = avia_cancel

    def set_service_avia_cargo(self, avia_cargo):
        self.service_avia_cargo = avia_cargo

    def set_service_avia_miss(self, avia_miss):
        self.service_avia_miss = avia_miss

    def set_service_auto(self, auto):
        self.service_auto = auto

    def set_service_charter_delay(self, charter_delay):
        self.service_charter_delay = charter_delay

    def set_service_chronic_arresting(self, chronic_arresting):
        self.service_chronic_arresting = chronic_arresting

    def set_service_civil_liability(self, liability):
        self.service_civil_liability = liability

    def set_service_document(self, document):
        self.service_document = document

    def set_service_delay_cargo(self, delay_cargo):
        self.service_delay_cargo = delay_cargo

    def set_service_disaster_assistance(self, disaster_assistance):
        self.service_disaster_assistance = disaster_assistance

    def set_service_dock_delay(self, dock_delay):
        self.service_dock_delay = dock_delay

    def set_service_duration_coeffs_100t3(self, duration_coeffs_100t3):
        self.service_duration_coeffs_100t3 = duration_coeffs_100t3

    def set_service_duration_coeffs_100t4(self, duration_coeffs_100t4):
        self.service_duration_coeffs_100t4 = duration_coeffs_100t4

    def set_service_duration_coeffs_t135(self, duration_coeffs_t135):
        self.service_duration_coeffs_t135 = duration_coeffs_t135

    def set_service_equipment(self, equipment):
        self.service_equipment = equipment

    def set_expected_calculation(self, exp_calc_dict):
        self.expected_calculation = exp_calc_dict or 0.0

    def set_service_foreign(self, foreign):
        self.service_foreign = foreign

    def set_service_hotel_cargo(self, hotel_cargo):
        self.service_hotel_cargo = hotel_cargo

    def set_service_insured_escort_living(self, insured_escort_living):
        self.service_insured_escort_living = insured_escort_living

    def set_service_insured_escort_return(self, insured_escort_return):
        self.service_insured_escort_return = insured_escort_return

    def set_service_insured_living(self, insured_living):
        self.service_insured_living = insured_living

    def set_service_insurer_temporary_return(self, insurer_temporary_return):
        self.service_insurer_temporary_return = insurer_temporary_return

    def set_service_legal(self, legal):
        self.service_legal = legal

    def set_service_medicine(self, medicine):
        self.service_medicine = medicine

    def set_service_medicine_coeffs_multy_t1(self, medicine_coeffs_multy_t1):
        self.service_medicine_coeffs_multy_t1 = medicine_coeffs_multy_t1

    def set_service_multipolicy(self, multipolicy):
        self.service_multipolicy = multipolicy

    def set_service_pregnancy(self, pregnancy):
        self.service_pregnancy = pregnancy

    def set_service_property(self, service_property):
        self.service_property = service_property

    def set_service_regular_delay(self, regular_delay):
        self.service_regular_delay = regular_delay

    def set_service_relative_ill_return(self, relative_ill_return):
        self.service_relative_ill_return = relative_ill_return

    def set_service_sunburn_assistance(self, sunburn_assistance):
        self.service_sunburn_assistance = sunburn_assistance

    def set_service_terror_assistance(self, terror_assistance):
        self.service_terror_assistance = terror_assistance

    def set_service_third_party_transportation(self, third_party_transportation):
        self.service_third_party_transportation = third_party_transportation

    def set_service_trip_cancel(self, trip_cancel):
        self.service_trip_cancel = trip_cancel

    def set_service_visa_cancel(self, visa_cancel):
        self.service_visa_cancel = visa_cancel

    def set_service_work(self, work):
        self.service_work = work
