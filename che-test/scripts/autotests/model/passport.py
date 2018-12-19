# -*- coding: utf-8; -*-


class Passport:

    def __init__(self, seriez, number, sep=" ", valid=True):
        self.seriez = seriez
        self.number = number
        self.valid = bool(valid)
        self.sep = sep

    def __eq__(self, other):
        return other is not None and self.seriez == other.seriez and self.number == other.number

    def __repr__(self):
        return "".join([
            "Passport:",
            self.seriez,
            self.sep,
            self.number,
        ])

    def __str__(self):
        return ("".join([self.seriez, self.sep, self.number])).strip()
