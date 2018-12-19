const request = require('request');
const baseModule = require('../../classes/baseModule');
const config = require('../../../../che-static/config/config.js') || {};
const extend = require('lodash').assign;

module.exports = function () {
    return extend(new baseModule, {
        name: 'calc',
        tags: ['api', 'calc'],
        description: 'Запускает внутренний backend-калькулятора и проверяет результаты тестового расчета',
        responseBody: null,
        artifacts: ['../../che-calc/public_html/logs'],

        run: function () {
            var module = this;
            this.start({
                name: ['testCalc']
            });

            request({
                url: config.api.calcBase+'test'
            }, function (err, response, body) {
                if (err) {
                    module.finish({
                        name: ['testCalc'],
                        status: 'error',
                        message: err.toString()
                    });

                    module.finishRequest();
                    return;
                }

                this.responseBody = body;
                try {
                    var res = JSON.parse(body);
                    if (res && res.status == 200 && res.data && res.data[0] && res.data[0].price > 0) {
                        module.finish({
                            name: ['testCalc', 'Проверка результата'],
                            status: 'success'
                        });
                    }
                    else {
                        var error = res && res.data && res.data.error
                            ? res.data.error
                            : "Получены данные в неверном формате";

                        module.finish({
                            name: ['testCalc', 'Проверка результата'],
                            status: 'failed',
                            message: error
                        });
                    }
                }
                catch (error) {
                    module.finish({
                        name: ['testCalc'],
                        status: 'error',
                        message: body
                    });
                }

                module.finishRequest();
            });

        },

        finishRequest: function () {
            this.finishModule();
        },

        getFullLog: function () {
            return this.responseBody;
        }
    });


};
