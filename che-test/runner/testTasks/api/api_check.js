const pythonModule = require('../../classes/pythontest');
const extend = require('lodash').assign;

module.exports = function () {

    return extend(new pythonModule, {
        name: 'api_check',
        tags: ['api'],
        description: 'Проверяет работу cherehapa api при выписке и удалении полисов',
        cmd: 'cd /var/www/che-test/scripts/autotests && source venvpython3/bin/activate;py.test ./test/test_che_api_check.py;deactivate',
        skipDefault: true
    });
};
