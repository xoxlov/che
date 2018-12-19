# -*- coding: utf-8; -*-
from common.system import execute_native_shell_command
from common.database import CheDb


def request_currency(verbose=False):
    """Executes external command 'php artisan currency:fetch' to fetch
       currency. This command adds currency values to database.
    """
    command = "cd /var/www/che-partner/public_html ; php artisan currency:fetch"
    result = execute_native_shell_command(command)
    verbose and print(result.get("stdout"))
    assert not result.get("stderr")


def verify_currency_is_set_for_today():
    with CheDb() as db:
        assert db.get_euro_exchange_rate(), "Euro exchange rate is not available"
        assert db.get_dollar_exchange_rate(), "Dollar exchange rate is not available"
