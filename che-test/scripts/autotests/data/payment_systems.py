# -*- coding: utf-8; -*-
from common.database import CheDb
from model.payment_systems import default_payment_systems
from model.payment_systems import PartnerData, PartnerTuple


def get_partners_data_from_db():
    query = "SELECT partners.id, partners.name, apiKeys.key, psp.paymentId, " \
            "psp.isIncludingRelation, psp.isExcludingRelation, " \
            "psp.isExclusiveRelation " \
            "FROM partners " \
            "LEFT JOIN paymentSystemsPartners as psp " \
            "ON partners.id=psp.partnerId " \
            "LEFT JOIN apiKeys " \
            "ON apiKeys.partnerId=partners.id " \
            "WHERE apiKeys.key is not NULL"
    with CheDb() as db:
        db_response = db.execute_query(query)
    partner_tuples = [
        PartnerTuple(
            pid, name, key, psp_payment_id,
            psp_including_relation,
            psp_excluding_relation,
            psp_exclusive_relation)
        for pid, name, key, psp_payment_id,
            psp_including_relation,
            psp_excluding_relation,
            psp_exclusive_relation
        in db_response
    ]
    return partner_tuples


def get_payment_systems_by_partner(partner_tuples, partner_id):
    # look for isIncluding relationships
    payments = set(x.psp_payment_id for x in partner_tuples
                   if x.pid == partner_id and x.psp_including_relation)
    # look for isExclusive relationships
    payments = payments.union(set(x.psp_payment_id for x in partner_tuples
                                  if x.pid == partner_id
                                  and x.psp_exclusive_relation))
    # if no isIncluding/isExclusive relationship found then set defaults
    if not payments:
        payments = set(default_payment_systems)
    # add isExcluding relationship, remove them from set
    payments = payments.difference(set(x.psp_payment_id for x in partner_tuples
                                       if x.pid == partner_id
                                       and x.psp_excluding_relation))
    return sorted(list(payments))


partners_data = get_partners_data_from_db()
testdata = [
    PartnerData(
        pid=p.pid,
        name=p.name,
        key=p.key,
        payment_systems=get_payment_systems_by_partner(partners_data, p.pid)
    )
    for p in partners_data
]
