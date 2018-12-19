# -*- coding: utf-8; -*-


class Address:

    def __init__(self, address, valid=True):
        self.address = address
        self.valid = bool(valid)

    def __eq__(self, other):
        return other is not None and self.address == other.address

    def __repr__(self):
        return " ".join(["Address:", self.address])

    def __str__(self):
        return self.address
