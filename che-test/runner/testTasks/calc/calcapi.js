const shellModule = require('../../classes/shellModule');
const extend = require('lodash').assign;

module.exports = function () {
    var fullLog = '';
    var currentCompany = false;
    var currentRequest = false;

    return extend(new shellModule, {
        name: 'calcApi',
        tags: ['calc'],
        description: 'Проводит сверку расчетов нашего калькулятора и API страховых компаний на тестах из правил. ' +
                     'Более 65к тестов!',
        cmd: 'cd /var/www/che-partner/public_html/ && php artisan test:calculate --no-ansi',
        skipDefault: true,

        processOutputRecord: function(logRecord) {
            var parse = {
                companyStart: logRecord.match(/Начинаю обработку компании (.*?)\.\.\./),
                requestStart: logRecord.match(/ +[0-9]+: (.*)/),
                testSuccessful: logRecord.match(/^[\. ]+Продукт (.*?) \(id=[0-9]+\) +\+\+\+ +CALC ([0-9\.\(\)]+)/),
                testFailed: logRecord.match(/^[\. ]+Продукт (.*?) \(id=[0-9]+\) +\!\!\! +CALC ([0-9\.\(\)]+) != API ([0-9\.\(\)]+)/),
                testUnknown: logRecord.match(/^[\. ]+Продукт (.*?) \(id=[0-9]+\) +\?\?\? +(.*)/)
            };

            if (parse.companyStart) {
                if (currentCompany) {
                    this.finish({
                        name: [currentCompany]
                    });
                    currentRequest = false;
                }

                currentCompany = parse.companyStart[1];
                this.start({
                    name: [currentCompany]
                })
            }

            if (parse.requestStart) {
                if (currentRequest) {
                    this.finish({
                        name: [currentCompany, currentRequest]
                    });
                }

                currentRequest = parse.requestStart[1];
                this.start({
                    name: [currentCompany, currentRequest]
                });
            }

            if (parse.testSuccessful) {
                this.finish({
                    name: [currentCompany, currentRequest, parse.testSuccessful[1]],
                    status: 'success',
                    message: 'Расчет совпал ['+parse.testSuccessful[2]+']'
                });
            }

            if (parse.testFailed) {
                this.finish({
                    name: [currentCompany, currentRequest, parse.testFailed[1]],
                    status: 'failed',
                    message: 'Наш расчет ['+parse.testFailed[2]+'] не совпал с API СК ['+parse.testFailed[3]+']'
                })
            }

            if (parse.testUnknown) {
                this.finish({
                    name: [currentCompany, currentRequest, parse.testUnknown[1]],
                    message: parse.testUnknown[2]
                })
            }
        },
    
        processOutput: function (stdoutBuffer) {
            var stdout = stdoutBuffer.toString();
            var exception = stdout.match(/^ *\[([a-zA-Z]+Exception)\] *((.*\n)+?)\n$/m);
            fullLog += stdout;

            if (exception) {
                var type = exception[1].replace(/ +/g, ' ').replace(/^ +/,'').replace(/ +$/,'');
                var descr = exception[2].replace(/\n/g, ' ').replace(/ +/g, ' ');

                this.debug({
                    name: [],
                    message: type+':'+descr
                })
            }
            else {
                stdout.split("\n").forEach(this.processOutputRecord, this);
            }
        },
    
        processErrorOutput: function (stderrBuffer) {
            this.processOutput(stderrBuffer);
        },
    
        getFullLog: function () {
            return fullLog;
        }
    });
};