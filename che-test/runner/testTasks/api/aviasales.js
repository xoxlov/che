const pythonModule = require('../../classes/pythontest');
const extend = require('lodash').assign;

module.exports = function () {

    return extend(new pythonModule, {
        name: 'aviasales',
        tags: ['api', 'aviasales', 'avia'],
        description: 'Проверяет формирование отчёта для aviasales',
        cmd: 'cd /var/www/che-test/scripts/autotests && source venvpython3/bin/activate;./test_aviasales_report_check.py;deactivate',
        skipDefault: true
    });
};