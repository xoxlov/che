# -*- coding: utf-8; -*-


valid_letters = "АВЕКМНОРСТУХ"
translit = {
    "А": "A",
    "В": "B",
    "Е": "E",
    "К": "K",
    "М": "M",
    "Н": "H",
    "О": "O",
    "Р": "P",
    "С": "C",
    "Т": "T",
    "У": "Y",
    "Х": "X",
}
invalid_letters = "БГДЁЖЗИЙЛПФЦЧШЩЪЫЬЭЮЯ"


class DriverLicense:

    def __init__(self, seriez, number, valid=True):
        self.seriez = seriez
        self.number = number
        self.valid = bool(valid)

    def __eq__(self, other):
        return other is not None and self.seriez == other.seriez and self.number == other.number

    def __repr__(self):
        return " ".join(["Driver License:", self.seriez, self.number])

    def __str__(self):
        return (" ".join([self.seriez, self.number])).strip()
