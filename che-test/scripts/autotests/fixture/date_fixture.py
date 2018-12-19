# -*- coding: utf-8; -*-
import pytest
from datetime import datetime, timedelta


@pytest.fixture()
def today():
    return datetime.today().strftime("%d.%m.%Y")


@pytest.fixture()
def tomorrow():
    return (datetime.today() + timedelta(days=1)).strftime("%d.%m.%Y")
