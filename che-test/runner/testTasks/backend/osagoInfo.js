const phpunitModule = require('./phpunit');
const extend = require('lodash').assign;

module.exports = function () {

    return extend(new phpunitModule, {
        name: 'osagoInfo',
        tags: ['api', 'osago'],
        description: 'Модульные тесты для osago-info',
        cmd: 'cd /var/www/osago-info && phpunit --debug --verbose'
    });
};