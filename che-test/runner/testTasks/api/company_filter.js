const pythonModule = require('../../classes/pythontest');
const extend = require('lodash').assign;

module.exports = function () {

    return extend(new pythonModule, {
        name: 'company_filter_api',
        tags: ['api'],
        description: 'Проверяет в API фильтрацию компаний для партнёров',
        cmd: 'cd /var/www/che-test/scripts/autotests && source venvpython3/bin/activate;py.test ./test/test_company_filtering_api.py;deactivate',
        skipDefault: true
    });
};
