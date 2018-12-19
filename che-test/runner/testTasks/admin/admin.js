const shellModule = require('../../classes/shellModule');
const extend = require('lodash').assign;

module.exports = function () {
    var skipProcessing = false;

    return extend(new shellModule, {
        name: 'admin',
        tags: ['admin'],
        description: 'Тестирование админки',
        cmd: 'cd /var/www/che-admin/public_html && npm run test:json',
        skipDefault: false,

        processOutputRecord: function(logRecord) {
            if (skipProcessing) {
                return;
            }

            if (~logRecord.indexOf('{')) {
                const { testResults } = JSON.parse(logRecord);
                testResults.forEach((testResult) => {
                    testResult.assertionResults.forEach((result) => {
                        if (result.status === 'passed') {
                            this.finish({
                                name: [result.title],
                                status: 'success'
                            });
                        } else {
                            this.finish({
                                name: [result.title],
                                status: 'failed',
                                message: result.failureMessages
                            })
                        }
                    });
                });
            }
            if (~logRecord.indexOf('PASS') && !~logRecord.indexOf('{')) {
                console.log(logRecord)
            }
        },

        processOutput: function (stdoutBuffer) {
            var stdout = stdoutBuffer.toString();
            stdout.split("\n").forEach(this.processOutputRecord, this);
        },

        processErrorOutput: function (stderrBuffer) {
            this.processOutput(stderrBuffer);
        },

        getFullLog: function () {

        }
    });
};