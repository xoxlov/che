const spawn = require('child_process').spawn;
const vagrantWorkingDir = process.cwd()+'/../../..';
const args = require('yargs').argv;
const _ = require('lodash');

var envValue = process.env.NODE_ENV || 'development';
var env = _.clone(process.env) || {};
if (args.env) {
    envValue = args.env;
}

env.NODE_ENV = envValue;

function runInShell(shell, params, stdoutProcessor, stderrProcessor, finishCallback, context) {
    var process = spawn(shell, params, {cwd: vagrantWorkingDir, env: env});

    if (!context) {
        context = global;
    }

    process.stdout.on('data', function (stdoutBuffer) {

        stdoutProcessor.call(context, stdoutBuffer);
    });
    process.stderr.on('data', function (stderrBuffer) {
        stderrProcessor.call(context, stderrBuffer);
    });
    process.on('close', function (exitcode) {
        finishCallback.call(context, exitcode);
    });
}

function runInVagrant(command, stdoutProcessor, stderrProcessor, finishCallback, context) {
    runInShell('vagrant', ['ssh', '-c', command], stdoutProcessor, stderrProcessor, finishCallback, context);
}

function runInLocalShell(command, stdoutProcessor, stderrProcessor, finishCallback, context) {
    runInShell('bash', ['-a', '-c', command], stdoutProcessor, stderrProcessor, finishCallback, context);
}

module.exports = {
    runInVagrant: runInVagrant,
    runInLocalShell: runInLocalShell
};