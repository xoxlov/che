const shellModule = require('../../classes/shellModule');
const extend = require('lodash').assign;

module.exports = function () {
    var hasAnyTestCompleted = false;
    var fullLog = '';
    var currentTest;

    return extend(new shellModule, {
        name: 'compiler',
        tags: ['compiler', 'calc'],
        description: 'Осуществляет unit-тестирование кода компилятора',

        cmd: 'cd /var/www/che-calc/tests && nightwatch -e "vagrant"',
        artifacts: ['../../che-calc/tests/reports'],

        processOutputRecord: function (logRecord) {
            var parsed = {
                newTest: logRecord.match(/^(\[(.*?)\] Test Suite|([a-zA-Z]+))$/),
                newTestCase: logRecord.match(/Running\: +(.*)$/),
                emptyTestCase: logRecord.match(/^No assertions ran\./),
                successfulTestCase: logRecord.match(/OK\. +([0-9]+) assertions passed\. +\(([0-9\. hms/]+)\)/),
                failedTestCase: logRecord.match(/FAILED: +([0-9]+) assertions failed and ([0-9]+) passed +\(([0-9\. hms/]+)\)/),
                error: logRecord.match(/ERROR: +(.*?)$/),
                seleniumError: logRecord.match(/WARN - (.*[Ff]ail.*)$/),
                successfulAssertion: logRecord.match(/✔ (.*)$/),
                failedAssertion: logRecord.match(/✖ (.*?(Failed|expected).*)$/)
            };

            if (parsed.successfulTestCase) {
                this.finish({
                    name: this.getLevel(),
                    status: 'successful'
                });
                this.levelUp();
            }

            if (parsed.successfulAssertion) {
                this.finish({
                    name: this.addCurrentLevelTo(parsed.successfulAssertion[1]),
                    status: 'success'
                });
            }

            if (parsed.failedTestCase) {
                this.finish({
                    name: this.getLevel(),
                    status: 'failed'
                });
                this.levelUp();
            }
            
            if (parsed.emptyTestCase) {
                this.finish({
                    name: this.getLevel()
                });
                this.levelUp();
            }

            var errorMessage = false;
            if (parsed.error) {
                errorMessage = parsed.error[1];
            }

            if (parsed.seleniumError) {
                errorMessage = parsed.seleniumError[1];
            }

            if (parsed.failedAssertion) {
                errorMessage = parsed.failedAssertion[1];
            }

            if (errorMessage) {
                this.finish({
                    name: currentTest,
                    status: 'error',
                    message: errorMessage
                });
                currentTest = false;
            }

            if (parsed.newTest) {
                this.testFinish();
                var newTestName = parsed.newTest[2]
                    ? parsed.newTest[2]
                    : parsed.newTest[1];

                currentTest = this.addCurrentLevelTo(newTestName);
                this.start({
                    name: currentTest
                });
            }

            if (parsed.newTestCase) {
                this.start({
                    name: this.addCurrentLevelTo(parsed.newTestCase[1])
                });
            }
        },

        processOutput: function (stdoutBuffer) {
            var stdout = stdoutBuffer.toString();
            fullLog += stdout;

            stdout.split("\n").forEach(this.processOutputRecord, this);
        },

        processErrorOutput: function (stderr) {
            var ignore = stderr.toString().match(/warning/i);

            if (!ignore) {
                this.debug({name: this.getLevel(), message: stderr});
            }
        },

        testFinish: function () {
            if (hasAnyTestCompleted) {
                this.finish({
                    name: this.getLevel()
                });
                this.levelUp();
            }

            hasAnyTestCompleted = true;
        },

        getFullLog: function () {
            return fullLog;
        }
    });
};
