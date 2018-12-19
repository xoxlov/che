const pythonModule = require('../../classes/pythontest');
const extend = require('lodash').assign;

module.exports = function () {

    return extend(new pythonModule, {
        name: 'company_filter_web',
        tags: ['frontend'],
        description: 'Тест фильтрации страховых компаний для партнеров с использованием веб-интерфейса.',
        cmd: 'cd /var/www/che-test/scripts/autotests && source venvpython3/bin/activate; xvfb-run --server-args="-screen 0, 1920x1080x24" py.test ./test/test_company_filtering_web.py;deactivate',
        skipDefault: true
    });
};
