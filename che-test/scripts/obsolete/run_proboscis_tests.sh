#!/bin/bash
#
# скрипт для запуска автотестов с использованием proboscis .
#
# параметр (если есть) - список
#
#

# import common functions & variables
if [ -r ./common_test_env.sh ]; then
 . ../../common_test_env.sh
else
  echo -e "No ./common_test_env.sh in `pwd` . Is env deployed correctly? Abort."
  exit 253
fi

### variables
# display number to create with Xvfb
DISPLAY_NUM=6

# set $testname depending to params 
case "${1}" in
   "") 
      testname="proboscis-run-all"
      ;;
   "--list-tests")
      testname="proboscis-list-tests"
      ;;
    *)
      testname="proboscis-parametrized"
esac
# do not edit below if unsure
rundir=${deploybase}/che-test/scripts/autotests
# prefix to construct $logfile 
logfileprefix="proboscis"
# log name w/o path, on format change - replace accordingly in common_test_env.sh in rename_logs_by_format() function
logfile="${logfileprefix}.${testname}.${logdatetime}.${logfilesuffix}"
# начало имени лога куда перенаправлять вывод команд подготавливающих запуск тестов
prepare_log_prefix="prepare"
prepare_log="/tmp/${prepare_log_prefix}.${testname}.${logdatetime}.${logfilesuffix}"
# make the commands that prepare environment to be silent, alternative is being kept for parametrized usage
#outputredirect=" 2>&1 3>&1 |tee -a ${prepare_log}"
outputredirect=" 1>/dev/null 2>&1 |tee -a ${prepare_log}"
# html log name w/o path, on format change - replace accordingly in common_test_env.sh in rename_logs_by_format() function
html_log_prefix=$logfileprefix
htmllogfile=${html_log_prefix}.${testname}.${logdatetime}.$htmllogfilesuffix
# xml logs
origxmllog="nosetests.xml"
xmllog=nosetests.${testname}.${logdatetime}.$xmllogfilesuffix
# list of commands used w/ sudo, space separated (always include "mkdir chown chmod" as its used by common_test_env.sh)
sudo_cmds="Xvfb mkdir chown chmod"
# space separated list of external apss required in $PATH by this script, its includes or by executables it starts
dependencies="sudo tee pwd id which basename grep ps wc Xvfb sleep firefox python nosetests unbuffer"
export DISPLAY=:$DISPLAY_NUM
export GST_GL_XINITTHREADS=1

### start here
# repeat import to renew function definitions: outputredirect & some other variables used there were modified above between imports
. ../../common_test_env.sh

# global vars check
check_vars
# local vars check
for var in "${rundir}" "${prepare_log}" "${logfile}" "${htmllogfile}" "${testname}" "${DISPLAY_NUM}" ; do
 if [ -z "${var}" ]; then
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
logfiles="${logfileprefix}*.$logfilesuffix ${prepare_log_prefix}*.$logfilesuffix geckodriver*.$logfilesuffix firefox*.$logfilesuffix ${html_log_prefix}*.${htmllogfilesuffix} nosetests*.${xmllogfilesuffix} dredd-tests*.${xmllogfilesuffix}"
# if any left earlier in $rundir - remove
remove_files_from_rundir $logfiles 
# cleanup $OldLogsMoveTo from too old
remove_too_old_logs $logfiles 
# move not too old left to $OldLogsMoveTo
move_old_logs $logfiles
cd $rundir
start_Xvfb
eval "echo \"  Starting tests with proboscis.. \"" $outputredirect
# set execution string depending to script params
case "${1}" in
   "")
      eval "echo \"        running: './run_tests_with_proboscis.py --nocapture --with-xunit '\"" $outputredirect
      DISPLAY=:$DISPLAY_NUM unbuffer ./run_tests_with_proboscis.py --nocapture --with-xunit 2>&1 3>&1 | tee -a ${rundir}/$logfile
      proboscis_retc=${PIPESTATUS[0]}
      ;;
   "--run-inside-npm-test")
      DISPLAY=:$DISPLAY_NUM unbuffer ./run_tests_with_proboscis.py --nocapture --with-xunit| tee -a ${rundir}/$logfile
      proboscis_retc=${PIPESTATUS[0]}
      ;;
   "--list-tests")
      eval "echo \"        running: './run_tests_with_proboscis.py --nocapture --with-xunit --show-plan'\"" $outputredirect
      DISPLAY=:$DISPLAY_NUM unbuffer ./run_tests_with_proboscis.py --nocapture --with-xunit --show-plan 2>&1 3>&1 | tee -a ${rundir}/$logfile
      proboscis_retc=${PIPESTATUS[0]}
      ;;
    *)
      echo "Trying to execute only tests matching groups: ${@}"
      # html option is not compatible w/ russian comments
      DISPLAY=:$DISPLAY_NUM unbuffer ./run_tests_with_proboscis.py --nocapture --with-xunit --group=$@ 2>&1 3>&1 | tee -a ${rundir}/$logfile
      proboscis_retc=${PIPESTATUS[0]}
esac

eval "echo \"proboscis exit code:  ${proboscis_retc}\"" $outputredirect
if [ -r ./$origxmllog ]; then
    eval "cp -f ./$origxmllog ${rundir}/${xmllog}" $outputredirect
    eval "mv -f ./$origxmllog ${xmllog}" $outputredirect
    rename_logs_by_format
    # we keep last copy in $rundir for these: $logfile $htmllogfile $prepare_log
    eval "cp $prepare_log $rundir" $outputredirect
    copy_logs_to_logdir $prepare_log ${rundir}/$htmllogfile ${rundir}/$xmllog  ${rundir}/$logfile $logfiles
else
    eval "echo -e \"\033[1;33mNo ./$origxmllog found, log file processing is skipped\033[0m\""
fi
exit $proboscis_retc
