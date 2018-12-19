const log = console.log;
const timestampLog = require('fancy-log');
const args = require('yargs').argv;
const glob = require('glob');
const path = require('path');
const fs = require('fs');
const _ = require('lodash');
const colors = require('chalk');
const Runner = require('./classes/runner.js');
const DefaultReporter = require('./classes/defaultReporter');


function loadTestModules(groups, modules, forceAll) {
    var allTests = glob.sync('testTasks/**/*.js');
    var matchingModules = {};
    var noGroupsSpecified = groups.length == 0;
    var anyGroupIsSpecified = groups.length > 0;
    var noModulesSpecified = modules.length == 0;

    allTests.forEach(function (fileName) {
        var moduleName = path.basename(fileName).replace(/\..*$/, '');
        var absoluteFileName = process.cwd()+'/'+fileName;
        var TestModuleClass = require(absoluteFileName);
        var testModule = new TestModuleClass();

        var isInGroups = (anyGroupIsSpecified && _.intersection(testModule.tags, groups).length > 0) || (noGroupsSpecified && noModulesSpecified);
        var explicitlyDefined = modules.indexOf(moduleName) != -1;
        var usedByDefault = !testModule.skipDefault;
        var canBeUsed = usedByDefault || explicitlyDefined || forceAll;

        if ((isInGroups || explicitlyDefined) && canBeUsed) {
            matchingModules[moduleName] = testModule;
        }
    });

    return matchingModules;
}

function loadAllTestModules() {
    return loadTestModules([], [], true);
}

function padString(length) {
    return new Array(length+1).join(' ');
}

function ensureArray(arg) {
    var array = arg || [];
    
    if (array && !(array instanceof Array)) {
        array = [array];
    }
    
    return array;
}

function showHelp() {
    var paramTemplate = _.template('<%= margin %><%= name %><%= alignMargin %><%= description %>');
    var exampleTemplate = _.template("<%= margin %><%= cmd %>\n<%= margin %><%= margin %><%= description %>\n");
    var columnLength = 15;
    var marginLength = 4;

    var params = {
        help: 'Эта помощь',
        list: 'Список модулей и групп модулей',
        group: 'Группа модулей для выполнения (можно использовать несколько раз)',
        module: 'Конкретный модуль для выполнения (можно использовать несколько раз)',
        all: 'Запускать все тесты, даже если они отключены для запуска по-умолчанию (серые в --list)',
        // temporary disabled till CHET-199 will be closed
        //parallel: 'Запускать модули параллельно (по-умолчанию используется последовательный запуск)',
        vagrant: 'Запускать модули в виртуальной машине (по умолчанию используется локальный запуск)',
        moduleArgs: 'Cтрока дополнительных параметров для запуска модуля с именем module (например --calcapiArgs=\'--arg1="val1" --arg2="val2"\')'

    };

    var examples = {
        'npm run test': 'Последовательно запустить все доступные модули',
        'npm run test -- --list': 'Покажет список доступных модулей и групп модулей',
        'npm run test -- --group=calc --group=api': 'Запустить модуль из групп calc и api',
        'npm run test -- --module=phpunit': 'Запустить только модуль phpunit',
        'npm run test -- --group=calc --module=phpunit': 'Запусить группу calc и модуль phpunit',
        // temporary disabled till CHET-199 will be closed
        //'npm run test -- --group=calc --all --parallel': 'Параллельно запустить все модули из группы calc, включая отключенные по-умолчанию',
        'npm run test -- --vagrant': 'Параллельно запустить все доступные модули в виртуалке',
        'npm run test -- --module=calcserver --calcserverArgs=\'--company="alfa"\'' : 'Запусить модуль calcserver с параметром --company="alfa"'
    };

    log(colors.underline('Помощь по использованию комманды'));
    log('Использование: npm run test [параметры]'+"\n");
    log(colors.underline('Доступные параметры:'));

    Object.keys(params).forEach(function (param) {
        log(paramTemplate({
            margin: padString(marginLength),
            alignMargin: padString(columnLength - marginLength - param.length),
            name: colors.cyan(param),
            description: params[param]
        }));
    });

    log("");
    log(colors.underline('Примеры использования:'));
    Object.keys(examples).forEach(function (cmd) {
        log(exampleTemplate({
            margin: padString(marginLength),
            cmd: colors.cyan(cmd),
            description: examples[cmd]
        }));
    });
}

function showModulesList() {
    var moduleDescriptionTemplate = _.template(
        "<%= margin %><%= name %><%= alignMargin %><%= description %>\n"+
        "<%= columnMargin %>(<%= cmd %>)"
    );
    var moduleGroupTemplate = _.template('<%= margin %><%=tag%>: <%= tests %>');
    var testGroups = {};
    var columnLength = 24;
    var marginLength = 4;

    log(colors.underline('Список доступных тестов')+"\n");

    modules = loadAllTestModules();
    Object.keys(modules).sort().forEach(function (moduleName) {
        var module = modules[moduleName];

        log(moduleDescriptionTemplate({
            margin: padString(marginLength),
            alignMargin: padString(columnLength - marginLength - moduleName.length),
            columnMargin: padString(columnLength),
            name: colors.cyan(moduleName),
            description: module.description,
            cmd: module.cmd || '-'
        }));

        module.tags.forEach(function (tag) {
            if (typeof testGroups[tag] == 'undefined') {
                testGroups[tag] = [];
            }

            testGroups[tag].push(module.skipDefault
                ? colors.gray(moduleName+'*')
                : moduleName);
        });
    });

    log("\n"+colors.underline('Тесты по группам')+"\n(Серым и * отмечены тесты, которые будут" +
        " запускаться только, если явно указаны параметром --test или если указан параметр --all)\n");
    Object.keys(testGroups).sort().forEach(function (groupTag) {
        log(moduleGroupTemplate({
            margin: padString(marginLength),
            tag: colors.cyan(groupTag),
            tests: testGroups[groupTag].join(', ')
        }));
    });

    log("");
}

var testGroupsToRun = ensureArray(args.group);
var testsToRun = ensureArray(args.module);

var modules;

if (args.help) {
    showHelp();
    return;
}

if (args.list) {
    showModulesList();
    return;
}

if (testGroupsToRun.length > 0) {
    timestampLog('Группы модулей для запуска: ', testGroupsToRun);
}

if (testsToRun.length > 0) {
    timestampLog('Модули для запуска: ', testsToRun);
}

modules = loadTestModules(testGroupsToRun, testsToRun, args.all);
var moduleNames = Object.keys(modules);
var reporter = new DefaultReporter();
var parallelModuleRun = false;

// temporary disabled till CHET-199 will be closed
/* 
  if (args.parallel && modulesCount > 1) {
    parallelModuleRun = true;
    reporter.enableParallelMode();
    timestampLog('Включен параллельный запуск модулей');
}
*/

timestampLog('Будут выполнены следующие модули: ', moduleNames);

timestampLog('Начинаю тестирование...');
timestampLog('-----------------------');

var runner = new Runner(modules, reporter);
runner.run(parallelModuleRun);

process.on('SIGINT', function() {
    timestampLog("SIGINT: Завершение работы тестов..");

    runner.gracefulShutdown();
    process.exit();
});
