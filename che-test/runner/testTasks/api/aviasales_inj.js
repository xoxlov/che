const pythonModule = require('../../classes/pythontest');
const extend = require('lodash').assign;

module.exports = function () {

    return extend(new pythonModule, {
        name: 'aviasales_inj',
        tags: ['api', 'aviasales', 'avia'],
        description: 'Проверяет возможность инъекций при формирование отчёта для aviasales с помощью соответствующих запросов',
        cmd: 'cd /var/www/che-test/scripts/autotests && source venvpython3/bin/activate;./test_aviasales_report_check_injections.py;deactivate',
        skipDefault: true
    });
};
