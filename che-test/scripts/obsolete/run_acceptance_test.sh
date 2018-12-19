#!/bin/bash

# import common functions and variables
if [ -r ./common_test_env.sh ]; then
    . common_test_env.sh
else
    echo -e "No ./common_test_env.sh in `pwd`. Check if the environment deployed correctly?"
    exit 253
fi

# display number to create with Xvfb
DISPLAY_NUM=12
# test name used in file names
testname="test_acceptance_vzr.py"
# directory to run the test
rundir=${deploybase}/che-test/scripts/autotests
# prefix to construct $logfile
logfileprefix="acceptance_vzr"
# log name w/o path
logfile="${logfileprefix}.${testname}.${logdatetime}.${logfilesuffix}"
# имя лога куда перенаправлять вывод команд подготавливающих запуск тестов
prepare_log_prefix="prepare"
prepare_log="/tmp/${prepare_log_prefix}.${testname}.${logdatetime}.${logfilesuffix}"
# make the commands that prepare environment to be silent, alternative is being kept for parametrized usage
outputredirect=" 2>&1 3>&1 |tee -a ${prepare_log}"
#outputredirect=" 1>/dev/null 2>&1 |tee -a ${prepare_log}"
# html log name w/o path
html_log_prefix=${logfileprefix}
htmllogfile=${html_log_prefix}.${testname}.${logdatetime}.$htmllogfilesuffix
# xml logs
origxmllog="nosetests.${xmllogfilesuffix}"
xmllog="nosetests.${testname}.${logdatetime}.${xmllogfilesuffix}"
# list of commands used w/ sudo, space separated (always include "mkdir chown chmod" as its used by common_test_env.sh)
sudo_cmds="Xvfb mkdir chown chmod"
# space separated list of external apss required in $PATH by this script, its includes or by executables it starts
dependencies="sudo tee pwd id which basename grep ps wc Xvfb sleep firefox python nosetests google-chrome"

### start here
# repeat import to renew function definitions: outputredirect and some other variables used there were modified above between imports
. common_test_env.sh

# global vars check
check_vars
# local vars check
for var in "${rundir}" "${prepare_log}" "${logfile}" "${htmllogfile}" "${testname}"  "${DISPLAY_NUM}" ; do
    if [ -z "$var" ]; then
        eval "echo \"`basename ${0}`: configuration error. One of requred variables is not set:\"" $outputredirect
        eval "echo \"     \\\$rundir \\\$prepare_log \\\$logfile \\\$htmllogfile \\\$testname \\\$DISPLAY_NUM \"" $outputredirect
        eval "echo \"Abort.\"" $outputredirect
        exit 1
    fi
done

check_deps $dependencies
check_sudo_access $sudo_cmds
prepare_dirs "${rundir}" "${logdir}" "${OldLogsMoveTo}"
check_logs_writable ${rundir}/$logfile ${rundir}/$htmllogfile $prepare_log
logfiles="${logfileprefix}*.$logfilesuffix ${prepare_log_prefix}*.$logfilesuffix geckodriver*.$logfilesuffix firefox*.$logfilesuffix ${html_log_prefix}*.${htmllogfilesuffix} nosetests*.${xmllogfilesuffix}"
# if any left earlier in $rundir - remove
remove_files_from_rundir $logfiles
# cleanup $OldLogsMoveTo from too old
remove_too_old_logs $logfiles
# move not too old left to $OldLogsMoveTo
move_old_logs $logfiles
cd $rundir
start_Xvfb
check_is_deployed_and_make_executable ${rundir}/${testname}

eval "echo \"  Starting $acceptancetest test.. \"" $outputredirect
DISPLAY=:$DISPLAY_NUM GST_GL_XINITTHREADS=1 unbuffer ${rundir}/${testname} --nocapture --with-xunit 2>&1 3>&1 | tee -a ${rundir}/$logfile
test_retc=${PIPESTATUS[0]}
eval "echo \"acceptance vzr exit code:  ${test_retc}\""

if [ -r ./$origxmllog ]; then
  eval "cp -f ./$origxmllog ${rundir}/${xmllog}" $outputredirect
  eval "mv -f ./$origxmllog ${xmllog}" $outputredirect
else
  eval "echo -e \"\033[1;33mNo ./$origxmllog found, log file processing is skipped\033[0m\""
fi
rename_logs_by_format
# we keep last copy in $rundir for these: $logfile $htmllogfile $prepare_log
eval "cp $prepare_log $rundir" $outputredirect
copy_logs_to_logdir $prepare_log ${rundir}/$htmllogfile ${rundir}/$logfile $logfiles
exit $test_retc
