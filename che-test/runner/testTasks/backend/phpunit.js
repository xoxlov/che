const shellModule = require('../../classes/shellModule');
const extend = require('lodash').assign;

module.exports = function () {
    var fullLog = '';
    var currentTest = false;
    var currentTestCase = false;
    var testsDone = false;

    return extend(new shellModule, {
        name: 'phpunit',
        tags: ['backend'],
        description: 'Проводит модульное тестирование кода на laravel при помощи phpunit',
        cmd: 'cd /var/www/che-partner/public_html && phpunit --debug --verbose',
    
        finishTest: function () {
            this.finish({
                name: this.getLevel()
            });
            this.levelUp();
        },
        
        processOutputRecord: function(logRecord) {
            var parsed = {
                newTest: logRecord.match(/Starting test '(.*?)'./),
                testSuccessful: logRecord.match(/^\.$/),
                assertionFailed: logRecord.match(/^F$/),
                testFailed: logRecord.match(/^([ERSI])$/),
                allDone: logRecord.match(/^Time: (.*?), Memory: (.*?)$/)
            };
    
            if (parsed.newTest) {
                var nameParts = parsed.newTest[1].split('::');
                var newTestName = nameParts[0];
                var newTestCase = nameParts[1];
    
                if (currentTest != newTestName) {
                    if (currentTest) {
                        this.finishTest();
                    }
    
                    currentTest = newTestName;
                    this.start({
                        name: this.addCurrentLevelTo(newTestName)
                    });
                }
    
                currentTestCase = newTestCase;
            }
    
            if (parsed.testSuccessful && !testsDone) {
                this.finish({
                    name: this.addCurrentLevelTo(currentTestCase),
                    status: 'success'
                });
            }
    
            if (parsed.assertionFailed) {
                this.finish({
                    name: this.addCurrentLevelTo(currentTestCase),
                    status: 'fail'
                });
            }
    
            if (parsed.testFailed) {
                this.finish({
                    name: this.addCurrentLevelTo(currentTestCase),
                    status: 'error'
                });
            }
    
            if (parsed.allDone) {
                this.finishTest();
                testsDone = true;
                currentTestCase = false;
            }
        },
    
        parseTestErrors: function(errorRecord) {
            var parse = {
                testName: errorRecord.match(/^(.*?::.*?)$/m),
                errorDescription: errorRecord.match(/(.*?[a-zA-Z]+.*?)\n\n/m)
            };
    
            if (parse.errorDescription && currentTestCase) {
                var nameParts = currentTestCase.split('::');
    
                this.debug({
                    name: nameParts,
                    message: parse.errorDescription[1]
                });
                currentTestCase = false;
            }
    
            if (parse.testName) {
                currentTestCase = parse.testName[1];
            }
        },
    
        processOutput: function (stdoutBuffer) {
            var stdout = stdoutBuffer.toString();
            fullLog += stdout;
    
            if (!testsDone) {
                stdout.split("\n").forEach(this.processOutputRecord, this);
            }
            else {
                stdout.split(/^[0-9]+\) /m).forEach(this.parseTestErrors, this);
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