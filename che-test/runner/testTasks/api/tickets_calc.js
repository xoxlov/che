const pythonModule = require('../../classes/pythontest');
const extend = require('lodash').assign;

module.exports = function () {

    return extend(new pythonModule, {
        name: 'v1Calculation',
        tags: ['api', 'tickets', 'avia'],
        description: 'Осуществляет проверку расчетов авиастрахования через API v1 (используется tickets.ru)',
        cmd: 'cd /var/www/che-test/scripts/autotests && source venvpython3/bin/activate;./test_tickets_api_check_calculation.py;deactivate',
        skipDefault: true
    });
};