# -*- coding: utf-8; -*-
import os
import jsonpickle
import importlib
from app.osago_app import CheWebOsagoApplication
from app.vzr_app import CheWebVzrApplication
from common.database import CheDb

# Test Cases preconditions from external fixture
from fixture.date_fixture import *


app_fixture = None
db_fixture = None


@pytest.fixture()
def osago_web_app(request):
    global app_fixture
    if not isinstance(app_fixture, CheWebOsagoApplication):
        if "destroy" in dir(app_fixture):
            app_fixture.destroy()
        del app_fixture
        app_fixture = None
    if app_fixture is None:
        app_fixture = CheWebOsagoApplication()
    assert app_fixture.webdriver, "Browser not started"
    return app_fixture


@pytest.fixture()
def vzr_web_app(request):
    global app_fixture
    if not isinstance(app_fixture, CheWebVzrApplication):
        if "destroy" in dir(app_fixture):
            app_fixture.destroy()
        del app_fixture
        app_fixture = None
    if app_fixture is None:
        app_fixture = CheWebVzrApplication()
        app_fixture.prepare_driver_and_pages()
    app_fixture.reset_url_params()
    assert app_fixture.webdriver, "Browser not started"
    return app_fixture


@pytest.fixture(scope="session", autouse=True)
def stop_app(request):
    def fin():
        if "destroy" in dir(app_fixture):
            app_fixture.destroy()
    request.addfinalizer(fin)
    return app_fixture


def pytest_generate_tests(metafunc):
    for fixture in metafunc.fixturenames:
        # pytest parametrizing is made in this way to correctly print russian
        # characters, see https://ru.stackoverflow.com/questions/768401/
        if fixture.startswith("data_"):
            testdata = load_from_module(fixture[5:])
            metafunc.parametrize(fixture,
                                 [pytest.param(test_args, id=test_id)
                                  for test_args, test_id
                                  in zip(testdata, [repr(x) for x in testdata])
                                  ])
        elif fixture.startswith("json_"):
            testdata = load_from_json(fixture[5:])
            metafunc.parametrize(fixture,
                                 [pytest.param(test_args, id=test_id)
                                  for test_args, test_id
                                  in zip(testdata, [repr(x) for x in testdata])
                                  ])


def load_from_module(module):
    return importlib.import_module("data.%s" % module).testdata


def load_from_json(file):
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "data/%s.json" % file)) as f:
        return jsonpickle.decode(f.read())


@pytest.fixture(scope="session")
def db(request):
    global db_fixture
    if db_fixture is None:
        db_fixture = CheDb()

    def fin():
        db_fixture.destroy()
    request.addfinalizer(fin)
    return db_fixture
