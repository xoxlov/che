const shellModule = require('../../classes/shellModule');
const extend = require('lodash').assign;

module.exports = function () {
    var currentAction = false;
    var taskTypes = {
        'Выписка полисов по Payture с неуспешной оплатой': 'createPaytureUnpaid',
        'Создание полисов по Payture': 'createPayture',
        'Создание полисов по Wire': 'createWire',
        'Проверяем отмененные полисы': 'cancelCheck',
        'Изменяем полисы': 'update',
        'Отменяем полисы': 'cancel'
    };
    var multistepActions = Object.keys(taskTypes);
    var currentTaskType = false;
    var fullLog = '';
    var tasks = {
        createPaytureUnpaid: [],
        createPayture: [],
        createWire: [],
        cancelCheck: [],
        update: [],
        cancel: []
    };

    return extend(new shellModule, {
        name: 'policy',
        tags: ['api'],
        description: 'Проверяет выписку полисов всех страховых компаний через API',
        cmd: 'cd /var/www/che-partner/public_html/app/tests && php ApiCreateCancelPolicy.php',
        //cmd: 'cat /var/www/che-test/runner/reports/policy.debug.log',
        artifacts: ['../../che-partner/public_html/app/storage/logs/laravel.log'],
    
        stripTimestampAndSymbols: function(str) {
            return str.replace(/^[0-9\.\: \-]+/, '');
        },
    
        failIncompleteTasks: function() {
            var incompleteTasks = this.findAllTasks({field: 'complete', value: false});
            var module = this;

            incompleteTasks.forEach(function (incompleteTask) {
                var errors = [];
                if (!incompleteTask.policyProcessed) {
                    errors.push('нет отметки о создании полиса');
                }

                if (!incompleteTask.taskProcessed) {
                    errors.push('нет отметки о завершении задачи');
                }

                var errorMessage = errors.length > 0
                    ? errors.join(', ')
                    : 'неизвестная ошибка';

                module.finish({
                    name: module.addCurrentLevelTo(incompleteTask.insuranceCode),
                    status: 'failed',
                    message: errorMessage
                });
            });
        },
    
        finishTest: function(action) {
            if (!action.isOneStep) {
                this.failIncompleteTasks();
            }
    
            var level = action.isOneStep
                ? this.addCurrentLevelTo(action.actionName)
                : this.getLevel();
            
            this.finish({
                name: level,
                status: 'success'
            });
        },
    
        processTaskStatus: function(task, message) {
            var taskNeeded = task.taskProcessed != undefined && task.taskId != undefined;

            if (taskNeeded) {
                task.complete = task.policyProcessed && task.taskProcessed;
            }
            else {
                task.complete = task.policyProcessed;
            }
    
            if (task.complete) {
                var result = {
                    name: this.addCurrentLevelTo(task.insuranceCode),
                    status: 'success'
                };
                
                if (message) {
                    result.message = message;
                }

                this.finish(result);
            }
        },
    
        findAllTasks: function(query) {
            var type = query.type || currentTaskType;
            var tasksOfType = tasks[type];
            var result = [];
    
            tasksOfType.forEach(function (task) {
                if (task[query.field] == query.value) {
                    result.push(task);
                }
            });
    
            return result;
        },
    
        findTask: function(query) {
            var allTasks = this.findAllTasks(query);
            return allTasks.length > 0 ? allTasks[0] : false;
        },
    
        processOutputRecord: function(logRecord) {
            var task;
            logRecord = this.stripTimestampAndSymbols(logRecord);
    
            var parse = {
                newStep: logRecord.match(/(.*?)\.\.\.$/),
                taskNewCreate: logRecord.match(/^.*?Создана задача ([a-z0-9\-]+) на создание полиса ([a-zA-Z_\-]+)$/),
                taskUpdateCreate: logRecord.match(/^.*?Создана задача ([a-z0-9\-]+) на изменение полиса ([a-zA-Z_\-]+) ([0-9]+)$/),
                taskCancelCreate: logRecord.match(/^.*?Создана задача ([a-z0-9\-]+) на отмену полиса ([a-zA-Z_\-]+) ([0-9]+)$/),

                policyCreated: logRecord.match(/^.*?Полис ([a-zA-Z_\-]+) ([0-9]+) создан$/),
                policyStopped: logRecord.match(/^.*?Полис ([a-zA-Z_\-]+) ([0-9]+) завис$/),
                policyUpdated: logRecord.match(/^.*?Полис ([a-zA-Z_\-]+) ([0-9]+) изменён$/),
                policyCanceled: logRecord.match(/^.*?Полис ([a-zA-Z_\-]+) ([0-9]+) отменён/),
                policyWasCanceled: logRecord.match(/^.*?Полис ([a-zA-Z_\-]+) ([0-9]+) уже отменён$/),
    
                taskSuccess: logRecord.match(/^.*?Задача ([a-z0-9\-]+) исключена из очереди$/),
                taskFailed: logRecord.match(/^.*?Задача ([a-z0-9\-]+) исключена из очереди в статусе неуспех$/),
                error: logRecord.match(/^(.*?) error:(.*?)$/)
            };
    
            if (parse.newStep) {
                var action = parse.newStep[1];
                var notWaiting = action != 'А теперь ждем результата';
    
                if (notWaiting) {
                    if (currentAction) {
                        this.finishTest(currentAction);
                    }
    
                    if (taskTypes[action] != undefined) {
                        currentTaskType = taskTypes[action];
                    }
    
                    currentAction = {
                        actionName: action,
                        isOneStep: multistepActions.indexOf(action) == -1
                    };
    
                    if (!currentAction.isOneStep) {
                        this.start({
                            name: [action]
                        });
                    }
                }
            }
    
            if (parse.taskNewCreate) {
                tasks[currentTaskType].push({
                    taskId: parse.taskNewCreate[1],
                    policyId: false,
                    insuranceCode: parse.taskNewCreate[2],
                    policyProcessed: false,
                    taskProcessed: false,
                    complete: false
                });
            }
    
            if (parse.taskUpdateCreate) {
                tasks.update.push({
                    taskId: parse.taskUpdateCreate[1],
                    policyId: parseInt(parse.taskUpdateCreate[3]),
                    insuranceCode: parse.taskUpdateCreate[2],
                    policyProcessed: false,
                    taskProcessed: false,
                    complete: false
                });

                tasks.cancelCheck.push({
                    policyId: parseInt(parse.taskUpdateCreate[3]),
                    insuranceCode: parse.taskUpdateCreate[2],
                    policyProcessed: false,
                    complete: false
                });
            }
            
            if (parse.taskCancelCreate) {
                tasks.cancel.push({
                    taskId: parse.taskCancelCreate[1],
                    policyId: parseInt(parse.taskCancelCreate[3]),
                    insuranceCode: parse.taskCancelCreate[2],
                    policyProcessed: false,
                    taskProcessed: false,
                    complete: false
                });
            }
    
            if (parse.policyCreated) {
                task = this.findTask({type: 'createPayture', field: 'insuranceCode', value: parse.policyCreated[1]});
                task.policyId = parseInt(parse.policyCreated[2]);
                task.policyProcessed = true;
                this.processTaskStatus(task);
            }

            if (parse.policyStopped) {
                task = this.findTask({type: 'createPaytureUnpaid', field: 'insuranceCode', value: parse.policyStopped[1]});
                task.policyId = parseInt(parse.policyStopped[2]);
                task.policyProcessed = true;
                this.processTaskStatus(task);
            }

            if (parse.policyUpdated) {
                task = this.findTask({type: 'update', field: 'policyId', value: parseInt(parse.policyUpdated[2])});
                if (task) {
                    task.policyProcessed = true;
                    this.processTaskStatus(task);
                }
            }

            if (parse.policyWasCanceled) {
                var policyId = parseInt(parse.policyWasCanceled[2]);
                task = this.findTask({type: 'cancelCheck', field: 'policyId', value: policyId});
                if (task) {
                    task.policyProcessed = true;
                    this.processTaskStatus(task);
                }
            }

            if (parse.policyCanceled) {
                var policyId = parseInt(parse.policyCanceled[2]);
                
                task = this.findTask({type: 'cancel', field: 'policyId', value: policyId});
                if (task) {
                    task.policyProcessed = true;
                    this.processTaskStatus(task);
                }
            }

            if (parse.taskSuccess) {
                task = this.findTask({field: 'taskId', value: parse.taskSuccess[1]});
                task.taskProcessed = true;
    
                this.processTaskStatus(task);
            }
    
            if (parse.taskFailed) {
                task = this.findTask({field: 'taskId', value: parse.taskFailed[1]});
    
                this.finish({
                    name: this.addCurrentLevelTo(task.insuranceCode),
                    status: 'failed',
                    message: logRecord
                });
            }

            if (parse.error) {
                var actionName = parse.error[1];
                var errorMessage = parse.error[2];

                this.finish({
                    name: this.addCurrentLevelTo(actionName),
                    status: 'failed',
                    message: errorMessage
                });
            }
        },
    
        processOutput: function (stdoutBuffer) {
            var stdout = stdoutBuffer.toString();
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