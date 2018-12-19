const clone = require('lodash').clone;
const log = require('fancy-log');
const fs = require('fs');
const fsextra = require('fs-extra');
const path = require('path');
const glob = require('glob');
const async = require('async');
const config = require('../config.json');
const args = require('yargs').argv;

module.exports = function (_modules, _reporter) {
    var modules = _modules;
    var reporter = _reporter;
    var tests = {};
    var callbacks = {};
    var finishedModules = [];
    var statusNames = ['success', 'failed', 'error', 'skipped', 'expectedfail'];

    return {
        run: function (parallelRun) {
            var runner = this;
            var tasks = [];
            parallelRun = typeof parallelRun == 'boolean' ? parallelRun : true;

            Object.keys(modules).forEach(function (moduleName) {
                var module = modules[moduleName];
                var task = function (callback) {
                    var cmdArgsString;
                    callbacks[moduleName] = callback;
                    module.init(null, runner);
                    var moduleArgsArgumentName = moduleName.toLowerCase()+'Args';
                    if (args[moduleArgsArgumentName]) {
                        cmdArgsString = " -- "+args[moduleArgsArgumentName];
                        module.setArgs(cmdArgsString);
                    }
                    module.run();
                };

                tasks.push(task);
            });

            if (parallelRun) {
                async.parallel(tasks);
            }
            else {
                async.series(tasks);
            }
        },

        addTest: function (levelsDown, levelsUp, testContainer, skipReport) {
            var addedTest = false;
            
            if ( !(levelsDown instanceof Array) ) {
                levelsDown = [levelsDown];
            }
            else {
                levelsDown = clone(levelsDown);
            }

            if (!testContainer) {
                testContainer = tests;
            }

            if (!levelsUp) {
                levelsUp = [];
            }

            var level = levelsDown.shift();
            var notLastLevel = levelsDown.length > 0;
            levelsUp.push(level);

            if (typeof testContainer[level] == 'undefined') {
                testContainer[level] = {
                    children: {},
                    successful: false,
                    failed: false,
                    error: false,
                    expectedfail: false,
                    skipped: false,
                    finished: false,
                    message: false
                };
                
                addedTest = testContainer[level];

                if (!skipReport) {
                    reporter.testStart(levelsUp);
                }
            }

            if (notLastLevel) {
                addedTest = this.addTest(levelsDown, levelsUp, testContainer[level].children, skipReport);
            }
            
            return addedTest;
        },

        findTest: function (levels) {
            levels = clone(levels);
            var firstLevel = levels.shift();
            var test = tests[firstLevel] || false;

            if (test) {
                levels.forEach(function (level) {
                    test = test.children[level];
                });
            }

            return test;
        },
        
        findOrAddTest: function (levels) {
            var test = this.findTest(levels);

            if (!test) {
                var skipReport = true;
                test = this.addTest(levels, false, false, skipReport);
            }
            
            return test;
        },

        finishTestRecursive: function (levels, status) {
            levels = clone(levels);
            var module = this;
            var test = this.findTest(levels);
            var testStats = this.getTestStats(test);
            var testHasNoStatus = testStats.total == 0;

            if (test) {
                Object.keys(test.children).forEach(function (subtest) {
                    var sublevels = clone(levels);

                    sublevels.push(subtest);
                    module.finishTestRecursive(sublevels, status);
                });

                if (!test.finished) {
                    if (status && testHasNoStatus) {
                        test[status] = true;
                    }
                    
                    var stats = this.getTestStatsRecursive(levels);
                    test.finished = true;
                    
                    reporter.testFinish(levels, stats, test.message);
                }
            }
        },
        
        getTestStats: function (test) {
            var stats = {
                success: 0,
                failed: 0,
                expectedfail: 0,
                error: 0,
                skipped: 0,
                total: 0
            };

            statusNames.forEach(function (status) {
                if (test[status]) {
                    stats[status]++;
                    stats.total++;
                }
            });
            
            return stats;
        },
        
        getTestStatsRecursive: function (levels) {
            levels = clone(levels);
            var module = this;
            var test = this.findTest(levels);
            var stats = this.getTestStats(test);
            var totalChildrenStats = {};

            if (test.children) {
                Object.keys(test.children).forEach(function (subtest) {
                    var sublevels = clone(levels);
                    sublevels.push(subtest);
                    var childStats = module.getTestStatsRecursive(sublevels);

                    statusNames.forEach(function (status) {
                        if (typeof totalChildrenStats[status] == 'undefined') {
                            totalChildrenStats[status] = 0;
                        }

                        if (childStats[status]) {
                            stats[status]+=childStats[status];
                            totalChildrenStats[status]+=childStats[status];
                            stats.total+=childStats[status];
                        }
                    });
                });
            }

            //Если есть дочерние тесты в каком-то статусе, то этот статус может быть продублирован в родительском
            //тесте (когда, например, модуль сначала сообщает об успехе дочерней проверки и потом, как следствие, об
            //успехе родительского теста). В этом случае, этот статус родительского теста не надо учитывать в
            //статистике, нужно учитывать только самостоятельные статусы дочерних проверок.
            statusNames.forEach(function (status) {
                if (totalChildrenStats[status] > 0 && stats[status] > totalChildrenStats[status]) {
                    stats[status] = totalChildrenStats[status];
                }
            });

            return stats;
        },

        getTestLevels: function (test, module) {
            var levels = test && test.name ? clone(test.name) : module.getLevel();
            levels.unshift(module.getModuleName());
            
            return levels;
        },
        
        checkAllModulesFinished: function () {
            var result = true;

            Object.keys(modules).forEach(function (moduleName) {
                var isModuleFinished = tests[moduleName] && tests[moduleName].finished;
                result = result && isModuleFinished;
            });

            return result;
        },
        
        reportTestMessageRecursive: function (levels) {
            levels = clone(levels);
            var module = this;
            var test = this.findTest(levels);

            if (test) {
                Object.keys(test.children).forEach(function (subtest) {
                    var sublevels = clone(levels);

                    sublevels.push(subtest);
                    module.reportTestMessageRecursive(sublevels);
                });

                if (typeof test.message == 'string' && test.message.indexOf('exitcode') == -1) {
                    reporter.testMessage(levels, test, this.getTestStats(test));
                }
            }
        },
        
        onStart: function (test, module) {
            var levels = this.getTestLevels(test, module);
            this.addTest(levels);
        },

        onFinish: function (result, module) {
            var levels = this.getTestLevels(result, module);
            var test = this.findOrAddTest(levels);
            var hasExitcode = typeof(result.exitcode) != 'undefined';
            var isModuleFinished = hasExitcode || levels.length == 1;
            var status = result && result.status ? result.status : false;

            if (result && result.message) {
                test.message = result.message;
            }
            
            if (hasExitcode) {
                var exitCodeMessage = 'exitcode='+result.exitcode
                test.message = test.message
                    ? test.message+' ('+exitCodeMessage+')'
                    : exitCodeMessage;
            }

            this.finishTestRecursive(levels, status);
            if (isModuleFinished) {
                this.onModuleFinish(module);
            }
        },

        onDebug: function (result, module) {
            var levels = this.getTestLevels(result, module);
            var test = this.findOrAddTest(levels);

            if (result && result.message) {
                test.message = result.message;
            }
        },

        copyArtifacts: function (module) {
            var paths = module.artifacts instanceof Array
                ? module.artifacts
                : [module.artifacts];

            var slashedPath = config.artifactsPath;
            if (slashedPath.slice(-1) != '/') {
                slashedPath += '/';
            }

            var dstDirPath = slashedPath+module.name+'/';
            fsextra.ensureDirSync(dstDirPath);

            paths.forEach(function (srcPath) {
                var dstPath = dstDirPath;

                var isGlob = srcPath.match(/[\!\*\?\(\)\[\]\{\}]+/) != undefined;

                if (isGlob) {
                    glob(srcPath, function (error, files) {
                        if (error)
                            return false;

                        files.forEach(function (srcFile) {
                            var fileName = path.basename(srcFile);
                            try {
                                fsextra.copySync(srcFile, dstDirPath + fileName);
                            }
                            catch(error) {
                                log("[!] При копировании файла '" + srcFile.toString() + "' в '" +
                                     dstDirPath.toString() + "' во время исполнения '" +
                                     module.name.toString() + "' возникла ошибка: " +
                                     error.toString() );
                            }
                        });
                    });
                }
                else {
                    try {
                        var dstInfo = fs.statSync(srcPath);
                        if (dstInfo.isFile()) {
                            var fileName = path.basename(srcPath);
                            dstPath += fileName;
                        }

                        fsextra.copySync(srcPath, dstPath);
                    }
                    catch (error) {
                        log("[!] При копировании файла '" + srcPath.toString() + "' в '" +
                             dstDirPath.toString() + "' во время исполнения '" +
                             module.name.toString() + "' возникла ошибка: " +
                             error.toString()   );
                    }
                }
            });
        },
        
        onModuleFinish: function (module) {
            var moduleName = module.name;
            var asyncFinishCallback = callbacks[moduleName];
            var isFinished = finishedModules.indexOf(moduleName) != -1;
            var hasArtifacts = module.artifacts != undefined && module.artifacts != false;
            var logFile = config.reportPath+moduleName + ".debug.log";
            try {
                fs.writeFileSync(logFile, module.getFullLog());
            }
            catch(error) {
                log("[!] Ошибка записи в лог файл '" + logFile + "' при завершении работы модуля '" +
                     module.name.toString() + "' :" + error.toString());
            }

            if (hasArtifacts) {
                this.copyArtifacts(module);
            }

            if (!isFinished) {
                finishedModules.push(moduleName);
                reporter.moduleFinished(module);

                if (typeof asyncFinishCallback == 'function') {
                    asyncFinishCallback();
                }

                if (this.checkAllModulesFinished()) {
                    this.onAllModulesFinish();
                }
            }
        },

        onAllModulesFinish: function () {
            var totalStats = {};
            var runner = this;

            Object.keys(tests).forEach(function (moduleName) {
                var stats = runner.getTestStatsRecursive([moduleName]);

                statusNames.forEach(function (status) {
                    if (typeof totalStats[status] == 'undefined') {
                        totalStats[status] = 0;
                    }

                    totalStats[status] += stats[status];
                });

                runner.reportTestMessageRecursive([moduleName]);
            });

            reporter.allFinished(modules, totalStats);
        },

        gracefulShutdown: function () {
            var runner = this;
            Object.keys(modules).forEach(function (moduleName) {
                var module = modules[moduleName];
                runner.onModuleFinish(module);
            });
            runner.onAllModulesFinish();
        }
    }
};
