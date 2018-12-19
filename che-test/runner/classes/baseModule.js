const clone = require('lodash').clone;

module.exports = function () {
    var callbacks;
    var context;
    var currentHierarchy = [];
    var runner;
    var finished;

    return {
        name: 'baseModule',
        tags: [],
        description: 'Описание не указано',
        skipDefault: false,
        /**
         * @property artifacts
         * Может быть строкой с путем к папке или файлу (желательно относительным, чтобы работало везде, а не только в
         * vagrante). Может быть массивом с несколькими путями. Может быть массивом с glo
         */
        artifacts: false,

        init: function (_context, _runner) {
            context = _context || null;
            callbacks = [];
            runner = _runner;
            finished = false;
        },

        getModuleName: function () {
            return this.name;
        },

        setArgs: function(cmdLineArgs) {
            this.cmd = this.cmd + ' ' + cmdLineArgs;
        },

        levelDown: function (levelName) {
            currentHierarchy.push(levelName);
        },

        levelUp: function () {
            return currentHierarchy.pop();
        },
        
        setLevel: function (levels) {
            currentHierarchy = clone(levels);
        },
        
        getLevel: function () {
            return clone(currentHierarchy);
        },
        
        addCurrentLevelTo: function (level) {
            var currentLevel = this.getLevel();
            currentLevel.push(level);
            
            return currentLevel;
        },
        
        start: function (test) {
            if (test && test.name) {
                this.setLevel(test.name);
            }
            else if (typeof test == "string") {
                this.levelDown(test);
            }
            
            runner.onStart(test, this);
        },
        
        finish: function (test) {
            runner.onFinish(test, this);
        },
        
        finishModule: function (test) {
            if (test) {
                test.name = [];
            }
            else {
                test = {name: []};
            }

            if (!finished) {
                finished = true;
                runner.onFinish(test, this);
            }
        },
        
        debug: function (test) {
            runner.onDebug(test, this);
        }
    };
};
