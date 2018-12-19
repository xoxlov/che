const pythonModule = require('../../classes/pythontest');
const extend = require('lodash').assign;

module.exports = function () {

    return extend(new pythonModule, {
        name: 'biletix_html',
        tags: ['api'],
        description: 'Проверяет работу cherehapa api с созданием html писем для biletix',
        cmd: 'cd /var/www/che-test/scripts/autotests && source venvpython3/bin/activate;py.test ./test/test_biletix_html.py;deactivate',
        skipDefault: true
    });
};
