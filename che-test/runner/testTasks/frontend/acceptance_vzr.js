const pythonModule = require('../../classes/pythontest');
const extend = require('lodash').assign;

module.exports = function () {

    return extend(new pythonModule, {
        name: 'acceptance_vzr',
        tags: ['acceptance', 'frontend'],
        description: 'Комплексный тест процесса покупки страховых полисов через веб-интерфейс.',
        cmd: 'cd /var/www/che-test/scripts/autotests && source venvpython3/bin/activate; xvfb-run --server-args="-screen 0, 1920x1080x24" ./test_acceptance_vzr.py;deactivate',
        skipDefault: true
    });
};