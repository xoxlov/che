# -*- coding: utf-8; -*-
from common.database import CheDb
from common.randomize import get_random_string
from model.payment_systems import default_payment_systems
from model.payment_systems import PartnerData


def generate_random_partner_key():
    with CheDb() as db:
        partner_keys = db.get_valid_partner_keys()
    while True:
        key = get_random_string()
        if key not in partner_keys:
            break
    return key


testdata = [
    PartnerData(
        pid=None,
        name="partner with no key",
        key=None,
        payment_systems=sorted(default_payment_systems.keys())),
    PartnerData(
        pid=None,
        name="partner with random key",
        key=generate_random_partner_key(),
        payment_systems=sorted(default_payment_systems.keys())),
]
