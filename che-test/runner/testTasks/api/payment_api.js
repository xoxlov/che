const pythonModule = require('../../classes/pythontest');
const extend = require('lodash').assign;

module.exports = function () {

    return extend(new pythonModule, {
        name: 'payment_api',
        tags: ['api'],
        description: 'Проверяет соответствие платёжных систем для клиентов в базе и полученных через API',
        cmd: 'cd /var/www/che-test/scripts/autotests && source venvpython3/bin/activate;py.test ./test/test_payment_systems_api.py;deactivate',
        skipDefault: false
    });
};