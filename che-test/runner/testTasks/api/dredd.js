const shellModule = require('../../classes/shellModule');
const extend = require('lodash').assign;

module.exports = function () {
    var fullLog = '';
    var testsProcessing = true;
    var lastFailedTestName;
    
    return extend(new shellModule, {
        name: ['dredd'],
        tags: ['api'],
        description: 'Запускает клиент-серверную проверку API по документации: формата, параметров в выдаче' +
            ' разных методов',
        cmd: 'cd /var/www/che-test/runner && npm run dredd',
        artifacts: [
            '../../che-test/scripts/dredd-api-testing/dredd-tests.xml',
            '../../che-test/scripts/dredd-api-testing/dredd-tests.*.xml',
            '../../che-test/scripts/dredd-api-testing/*.log',
        ],
    
        trim: function(str) {
            return str.replace(/^\s+|\s+$/g, "");
        },
        
        getTestName: function (rawStr) {
            var testName = rawStr.replace(/\?.*/, '');

            if (testName.indexOf('quote') != -1) {
                var typeMatch = rawStr.match(/type=([a-z]+)/);
                if (typeMatch) {
                    testName += ' type='+typeMatch[1];
                }
            }
            
            return testName;
        },
    
        processOutputRecord: function(logRecord) {
            logRecord = this.trim(logRecord);
            var testName;
    
            if (testsProcessing) {
                var parsed = {
                    testSuccessful: logRecord.match(/^pass: ([A-Z]+ .*?) duration/),
                    testFailed: logRecord.match(/^fail: ([A-Z]+ .*?) duration/),
                    testsDone: logRecord.match(/^info: Displaying failed tests\.\.\./)
                };
    
                if (parsed.testSuccessful) {
                    testName = this.getTestName(parsed.testSuccessful[1]);
                    
                    this.finish({
                        name: this.addCurrentLevelTo(testName),
                        status: 'success'
                    });
                }
    
                if (parsed.testFailed) {
                    testName = this.getTestName(parsed.testFailed[1]);
                    this.finish({
                        name: this.addCurrentLevelTo(testName),
                        status: 'error'
                    });
                }
    
                if (parsed.testsDone) {
                    testsProcessing = false;
                }
            }
            else {
                var errorText;
                var parsedError = {
                    failedTest: logRecord.match(/^fail: ([A-Z]{3,} .*?) duration/m),
                    failErrorInfo: logRecord.match(/fail: (.*?\.)$/m),
                    failInfo: logRecord.match(/fail: ([a-z]+:(.*?(\n)*)+)/m)
                };
    
                if (parsedError.failedTest) {
                    lastFailedTestName = this.getTestName(parsedError.failedTest[1]);
                }
    
                if (parsedError.failErrorInfo) {
                    errorText = parsedError.failErrorInfo[1];
                    this.finish({
                        name: this.addCurrentLevelTo(lastFailedTestName),
                        status: 'error',
                        message: errorText
                    });
                }
    
                if (parsedError.failInfo) {
                    errorText = parsedError.failInfo[1]
                        .replace(/^fail: /, '')
                        .split("\n")
                        .join(', ');
                    this.finish({
                        name: this.addCurrentLevelTo(lastFailedTestName),
                        status: 'error',
                        message: errorText
                    });
                }
            }
        },
    
        processOutput: function (stdoutBuffer) {
            var stdout = stdoutBuffer.toString();
            fullLog += stdout;
    
            stdout.split(/[0-9\-\.:TZ]+ - /m).forEach(this.processOutputRecord, this);
        },
    
        processErrorOutput: function (stderrBuffer) {
            this.processOutput(stderrBuffer);
        },
    
        getFullLog: function () {
            return fullLog;
        }
    });
};
