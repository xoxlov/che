const shellModule = require('./shellModule');
const extend = require('lodash').assign;
const log = require('fancy-log');

function stripColors(str) {
    return str.replace(/.\[\d+m/g, '');
}

function stripTime(str) {
    return str.replace(/^\[.*?\] /, '');
}

function stripPrefix(str) {
    return str.replace(/^ *(DEBUG|ERROR): /, '');
}

module.exports = function () {
    var stdoutLog = '';
    var currentTest = false;
    var currentTestCase = false;
    var errorTestName = false;

    return extend(new shellModule, {

        finishLevelInStatus: function(status) {
            this.finish({
                name: this.getLevel(),
                status: status
            });
            this.levelUp();
        },

        processOutputString: function(strWithTimeAndColor) {
            var str = stripPrefix( stripTime( stripColors(strWithTimeAndColor) ) );

            var parsedInTestOutput = {
                testStart: str.match(/> Starting (.*?) test/),
                testStepStart: str.match(/^\> (?!Starting)(.+?)(\.\.+)*$/),

                testStepSuccess: str.match(/^\< \[\+\] (.+)/),
                testStepFailed: str.match(/^\< \[\-\] (.+)/),
                testStepFailedExpected: str.match(/^\< \[\#\] (.+)/),
                testStepError: str.match(/^\< \[\!\] (.+)/),

                assertionSuccess: str.match(/^\[\+\] (.+)/),
                assertionFail: str.match(/^\[\-\] (.+)/),
                assertionFailExpected: str.match(/^\[\#\] (.+)/),
                assertionError: str.match(/^\[\!\] (.+)/)
            };

            // Test Step start with level begin
            if (parsedInTestOutput.testStepStart) {
                var testStepName = parsedInTestOutput.testStepStart[1];
                this.start({
                    name: this.addCurrentLevelTo(testStepName)
                });
            }

            // Test Step assertions with level complete
            if (parsedInTestOutput.testStepSuccess) {
                var notTestFinish = parsedInTestOutput.testStepSuccess[1].indexOf(currentTest) == -1;
                if (notTestFinish) {
                    this.finishLevelInStatus('success');
                }
            }
            if (parsedInTestOutput.testStepFailed) {
                var notTestFinish = parsedInTestOutput.testStepFailed[1].indexOf(currentTest) == -1;
                if (notTestFinish) {
                    this.finishLevelInStatus('failed');
                }
            }
            if (parsedInTestOutput.testStepFailedExpected) {
                var notTestFinish = parsedInTestOutput.testStepFailedExpected[1].indexOf(currentTest) == -1;
                if (notTestFinish) {
                    this.finishLevelInStatus('expectedfail');
                }
            }
            if (parsedInTestOutput.testStepError) {
                var notTestFinish = parsedInTestOutput.testStepError[1].indexOf(currentTest) == -1;
                if (notTestFinish) {
                    this.finishLevelInStatus('error');
                }
            }

            // Single checks assertions
            if (parsedInTestOutput.assertionSuccess) {
                this.finish({
                    name: this.addCurrentLevelTo(parsedInTestOutput.assertionSuccess[1]),
                    status: 'success'
                });
            }
            if (parsedInTestOutput.assertionFail) {
                this.finish({
                    name: this.addCurrentLevelTo(parsedInTestOutput.assertionFail[1]),
                    status: 'failed'
                });
            }
            if (parsedInTestOutput.assertionFailExpected) {
                this.finish({
                    name: this.addCurrentLevelTo(parsedInTestOutput.assertionFailExpected[1]),
                    status: 'expectedfail'
                });
            }
            if (parsedInTestOutput.assertionError) {
                this.finish({
                    name: this.addCurrentLevelTo(parsedInTestOutput.assertionError[1]),
                    status: 'error'
                });
            }
        },

        // Process output  and error pipes
        processOutput: function (stdoutBuffer) {
            var stdout = stdoutBuffer.toString();
            stdoutLog += stdout;

            stdout.split("\n").forEach(this.processOutputString, this);
        },

        processErrorOutput: function (stderrBuffer) {
            this.processOutput(stderrBuffer);
        },

        getFullLog: function () {
            return stdoutLog;
        }
    });
};
