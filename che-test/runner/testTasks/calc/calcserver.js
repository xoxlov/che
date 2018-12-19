const shellModule = require('../../classes/shellModule');
const extend = require('lodash').assign;

function stripColors(str) {
    return str.replace(/.\[\d+m/g, '');
}

module.exports = function () {
    var fullLog = '';
    var currentTest = false;
    var skipProcessing = false;

    return extend(new shellModule, {
        name: 'calcserver',
        tags: ['calc'],
        description: 'Проводит проверку вычислений серверного калькулятора на тестах из правил',
        cmd: 'cd /var/www/che-calc && npm run testCalc',
        skipDefault: true,

        processOutputRecord: function(logRecord) {
            if (skipProcessing) {
                return;
            }

            var parse = {
                testStart: logRecord.match(/^Running: (.*?)...$/),
               //суть тестового утверждения, то что попадёт в test.message в defaultReporter.js
                assertionSuccessful: logRecord.match(/ *✔ (.*)$/),
               //суть тестового утверждения, то что попадёт в test.message в defaultReporter.js
                assertionFailed: logRecord.match(/ *✖ (.*?): (.*)$/),
                skipProcessing: logRecord.match(/^\-+$/)
            };

            if (parse.testStart) {
                if (currentTest) {
                    this.finish({name: [currentTest]});
                }

                currentTest = parse.testStart[1];
                this.start({name: [currentTest]});
            }

            if (parse.assertionSuccessful) {
                var testName = parse.assertionSuccessful[1];
                this.finish({
                    name: this.addCurrentLevelTo(testName),
                    status: 'success'
                });
            }

            if (parse.assertionFailed) {
                var testName = parse.assertionFailed[1];
                this.finish({
                    name: this.addCurrentLevelTo(testName),
                    status: 'failed',
                    message: parse.assertionFailed[2]
                })
            }

            if (parse.skipProcessing) {
                skipProcessing = true;
                this.finish({name: [currentTest]});
                currentTest = false;
            }
        },
    
        processOutput: function (stdoutBuffer) {
            var stdout = stripColors(stdoutBuffer.toString());
            fullLog += stdout;

            stdout.split("\n").forEach(this.processOutputRecord, this);
        },
    
        processErrorOutput: function (stderrBuffer) {
            this.processOutput(stderrBuffer);
        },
    
        getFullLog: function () {
            return fullLog;
        }
    });
};
