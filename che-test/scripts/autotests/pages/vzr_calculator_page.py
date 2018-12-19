# -*- coding: utf-8; -*-
import time
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import WebDriverException

from common.webpages.button import Button
from common.webpages.checkbox import CheckBox
from common.webpages.radiobutton import RadioButton
from common.webpages.pageobject import PageObject, page_element_operation, PageError
from common.system import function_name
import common.config_module as config_module
import common.logger as logger
from common.database import CheDb


class CalculatorPage(PageObject):

    def __init__(self, app):
        self.completeness = False
        super(CalculatorPage, self).__init__(app)
        self.db = CheDb(db_config=config_module.load()["database"], verbose=False)
        self.insurance_companies = self.db.get_insurance_companies_list()
        self.calculator_page_timeout = int(config_module.get_value_from_config("['vzr_pages']['calculator_page_timeout']", self.config_file_name))
        self.company = None
        self.exchange_rate = 1.0
        self.price = 0.0
        self.price_calculation_timeout = 10
        self.page_name = "Calculator page"
        self.screenshot_name_suffix = "calculator_page"
        self.expected_titles = [u"Расчет стоимости страховки".encode("utf-8"),
                                u"Туристическая страховка в ".encode("utf-8"),
                                u"Туристическая страховка на ".encode("utf-8")]

        # Page Objects interface elements
        self.period_of_stay = \
            Button(webdriver=self.driver,
                   name="ButtonPeriodOfStay",
                   locator=".period-of-stay",
                   description="Срок пребывания")
        self.abroad_checkbox = \
            CheckBox(webdriver=self.driver,
                     name="Abroad",
                     locator="input#cb-abroad",
                     description="Я уже путешествую")
        self.accident_avia_checkbox = \
            CheckBox(webdriver=self.driver,
                     name="aviaAccident",
                     locator="input#cb-aviaAccident",
                     description="Страхование от несчастных случаев На время авиаперелёта")
        self.accident_service_checkbox = \
            CheckBox(webdriver=self.driver,
                     name="Accident service",
                     locator="input#cb-accident.serviceCheckbox",
                     description="Страхование от несчастных случаев На время путешествия")
        self.accidents_checkbox = \
            CheckBox(webdriver=self.driver,
                     name="Accidents section",
                     locator="input#cb-accidents",
                     description="Страхование от несчастных случаев")
        self.alcoholAssistance_checkbox = \
            CheckBox(webdriver=self.driver,
                     name="alcoholAssistance",
                     locator="input#cb-alcoholAssistance",
                     description="Помощь при наличии алкогольного опьянения")
        self.auto_checkbox = \
            CheckBox(webdriver=self.driver,
                     name="Auto",
                     locator="input#cb-auto",
                     description="Поездка на личном автомобиле")
        self.avia_service_checkbox = \
            CheckBox(webdriver=self.driver,
                     name="Avia service",
                     locator="input#cb-avia.serviceCheckbox",
                     description="Страхование авиаперелёта")
        self.avia_regularDelay_checkbox = \
            CheckBox(webdriver=self.driver,
                     name="Avia regularDelay",
                     locator="input#cb-regularDelay",
                     description="Страхование задержки регулярного рейса")
        self.avia_charterDelay_checkbox = \
            CheckBox(webdriver=self.driver,
                     name="Avia charterDelay",
                     locator="input#cb-charterDelay",
                     description="Страхование задержки чартерного рейса")
        self.cargo_checkbox = \
            CheckBox(webdriver=self.driver,
                     name="Cargo",
                     locator="input#cb-cargo",
                     description="Страхование багажа")
        self.cargo_avia_checkbox = \
            CheckBox(webdriver=self.driver,
                     name="Cargo",
                     locator="input#cb-aviaCargo.serviceCheckbox",
                     description="Страхование багажа на время перелета")
        self.cargo_delay_checkbox = \
            CheckBox(webdriver=self.driver,
                     name="Cargo Delay",
                     locator="input#cb-delayCargo",
                     description="Страхование задержки багажа")
        self.chronicArresting_checkbox = \
            CheckBox(webdriver=self.driver,
                     name="chronicArresting",
                     locator="input#cb-chronicArresting",
                     description="Купирование обострения хронических заболеваний")
        self.civilLiability_checkbox = \
            CheckBox(webdriver=self.driver,
                     name="civilLiability",
                     locator="input#cb-civilLiability.serviceCheckbox",
                     description="Страхование гражданской ответственности")
        self.disasterAssistance_checkbox = \
            CheckBox(webdriver=self.driver,
                     name="disasterAssistance",
                     locator="input#cb-disasterAssistance",
                     description="Помощь в результате стихийных бедствий (наводнения, цунами, торнадо и др.)")
        self.document_checkbox = \
            CheckBox(webdriver=self.driver,
                     name="Document",
                     locator="input#cb-document",
                     description="Страхование потери документов")
        self.foreign_checkbox = \
            CheckBox(webdriver=self.driver,
                     name="Foreign",
                     locator="input#cb-foreign",
                     description="Я не гражданин России")
        self.insuredEscortLiving_checkbox = \
            CheckBox(webdriver=self.driver,
                     name="insuredEscortLiving",
                     locator="input#cb-insuredEscortLiving",
                     description="Оплата проживания третьего лица в случае чрезвычайной ситуации с Застрахованным  ")
        self.insuredEscortReturn_checkbox = \
            CheckBox(webdriver=self.driver,
                     name="insuredEscortReturn",
                     locator="input#cb-insuredEscortReturn",
                     description="Оплата проезда до места жительства после лечения в больнице сопровождающего лица Застрахованного")
        self.insuredLiving_checkbox = \
            CheckBox(webdriver=self.driver,
                     name="insuredLiving",
                     locator="input#cb-insuredLiving",
                     description="Оплата проживания Застрахованного до отъезда после лечения в больнице")
        self.insurerTemporaryReturn_checkbox = \
            CheckBox(webdriver=self.driver,
                     name="insurerTemporaryReturn",
                     locator="input#cb-insurerTemporaryReturn",
                     description="Временное возвращение Застрахованного домой")
        self.legal_checkbox = \
            CheckBox(webdriver=self.driver,
                     name="Legal",
                     locator="input#cb-legal",
                     description="Юридическая помощь")
        self.medicine_checkbox = \
            CheckBox(webdriver=self.driver,
                     name="Medicine",
                     locator="input#cb-medicine.serviceCheckbox",
                     description="Медицинское страхование")
        self.motorcycle_checkbox = \
            CheckBox(webdriver=self.driver,
                     name="Motorcycle",
                     locator="input#cb-motorcycle",
                     description="Передвижение на мотоцикле/мопеде")
        self.multipolicy_checkbox = \
            CheckBox(webdriver=self.driver,
                     name="Multipolicy",
                     locator="input#holder-multipolicy.serviceCheckbox",
                     description="Годовой полис")
        self.multipolicy_limited_checkbox = \
            CheckBox(webdriver=self.driver,
                     name="LimitedMultipolicy",
                     locator="input.multipolicy-checkbox#cb-multipolicy[type='radio']",
                     description="Количество застрахованных дней в году")
        self.pregnancy_checkbox = \
            CheckBox(webdriver=self.driver,
                     name="Pregnancy",
                     locator="input#cb-pregnancy.serviceCheckbox",
                     description="Страхование на случай осложнения беременности ")
        self.relativeIllReturn_checkbox = \
            CheckBox(webdriver=self.driver,
                     name="relativeIllReturn",
                     locator="input#cb-relativeIllReturn",
                     description="Оплата проезда домой в случае внезапной болезни/смерти родственника")
        self.rescueActivities_checkbox = \
            CheckBox(webdriver=self.driver,
                     name="rescueActivities",
                     locator="input#cb-rescueActivities",
                     description="Поисково-спасательные мероприятия")
        self.searchActivities_checkbox = \
            CheckBox(webdriver=self.driver,
                     name="searchActivities",
                     locator="input#cb-searchActivities",
                     description="Эвакуация вертолетом")
        self.sunburnAssistance_checkbox = \
            CheckBox(webdriver=self.driver,
                     name="sunburnAssistance",
                     locator="input#cb-sunburnAssistance",
                     description="Помощь при солнечных ожогах")
        self.terrorAssistance_checkbox = \
            CheckBox(webdriver=self.driver,
                     name="terrorAssistance",
                     locator="input#cb-terrorAssistance",
                     description="Помощь в результате терактов")
        self.thirdPartyTransportation_checkbox = \
            CheckBox(webdriver=self.driver,
                     name="thirdPartyTransportation",
                     locator="input#cb-thirdPartyTransportation",
                     description="Оплата проезда третьего лица в случае чрезвычайной ситуации с Застрахованным")
        self.tripCancel_checkbox = \
            CheckBox(webdriver=self.driver,
                     name="tripCancel",
                     locator="input#cb-tripCancel.serviceCheckbox",
                     description="Страхование отмены поездки")
        self.visaCancel_checkbox = \
            CheckBox(webdriver=self.driver,
                     name="visaCancel",
                     locator="input#cb-visaCancel",
                     description="Страхование риска отказа в визе")
        self.work_checkbox = \
            CheckBox(webdriver=self.driver,
                     name="Work",
                     locator="input#cb-work",
                     description="Работа с повышенным риском")

        self.accident_radio = \
            RadioButton(webdriver=self.driver,
                        name="Accident",
                        locator="input#cb-accident[type='radio']",
                        description="Страхование от несчастных случаев на всё время путешествия")
        self.cargo_avia_radio = \
            RadioButton(webdriver=self.driver,
                        name="Cargo",
                        locator="input#cb-aviaCargo[type='radio']",
                        description="Страхование багажа на время перелёта")
        self.civilLiability_radio = \
            RadioButton(webdriver=self.driver,
                        name="civilLiability",
                        locator="input#cb-civilLiability[type='radio']",
                        description="Страхование гражданской ответственности")
        self.medicine_service_radio = \
            RadioButton(webdriver=self.driver,
                        name="Medicine",
                        locator="input#cb-medicine[type='radio']",
                        description="Медицинское страхование")
        self.pregnancy_radio = \
            RadioButton(webdriver=self.driver,
                        name="Pregnancy",
                        locator="input#cb-pregnancy[type='radio']",
                        description="Страхование на случай осложнения беременности")
        self.tripCancel_radio = \
            RadioButton(webdriver=self.driver,
                        name="tripCancel",
                        locator="input#cb-tripCancel[type='radio']",
                        description="Страхование отмены поездки")
        self.multipolicy_value_radio = \
            RadioButton(webdriver=self.driver,
                        name="Multipolicy",
                        locator="input#cb-multipolicy[type='radio']",
                        description="Годовой полис по количеству застрахованных дней в году")

        self.medicine_more_button = \
            Button(webdriver=self.driver,
                   name="MedicineMore",
                   locator="a.med-more",
                   description="Подробности 'Входит в Вашу страховку'")
        self.sport_open_button = \
            Button(webdriver=self.driver,
                   name="ButtonOpenSport",
                   locator="[for='cb-sportGroup']",
                   description="Занятие спортом и активный отдых")
        self.tripCancel_list_more_prices = \
            Button(webdriver=self.driver,
                   name="MorePricesTripCancel",
                   locator=".price-list-more",
                   description="Дополнительные цены для отмены поездки")

    def __getattribute__(self, name):
        """Overloaded operator is used to catch insurance options change, if any of them caught then
        notifications are checked and processing delayed for notifications to disappear.

        """
        attr = object.__getattribute__(self, name)
        # check if attribute is method
        # check if method has name
        # check if method name is related to insurance options set
        if hasattr(attr, '__call__') \
                and hasattr(attr, '__name__') \
                and (attr.__name__.startswith("page_wrapper") or attr.__name__.startswith("set_")):
            def wait_until_no_insurance_nofitication_is_off(*args, **kwargs):
                self.wait_notification_to_disappear()
                return attr(*args, **kwargs)
            return wait_until_no_insurance_nofitication_is_off
        else:
            return attr

    @property
    def yellow_line(self):
        found = self.driver.find_elements_by_css_selector(".modal-backdrop")
        return found[0] if found else None

    @property
    def start_date_input(self):
        found = self.driver.find_elements_by_css_selector("input#from")
        return found[0] if found else None

    @property
    def end_date_input(self):
        found = self.driver.find_elements_by_css_selector("input#to")
        return found[0] if found else None

    @property
    def active_currency_button(self):
        found = self.driver.find_elements_by_css_selector("button.changeCurrencyTrigger.active")
        return found[0] if found else None

    @property
    def currency_usd_button(self):
        found = self.driver.find_elements_by_css_selector("button.changeCurrencyTrigger[value='usd']")
        return found[0] if found else None

    @property
    def currency_eur_button(self):
        found = self.driver.find_elements_by_css_selector("button.changeCurrencyTrigger[value='eur']")
        return found[0] if found else None

    @property
    def data_serial_value(self):
        found = self.driver.find_elements_by_css_selector("div#offers")
        if not found:
            return -1
        dataset = found[0].get_property("dataset")
        return int(dataset["serial"]) if "serial" in dataset.keys() else 0

    @property
    def insurance_company_buy_button(self):
        found = self.driver.find_elements_by_css_selector(".%s-hc .offer-buy" % self.company)
        return found[0] if found else None

    @property
    def med_more_box(self):
        found = self.driver.find_elements_by_css_selector(".med-more-box")
        return found[0] if found else None

    @property
    def price_from_page(self):
        found = self.driver.find_elements_by_css_selector(".%s-hc .odometer" % self.company)
        return float(found[0].get_property("dataset")['number']) if found else 0.0

    @property
    def is_service_trip_cancel_3000_clickable(self):
        found = self.driver.find_elements_by_css_selector("input#cb-tripCancel[type='radio'][value='3000']")
        return found and found[0].is_displayed() and found[0].is_enabled()

    @property
    def sport_amateur_label(self):
        found = self.driver.find_elements_by_css_selector("[data-service='sport'] .checkbox")
        return found[0] if found else None

    @property
    def sport_competition_label(self):
        found = self.driver.find_elements_by_css_selector("[data-service='sportCompetition'] .checkbox")
        return found[0] if found else None

    @property
    def sport_amateur_input(self):
        return self.driver.find_element_by_css_selector(".custom-sport#magicsuggest-sport input")

    @property
    def sport_competition_input(self):
        return self.driver.find_element_by_css_selector(".custom-sport#magicsuggest-sports-competitions input")

    @property
    def sport_amateur_dropdown_menu(self):
        found = self.driver.find_elements_by_css_selector(".ms-res-item-grouped")
        return found[0] if found else None

    def set_url(self):
        # calculator page has "c/" in the middle - add it
        if "/c/" in self.app.testing_url:
            url = self.app.testing_url
        else:
            main_url, params = self.app.testing_url.rsplit("/", 1)
            url = '/'.join([main_url, "c", params])
        return url

    def open_calculator_page_no_structure_checks(self):
        url = self.set_url()
        self.driver.get(url)
        try:
            WebDriverWait(self.driver, self.calculator_page_timeout).until(
                EC.presence_of_element_located((By.CLASS_NAME, "new-calculation")))
            return True
        except TimeoutException:
            self.result = False
            raise PageError("ERROR: %s cannot be loaded within expected timeout" % self.page_name)

    def open_calculator_page(self):
        url = self.set_url()
        self.driver.get(url)
        self.wait_for_calculator_page()

    def wait_for_calculator_page(self):
        self.result = True
        self.completeness = False
        logger.start(self.page_name)
        self.wait_for_page_to_be_loaded(self.calculator_page_timeout, By.CLASS_NAME, "progress-bar")

    def wait_for_page_to_be_loaded(self, timeout, by, locator):
        try:
            WebDriverWait(self.driver, timeout).until_not(EC.visibility_of_element_located((By.CLASS_NAME, "progress-bar")))
        except TimeoutException:
            pass
        result = super(CalculatorPage, self).wait_for_page_to_be_loaded(timeout, by, locator)
        logger.success("{page} was loaded successfully".format(page=self.page_name))
        return result

    @page_element_operation
    def buy_insurance_from_company(self, company, expected_calculation):
        if self.completeness:
            logger.fail("All requested parameters for policy are set correctly")
            self.make_screenshot(suffix=self.screenshot_name_suffix + "_fail")
            return self.get_page_result()
        self.company = company
        if expected_calculation == 0.0:
            if self.insurance_company_buy_button is None:
                self.process_no_policy_calculation_available()
            else:
                self.process_policy_calculation_available_but_not_expected()
        else:
            if self.insurance_company_buy_button is None:
                self.process_no_policy_calculation_available_but_expected()
            else:
                self.process_policy_available_and_expected(expected_calculation)
        self.make_screenshot_if_needed(suffix=self.screenshot_name_suffix + "_ready")
        return self.get_page_result()

    def process_no_policy_calculation_available(self):
        self.completeness = True
        logger.success("Policy price was not calculated as expected")

    def process_policy_calculation_available_but_not_expected(self):
        self.completeness = True
        logger.fail("Policy price was not calculated as expected")
        self.print_price_from_page()
        self.result = False

    def process_no_policy_calculation_available_but_expected(self):
        self.completeness = True
        logger.fail("Policy price was calculated as expected")
        logger.info("Button to buy policy is not available on the page for '%s'" % self.insurance_companies[self.company])
        self.result = False

    def process_policy_available_and_expected(self, expected_calculation):
        self.result = self.compare_price_expected_and_calculated(expected_calculation) and self.result
        self.insurance_company_buy_button.click()
        logger.success("Insurance company '%s' selected" % self.insurance_companies[self.company])

    def print_price_from_page(self):
        if not self.price:
            self.price = self.price_from_page
        logger.info("Calculated value for '%s': %.2f" % (self.insurance_companies[self.company], self.price))
        return self.price

    def compare_price_expected_and_calculated(self, expected_calculation):
        displayed_price = self.price_from_page
        # put the calculated price into the policy data structure for further using
        self.app.policy_data.price = displayed_price

        expected_calculation_rub = []
        for expected_price in expected_calculation:
            expected_price_rub = round(expected_calculation[expected_price] * self.exchange_rate, 2)
            expected_calculation_rub.append(expected_price_rub)
            if abs(displayed_price - expected_price_rub) <= 1:
                # Calculation accuracy depends on the companies rules, so calculated value can be rounded accordingly.
                # Acceptable difference between calculated and expected price is taken as 1.00 Rub.
                logger.success("Policy price calculated (%.2f) matches expected (%.2f)" % (displayed_price, expected_price_rub))
                if displayed_price != expected_price_rub:
                    logger.warning("Difference between calculated and expected price is equal to %.2f"
                                   % float(abs(displayed_price - expected_price_rub)))
                return True
        logger.fail("Policy price calculated (%.2f) matches expected from list %s" % (displayed_price, expected_calculation_rub))
        return False

    def set_policy_options(self, policy):
        self.close_jivosite_frame()
        self.wait_dataset_serial_has_changed(0)
        initial_data_serial = self.data_serial_value
        self.set_currency(policy.currency)
        self.set_service_abroad(policy.service_abroad)
        self.set_service_accident_limit(policy.service_accident)
        self.set_service_alcoholAssistance(policy.service_alcohol_assistance)
        self.set_service_aviaAccident(policy.service_avia_accident)
        self.set_service_aviaCancel(policy.service_avia_cancel)
        self.set_service_aviaCargo(policy.service_avia_cargo)
        self.set_service_aviaMiss(policy.service_avia_miss)
        self.set_service_auto(policy.service_auto)
        self.set_service_charterDelay(policy.service_charter_delay)
        self.set_service_chronicArresting(policy.service_chronic_arresting)
        self.set_service_civilLiability(policy.service_civil_liability)
        self.set_service_document(policy.service_document)
        self.set_service_delayCargo(policy.service_delay_cargo)
        self.set_service_disasterAssistance(policy.service_disaster_assistance)
        self.set_service_dockDelay(policy.service_dock_delay)
        self.set_service_durationCoeffs100t3(policy.service_duration_coeffs_100t3)
        self.set_service_durationCoeffs100t4(policy.service_duration_coeffs_100t4)
        self.set_service_durationCoeffst135(policy.service_duration_coeffs_t135)
        self.set_service_equipment(policy.service_equipment)
        self.set_service_foreign(policy.service_foreign)
        self.set_service_hotelCargo(policy.service_hotel_cargo)
        self.set_service_insuredEscortLiving(policy.service_insured_escort_living)
        self.set_service_insuredEscortReturn(policy.service_insured_escort_return)
        self.set_service_insuredLiving(policy.service_insured_living)
        self.set_service_insurerTemporaryReturn(policy.service_insurer_temporary_return)
        self.set_service_legal(policy.service_legal)
        self.set_service_medicine(policy.service_medicine)
        self.set_service_medicineCoeffsMultyt1(policy.service_medicine_coeffs_multy_t1)
        self.set_service_multipolicy(policy.service_multipolicy)
        self.set_service_pregnancy(policy.service_pregnancy)
        self.set_service_property(policy.service_property)
        self.set_service_regularDelay(policy.service_regular_delay)
        self.set_service_relativeIllReturn(policy.service_relative_ill_return)
        self.set_service_sunburnAssistance(policy.service_sunburn_assistance)
        self.set_service_terrorAssistance(policy.service_terror_assistance)
        self.set_service_thirdPartyTransportation(policy.service_third_party_transportation)
        self.set_service_tripCancel(policy.service_trip_cancel)
        self.set_service_visaCancel(policy.service_visa_cancel)
        self.set_service_work(policy.service_work)
        self.set_sport(policy.sport)
        self.wait_dataset_serial_has_changed(initial_data_serial)

        self.exchange_rate = self.get_exchange_rate(policy.currency)

    def get_exchange_rate(self, currency):
        if currency.lower() == "eur":
            return self.db.get_euro_exchange_rate()
        elif currency.lower() == "usd":
            return self.db.get_dollar_exchange_rate()
        return 0.0

    def wait_dataset_serial_has_changed(self, initial_value):
        start_time = time.time()
        while True:
            if self.data_serial_value > initial_value:
                return True
            time.sleep(self.loop_time_delta)
            if time.time() - start_time > self.price_calculation_timeout:
                return False

    @page_element_operation
    def set_currency(self, currency):
        currency = currency.lower()
        if currency not in ["usd", "eur"]:
            raise ValueError("Unrecognized currency in %s('%s')" % (function_name(), currency.lower()))
        currency_button = eval("self.currency_%s_button" % currency.lower())
        if currency_button:
            if self.active_currency_button == currency_button:
                logger.success("Currency is already set to '%s'" % currency.upper())
            else:
                currency_button.click()
                logger.success("Currency is set to '%s'" % currency.upper())
        else:
            logger.fail("Currency cannot be set to '%s'" % currency.upper())
            self.completeness = True
            self.result = False

    @page_element_operation
    def set_service_abroad(self, abroad):
        self.abroad_checkbox.set(abroad)

    @page_element_operation
    def set_service_accident_limit(self, accident):
        if accident is None:
            return
        self.accidents_checkbox.set(True)
        self.accident_service_checkbox.set(accident)
        self.accident_radio.set(accident)

    @page_element_operation
    def set_service_alcoholAssistance(self, alcoholAssistance):
        if alcoholAssistance is None:
            return
        self.medicine_checkbox.set(True)
        self.open_or_close_hidden_additional_medicine_options(do_open=True)
        self.alcoholAssistance_checkbox.set(alcoholAssistance)

    @page_element_operation
    def set_service_aviaAccident(self, aviaAccident):
        if aviaAccident is None:
            return
        self.accidents_checkbox.set(True)
        self.accident_avia_checkbox.set(aviaAccident)
        self.accident_service_checkbox.restore()
        self.accident_radio.restore()

    @page_element_operation
    def set_service_aviaCancel(self, aviaCancel):
        if aviaCancel is not None:
            logger.warning("Cannot set insurance option 'aviaCancel': no associated element on the page")

    @page_element_operation
    def set_service_aviaCargo(self, aviaCargo):
        if aviaCargo is None:
            return
        self.cargo_checkbox.set(True)
        self.cargo_avia_checkbox.set(aviaCargo)
        self.cargo_avia_radio.set(aviaCargo)

    @page_element_operation
    def set_service_aviaMiss(self, aviaMiss):
        if aviaMiss is not None:
            logger.warning("Cannot set insurance option 'aviaMiss': no associated element on the page")

    @page_element_operation
    def set_service_auto(self, auto):
        self.auto_checkbox.set(auto)

    @page_element_operation
    def set_service_charterDelay(self, charterDelay):
        if charterDelay is None:
            return
        self.avia_service_checkbox.set(True)
        self.avia_charterDelay_checkbox.set(charterDelay)
        self.avia_regularDelay_checkbox.restore()

    @page_element_operation
    def set_service_chronicArresting(self, chronicArresting):
        if chronicArresting is None:
            return
        self.medicine_checkbox.set(True)
        self.open_or_close_hidden_additional_medicine_options(do_open=True)
        self.chronicArresting_checkbox.set(chronicArresting)

    @page_element_operation
    def set_service_civilLiability(self, civilLiability):
        if civilLiability is None:
            return
        self.civilLiability_checkbox.set(civilLiability)
        self.civilLiability_radio.set(civilLiability)

    @page_element_operation
    def set_service_delayCargo(self, delayCargo):
        if delayCargo is None:
            return
        self.cargo_checkbox.set(True)
        self.cargo_delay_checkbox.set(delayCargo)
        self.cargo_avia_checkbox.restore()
        self.cargo_avia_radio.restore()

    @page_element_operation
    def set_service_disasterAssistance(self, disasterAssistance):
        if disasterAssistance is None:
            return
        self.medicine_checkbox.set(True)
        self.open_or_close_hidden_additional_medicine_options(do_open=True)
        self.disasterAssistance_checkbox.set(disasterAssistance)

    @page_element_operation
    def set_service_dockDelay(self, dockDelay):
        if dockDelay is not None:
            logger.warning("Cannot set insurance option 'dockDelay': no associated element on the page")

    @page_element_operation
    def set_service_document(self, document):
        self.document_checkbox.set(document)

    @page_element_operation
    def set_service_durationCoeffs100t3(self, durationCoeffs100t3):
        if durationCoeffs100t3 is not None:
            logger.warning("Cannot set insurance option 'durationCoeffs100t3': no associated element on the page")

    @page_element_operation
    def set_service_durationCoeffs100t4(self, durationCoeffs100t4):
        if durationCoeffs100t4 is not None:
            logger.warning("Cannot set insurance option 'durationCoeffs100t4': no associated element on the page")

    @page_element_operation
    def set_service_durationCoeffst135(self, durationCoeffst135):
        if durationCoeffst135 is not None:
            logger.warning("Cannot set insurance option 'durationCoeffst135': no associated element on the page")

    @page_element_operation
    def set_service_equipment(self, equipment):
        if equipment is not None:
            logger.warning("Cannot set insurance option 'equipment': no associated element on the page")

    @page_element_operation
    def set_service_foreign(self, foreign):
        self.foreign_checkbox.set(foreign)

    @page_element_operation
    def set_service_hotelCargo(self, hotelCargo):
        if hotelCargo is not None:
            logger.warning("Cannot set insurance option 'hotelCargo': no associated element on the page")

    @page_element_operation
    def set_service_insuredEscortLiving(self, insuredEscortLiving):
        if insuredEscortLiving is None:
            return
        self.medicine_checkbox.set(True)
        self.open_or_close_hidden_additional_medicine_options(do_open=True)
        self.insuredEscortLiving_checkbox.set(insuredEscortLiving)

    @page_element_operation
    def set_service_insuredEscortReturn(self, insuredEscortReturn):
        if insuredEscortReturn is None:
            return
        self.medicine_checkbox.set(True)
        self.open_or_close_hidden_additional_medicine_options(do_open=True)
        self.insuredEscortReturn_checkbox.set(insuredEscortReturn)

    @page_element_operation
    def set_service_insuredLiving(self, insuredLiving):
        if insuredLiving is None:
            return
        self.medicine_checkbox.set(True)
        self.open_or_close_hidden_additional_medicine_options(do_open=True)
        self.insuredLiving_checkbox.set(insuredLiving)

    @page_element_operation
    def set_service_insurerTemporaryReturn(self, insurerTemporaryReturn):
        if insurerTemporaryReturn is None:
            return
        self.medicine_checkbox.set(True)
        self.open_or_close_hidden_additional_medicine_options(do_open=True)
        self.insurerTemporaryReturn_checkbox.set(insurerTemporaryReturn)

    @page_element_operation
    def set_service_legal(self, legal):
        self.legal_checkbox.set(legal)

    @page_element_operation
    def set_service_medicine(self, medicine):
        if medicine is None:
            return
        self.medicine_checkbox.set(medicine)
        self.medicine_service_radio.set(medicine)

    @page_element_operation
    def set_service_medicineCoeffsMultyt1(self, medicineCoeffsMultyt1):
        if medicineCoeffsMultyt1 is not None:
            logger.warning("Cannot set insurance option 'medicineCoeffsMultyt1': no associated element on the page")

    @page_element_operation
    def set_service_multipolicy(self, multipolicy):
        if multipolicy is None:
            return
        self.multipolicy_checkbox.set(multipolicy)
        if bool(multipolicy):
            multipolicy = self.recalculate_multipolicy_limit(multipolicy)
            self.multipolicy_limited_checkbox.wait_until_clickable()
            self.multipolicy_limited_checkbox.set(multipolicy)
            self.multipolicy_value_radio.set(multipolicy)

    @staticmethod
    def recalculate_multipolicy_limit(multipolicy):
        multipolicy_milestones = [30, 45, 60, 90, 180, 365]
        multipolicy = min(filter(lambda x: x >= multipolicy, multipolicy_milestones)) \
            if multipolicy <= max(multipolicy_milestones) \
            else max(multipolicy_milestones)
        return multipolicy

    @page_element_operation
    def set_service_pregnancy(self, pregnancy):
        if pregnancy is None:
            return
        self.pregnancy_checkbox.set(pregnancy)
        self.pregnancy_radio.set(pregnancy)

    @page_element_operation
    def set_service_property(self, service_property):
        if service_property is not None:
            logger.warning("Cannot set insurance option 'property': no associated element on the page")

    @page_element_operation
    def set_service_regularDelay(self, regularDelay):
        if regularDelay is None:
            return
        self.avia_service_checkbox.set(True)
        self.avia_regularDelay_checkbox.set(regularDelay)
        self.avia_charterDelay_checkbox.restore()

    @page_element_operation
    def set_service_relativeIllReturn(self, relativeIllReturn):
        if relativeIllReturn is None:
            return
        self.medicine_checkbox.set(True)
        self.open_or_close_hidden_additional_medicine_options(do_open=True)
        self.relativeIllReturn_checkbox.set(relativeIllReturn)

    @page_element_operation
    def set_service_sunburnAssistance(self, sunburnAssistance):
        if sunburnAssistance is None:
            return
        self.medicine_checkbox.set(True)
        self.open_or_close_hidden_additional_medicine_options(do_open=True)
        self.sunburnAssistance_checkbox.set(sunburnAssistance)

    @page_element_operation
    def set_service_terrorAssistance(self, terrorAssistance):
        if terrorAssistance is None:
            return
        self.medicine_checkbox.set(True)
        self.open_or_close_hidden_additional_medicine_options(do_open=True)
        self.terrorAssistance_checkbox.set(terrorAssistance)

    @page_element_operation
    def set_service_thirdPartyTransportation(self, thirdPartyTransportation):
        if thirdPartyTransportation is None:
            return
        self.medicine_checkbox.set(True)
        self.open_or_close_hidden_additional_medicine_options(do_open=True)
        self.thirdPartyTransportation_checkbox.set(thirdPartyTransportation)

    @page_element_operation
    def set_service_tripCancel(self, tripCancel):
        if tripCancel is None:
            return
        self.tripCancel_checkbox.set(tripCancel)
        if bool(tripCancel):
            self.show_hidden_options_for_tripCancel()
            self.tripCancel_radio.set(tripCancel)

    @page_element_operation
    def set_service_visaCancel(self, visaCancel):
        if visaCancel is None:
            return
        self.tripCancel_checkbox.set(True)
        self.visaCancel_checkbox.set(visaCancel)
        self.tripCancel_radio.restore()

    @page_element_operation
    def set_service_work(self, work):
        self.work_checkbox.set(work)

    def show_hidden_options_for_tripCancel(self):
        self.tripCancel_list_more_prices.wait_until_clickable()
        # sometimes tripCancel_list_more_prices.click() doesn't work at first several times, continue to click the
        #     button and scroll page down until trip cancel hidden options are displayed
        self.driver.execute_script("window.scrollTo(0, 0);")
        scroll_height_position = 0
        while not self.is_service_trip_cancel_3000_clickable:
            self.tripCancel_list_more_prices.click()
            scroll_height_position += 10
            self.driver.execute_script("window.scrollTo(0, %d);" % scroll_height_position)
        logger.success("Hidden options for tripCancel ('Отмена поездки') are displayed")

    def open_or_close_hidden_additional_medicine_options(self, do_open=True):
        self.medicine_more_button.wait_until_clickable()
        condition_to_open = do_open and not self.med_more_box.is_displayed()
        if condition_to_open:
            self.medicine_more_button.click()
        condition_to_close = not do_open and self.med_more_box.is_displayed()
        if condition_to_close:
            self.medicine_more_button.click()

    def set_sport(self, sport):
        self.set_sport_amateur(sport)
        self.set_sport_competition(sport)

    @page_element_operation
    def set_sport_amateur(self, sport):
        sport_name = self.db.get_sport_name_by_code(sport, competition=False)
        if sport_name is None:
            return
        if not (self.sport_amateur_input.is_displayed() and self.sport_competition_input.is_displayed()):
            self.sport_open_button.click()
        if not self.sport_amateur_input.is_displayed():
            self.sport_amateur_label.click()
        self.sport_amateur_input.click()
        self.sport_amateur_input.send_keys(sport_name)
        self.search_element_is_only_one(By.CSS_SELECTOR, ".ms-res-item-grouped")
        self.sport_amateur_dropdown_menu.click()
        logger.success("Added '%s' ('%s') to the policy sport options" % (sport, sport_name))

    @page_element_operation
    def set_sport_competition(self, sport):
        sport_name = self.db.get_sport_name_by_code(sport, competition=True)
        if sport_name is None:
            return
        if not (self.sport_amateur_input.is_displayed() or self.sport_competition_input.is_displayed()):
            self.sport_open_button.click()
        if not self.sport_competition_input.is_displayed():
            self.sport_competition_label.click()
        self.sport_competition_input.click()
        self.sport_competition_input.send_keys(sport_name)
        self.search_element_is_only_one(By.CSS_SELECTOR, ".ms-res-item-grouped")
        self.sport_amateur_dropdown_menu.click()
        logger.success("Added '%s' ('%s') to the policy sport competitions options" % (sport, sport_name))

    def close_jivosite_frame(self):
        try:
            self.driver.execute_script("document.getElementsByTagName('jdiv')[0].hidden = true;")
        except WebDriverException:
            pass

    def get_enabled_company_names(self):
        recommended_companies = self.driver.find_elements_by_css_selector(".best_offers img")
        matched_companies = self.driver.find_elements_by_css_selector(".other_offers img")
        return [x.get_attribute('alt') for x in recommended_companies + matched_companies]

    def set_travel_dates(self, start_date=None, end_date=None):
        """
        Note: not fully implemented, that's why start and end dates are None by
        default, dates are set from 10th next month to 19th next month (10 days)
        """
        # FIXME: костыль!
        period_of_stay = \
            self.app.webdriver.find_element_by_css_selector(".period-of-stay span").text
        if "10 дней" not in period_of_stay:
            self.period_of_stay.click()
            self.start_date_input.click()
            self.driver.find_elements_by_css_selector(".ui-datepicker-next")[0].click()
            self.driver.find_elements_by_css_selector(".ui-state-default")[18].click()
            self.end_date_input.click()
            self.driver.find_elements_by_css_selector(".ui-state-default")[27].click()
            self.yellow_line.click()
