const processRunner = require('./processRunner');
const baseModule = require('./baseModule');
const args = require('yargs').argv;
const extend = require('lodash').assign;

module.exports = function () {
    return extend(new baseModule, {
        cmd: 'whoami',

        run: function () {
            var callbackContext = this;
            var run = processRunner.runInLocalShell;
    
            if (args.vagrant) {
                run = processRunner.runInVagrant;
            }

            run(this.cmd, this.processOutput, this.processErrorOutput, this.processFinish, callbackContext);
        },

        processFinish: function (exitcode) {
            if (typeof(this.testFinish) == 'function') {
                this.testFinish();
            }
    
            var isSuccess = exitcode == 0;

            this.finishModule({
                status: isSuccess ? 'success' : 'error',
                exitcode: exitcode
            });
        }
    });
};