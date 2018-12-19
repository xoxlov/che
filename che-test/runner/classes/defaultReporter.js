const log = require('fancy-log');
const clone = require('lodash').clone;

module.exports = function () {
    var printModuleName = false;

    return {
        enableParallelMode: function () {
            printModuleName = true;
        },

        getPrintModuleName: function (levels) {
            return (printModuleName ? '['+levels[0]+'] ' : '');
        },

        getStatusChar: function (stats) {
            var statusChar = '?';
            if (stats.success > 0) {
                statusChar = '+';
            }

            if (stats.failed > 0) {
                statusChar = '-';
            }

            if (stats.error > 0) {
                statusChar = '!';
            }

            if (stats.expectedfail > 0) {
                statusChar = '#';
            }

            return statusChar;
        },

        getStatsInfo: function (stats) {
            return '('+stats.success+'/'+stats.failed+'/'+stats.expectedfail+'/'+stats.error+')';
        },

        generatePadString: function (length) {
            return new Array(length).join('   ')
        },

        generateLevelDescription: function (levels) {
            levels = clone(levels);
            var levelMsgSplit = null;
            var levelNames = ['Модуль', 'Тест', 'Проверка', 'Утверждение', 'Уровень'];
            var levelNameIndex = levels.length <= levelNames.length
                ? levels.length-1
                : levelNames.length-1;

            var level = levels.pop();
            var levelName = levelNames[levelNameIndex];
            if ( typeof(level) == 'string' ) {
                levelMsgSplit = level.match(/^(\[\d+\/\d+\]) (.*)$/)
            }
            if (levelMsgSplit != null ) {
                return levelName+' '+levelMsgSplit[1] + ' "'+levelMsgSplit[2]+'"';
            }
            else {
                return levelName+' "'+level+'"';
            }
        },

        testStart: function (levels) {
            log( this.getPrintModuleName(levels)+this.generatePadString(levels.length)+'[>] '+this.generateLevelDescription(levels) );
        },

        testFinish: function (levels, stats, message) {
            var statusChar = this.getStatusChar(stats);
            var statsInfo = this.getStatsInfo(stats);
            var testInfo;

            testInfo = this.getPrintModuleName(levels);
            testInfo += this.generatePadString(levels.length)+'['+statusChar+'] '+this.generateLevelDescription(levels);
            if (message) {
                testInfo += ': '+message;
            }
            testInfo += ' '+statsInfo;

            log(testInfo);
        },

        testMessage: function (levels, test, stats) {
            log('['+this.getStatusChar(stats)+'] '+levels.join('->')+': '+test.message);
        },

        moduleFinished: function (module) {
            log(this.getPrintModuleName([module.name])+'-----------------------');
        },

        allFinished: function (modules, stats) {
            log('Выполнение закончено '+this.getStatsInfo(stats));
            log('-----------------------');
        }
    }
};
