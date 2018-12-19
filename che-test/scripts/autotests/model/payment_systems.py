# -*- coding: utf-8; -*-
from collections import namedtuple


PartnerTuple = namedtuple(
    "PartnerTuple",
    "pid "
    "name "
    "key "
    "psp_payment_id "
    "psp_including_relation "
    "psp_excluding_relation "
    "psp_exclusive_relation",
    verbose=False)


default_payment_systems = {
    7: "Payture",
    8: "Cashless (wire) payment",
    188: "Coupons",
}


class PartnerData:
    def __init__(self, pid, name, key, payment_systems):
        self.pid = pid
        self.name = name
        self.key = key
        self.payment_systems = payment_systems

    def __repr__(self):
        return "Partner id={}: {} [key={}]".format(self.pid, self.name, self.key)

    def __str__(self):
        return "Partner id={}: {} [key={}]".format(self.pid, self.name, self.key)
