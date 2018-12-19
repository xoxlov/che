const pythonModule = require('../../classes/pythontest');
const extend = require('lodash').assign;

module.exports = function () {

    return extend(new pythonModule, {
        name: 'osago_web',
        tags: ['frontend'],
        description: 'Реализация тестовых кейсов для фронтенда ОСАГО.',
        cmd: 'cd /var/www/che-test/scripts/autotests && source venvpython3/bin/activate; xvfb-run --server-args="-screen 0, 1920x1080x24" py.test ./test/test_osago_*.py;deactivate',
        skipDefault: true
    });
};
