#!/bin/bash
#
# тут общие переменные и функции используемые *.sh скриптами из $deploybase/che-test/scripts (всем кроме run_deploy_checks.sh)
#
# внимание: этот файл НЕ используется из run_deploy_checks.sh, его надо конфигурировать отдельно

#### common vars
# deployment root
deploybase=/var/www
#log file name modifier for diffrent executionns
logdatetime=`date +%Y%m%d_%T|tr ':' '_'`
# 1st dir under repo root in path to python scripts used to run $acceptancetest
src_topdir="che-test"
doc_topdir="che-docs"
# relative path for dredd related 
dredd_repo_path=${deploybase}/${src_topdir}/scripts/dredd-api-testing
# environment based path to dredd config file dredd.yml
dredd_env_cfg=${dredd_repo_path}/dredd.yml
# evnironment based path to dreed hooks.py
dredd_hooks=${dredd_repo_path}/hooks.py
# python autotests base
python_tests_basedir=${deploybase}/${src_topdir}/scripts/python-autotests
# common for python scripts config reader
python_config_reader=${python_tests_basedir}/config.py
# python commons folder
python_commons=${python_tests_basedir}/common
# legacy python common include file
python_legacy_common=${python_tests_basedir}/common_test_functions.py
# new logger, also required by legacy commons
python_logger=${python_tests_basedir}/common/common_logger.py
#  json config common for python scripts 
json_env_config=${python_tests_basedir}/config.json
# all logs and screenshots will be copied there. Must not be the same as rundir
logdir="${deploybase}/che-test/public_html"
# old logs will be moved to $OldLogsMoveTo
OldLogsMoveTo="${logdir}/old_logs"
# окончания имени логов 
logfilesuffix="log"
xmllogfilesuffix="xml"
htmllogfilesuffix="html"
# keep old logs this number of days, if 0 - do not keep logs
LogsKeepDays=2
# если скрипт отсылает нотификации, то на этот адрес
mail_report_to="p4j2b8j3r1m8j5m8@cherehapa.slack.com,olli@cherehapa.ru"

## do not edit vars below if unsure
# acceptance test name
acceptancetest="acceptance_test.py"
# how long to wait till Xvfb is ready with new display: some times firefox reports no access to display. This should provide time for Xvfb to finish its start.
XVfb_settle_seconds=4
# required when console is not configured properly.
export PYTHONIOENCODING=UTF-8

#### common functions

# overwrites dredd-related files , assuming current position in $dredd_repo_path or a copy of it.
function install_dredd_deps_from_current_repo() {
    if [ "$rundir" == "${dredd_repo_path}" ]; then
      if [[ -r "./python-autotests/config.py" ]]; then # check for any file that must be in repo
         if [[ -r "${python_config_reader}" ]]; then 
           echo " Notice - for files under $dredd_repo_path we omit updating dredd related dependencies: environment seems already deployed."
           return 
          else
           echo " Environment looks to be only partially deployed. Trying to place some files from current repo.."
           sudo cp -rf ./python-autotests    ${deploybase}/${src_topdir}/scripts
           sudo cp -rf ./dredd-api-testing   ${deploybase}/${src_topdir}/scripts
         fi
       else
         echo " Notice - omitting update of dredd related dependencies. Environment seems already deployed."
      fi
    fi
    if [[ -r "./python-autotests/config.py" ]]; then # check for any file that must be there
      echo " Seems we're executing from a copy of cherehapa repository."
      echo " Overwriting all python autotests and dredd related files in $rundir from this repository.. "
      sudo cp -rf ./python-autotests        $rundir/..
      sudo cp -rf ./dredd-api-testing/*.*   $rundir
      echo " Note: we don't cleanup those files at the end since those are overwiten each start."
      echo "Done."
    else
     echo "Unable to find dependency files. Abort."
     exit 253
    fi
}
#end of function overwrite_dredd_deps_from_current_repo()


function Add2prepareLogAndRemove() {
   file2operate=$1
   if [ -z "${file2operate}" ]; then
     echo "Incorrect use of Add2prepareLogAndRemove() function from common_test_env.sh . Abort."
     exit 1
   fi
   cat $file2operate >> $prepare_log
   rm -f $file2operate 2>/dev/null >/dev/null
}

function rename_logs_by_format() {
 # acceptance
 if [[ ! -r ./geckodriver.${testname}.${logdatetime}.$logfilesuffix ]]; then
  mv -f ./geckodriver.log ./geckodriver.${testname}.${logdatetime}.$logfilesuffix 2>/dev/null 
 fi
 if [[ ! -r ./firefox.${testname}.${logdatetime}.$logfilesuffix} ]]; then
  mv -f ./firefox.log ./firefox.${testname}.${logdatetime}.$logfilesuffix} 2>/dev/null
 fi
 if [[ ! -r ./nosetests.${testname}.${logdatetime}.$xmllogfilesuffix ]]; then
  mv -f ./nosetests.xml ./nosetests.${testname}.${logdatetime}.$xmllogfilesuffix 2>/dev/null
 fi
 # dredd
 if [[ ! -r ./dredd-tests.${testname}.${logdatetime}.$xmllogfilesuffix ]]; then
  mv -f ./dredd-tests.xml ./dredd-tests.${testname}.${logdatetime}.$xmllogfilesuffix 2>/dev/null
 fi
}

# remove logs older than $LogsKeepDays from $OldLogsMoveTo , parameters: space separated list of escaped patterns (file names without paths)
function remove_too_old_logs() {
 local files="${@}"
 local filename
 eval "echo \"  Removing too old files in '${OldLogsMoveTo}'..\"" $outputredirect
 for filename in $files ; do
  local execstr
  execstr="find  \"${OldLogsMoveTo}\" -maxdepth 1 \! -newermt \"`date --date \"$logskeepdays days ago\"`\" -type f -name \"${filename}\" -exec rm -vf '{}' \;"
  eval "echo -e \"\\\tusing: '${execstr}' command to aquire files..\"" $outputredirect
  eval "${execstr}" $outputredirect
 done
}

# move logs from $logdir to $OldLogsMoveTo, parameters: space separated list of escaped patterns (file names without paths)
function move_old_logs() {
 local files="${@}"
 local filename
 eval "echo \"  Moving log files from '$logdir' to '${OldLogsMoveTo}'..\"" $outputredirect
 for filename in $files ; do
  local execstr
  execstr="find \"${logdir}\" -maxdepth 1 \! -newermt \"`date --date \"$logskeepdays days ago\"`\" -type f -name \"${filename}\" -exec mv -vf '{}' \"$OldLogsMoveTo\" \;"
  eval "echo -e \"\\\tusing: '${execstr}' command to aquire files..\"" $outputredirect
  eval "${execstr}" $outputredirect
 done
}

# cleanup $rundir from log files
# parameters: space separated list of escaped patterns (file names without paths)
function remove_files_from_rundir() {
 local files="${@}"
 local filename
 eval "echo \"  Removing files from '${logdir}' ..\"" $outputredirect
 for filename in $files ; do
  local execstr
  execstr="find \"${rundir}\" -maxdepth 1 -type f -name \"${filename}\" -exec rm -vf '{}' \;"
  eval "echo -e \"\\\tusing: '${execstr}' command to aquire files..\"" $outputredirect
  eval "${execstr}" $outputredirect
 done
}

# copy logs from $rundir to $logdir, parameters: space separated list of escaped patterns (file names without paths)
function copy_logs_to_logdir() {
 local files="${@}"
 local filename
 ##eval "echo \"  Copying files matching '${files}' to '${logdir}' ..\"" $outputredirect
 for filename in $files ; do
  local execstr
  if [[ -r "${filename}" ]]; then 
    # param is path
    execstr="cp -f \"${filename}\" ${logdir}"
    ##eval "echo -e \"\\\tusing: '${execstr}' command to aquire files..\"" $outputredirect
    eval "${execstr}" $outputredirect
   else
    # param is pattern
    execstr="find \"${rundir}\" -maxdepth 1 -type f -name \"${filename}\" -exec cp -f '{}' \"${logdir}\" \;"
    ##eval "echo -e \"\\\tusing: '${execstr}' command to aquire files..\"" $outputredirect
    eval "${execstr}" $outputredirect
  fi
 done
 # nightwatch
 cp -f ${rundir}/selenium-debug.log ${logdir}/nightwatch-selenium-debug.${logdatetime}.log 2>/dev/null
 if [[ -d "./reports" ]]; then
  cp -rf ./reports ${logdir}/nightwatch-reports.$logdatetime 2>/dev/null
 fi
}
# end of function copy_logs_to_logdir()

# make sure we've write access to logs
function check_logs_writable() {
 local files="${@}"
 for file in $files ; do
   remove_after_touch="no"
   if [[ ! -e "${file}" ]]; then
    remove_after_touch="yes"
   fi
   touch $file >/dev/null 2>/dev/null 3>/dev/null
   retc=$?
   if [ "${retc}" != "0" ]; then
    eval "echo -e \"\\\n`basename ${0}`: ERROR: No write access: non-zero return from 'touch '${file}' . Abort.\"" $outputredirect
    exit 1
   fi
   if [ "${remove_after_touch}" == "yes" ]; then
     rm -f $file >/dev/null 2>/dev/null 3>/dev/null
   fi
 done
}

# prepare dirs
function prepare_dirs() {
 local params="${@}"
 eval "echo \"  Creating directories..\"" $outputredirect
 uid=`id -u`
 for d in $params ; do
  eval "echo -n  \"    '${d}' .. \""
  echo
  if [[ ! -d "${d}" ]]; then 
   eval "sudo -n mkdir -p \"${d}\"" $outputredirect
  fi
  eval "sudo -n chown $uid \"${d}\"" $outputredirect
  eval "sudo -n chmod a+rx \"${d}\"" $outputredirect
  eval "sudo -n chmod u+w  \"${d}\"" $outputredirect
 done
 eval echo $outputredirect
}


# check we're allowed to run sudo with each of commands passed to this function as parameter
# typical usage: check_sudo_access cmd1 cmd2 ... cmdN
function check_sudo_access() {
 sudo_cmds="${@}"
 eval "echo \"  Checking we've access to sudo for utils we use it with..\"" $outputredirect
 for cmd in $sudo_cmds ; do 
  cmd_path=`which $cmd`
  sudo -nl $cmd_path >/dev/null 2>/dev/null 3>/dev/null
  retc=$?
  if [ "${retc}" != "0" ]; then
   eval "echo -e \"\\\n`basename ${0}`: Looks like we are not allowed to run '${cmd_path}' with sudo.\\\nAbort.\\\n\"" $outputredirect
   eval "echo \"'sudo' in '${0}' is used in non-interactive mode & thus cannot ask password.\"" $outputredirect
   eval "echo -e \"Note, if you run '${0}' script interactively & know root password:\\\n\\\n run 'sudo ls' (or other allowed cmd) and then rerun `basename ${0}`.\\\n\"" $outputredirect
   eval "echo \"This is needed due to 'sudo' doesn't ask password if it was provided within little timeout earlier.\"" $outputredirect
   exit 2
  fi
 done
}

# Abort if one of these is not present in $PATH
function check_deps() {
 dependencies="${@}"
 eval "echo \"  Checking required dependencies are available..\"" $outputredirect
 for what in $dependencies ; do
  unalias $what >/dev/null 2>/dev/null
  which $what 2>/dev/null >/dev/null
  retc=$?
  if [ "${retc}" != "0" ]; then
   eval "echo -e \"\\\n${0}: ERROR: Requred '\"${what}\"' utility not found. Abort.\"" $outputredirect
   exit 3
  fi
 done
}

# Abort if one of these is not present or not readable on disk
function check_files_readable() {
 local file_list="${@}"
 eval "echo \"Checking required files are available..\"" $outputredirect
 for what in ${file_list} ; do
  if [[ ! -r "$what" ]]; then
   eval "echo -e \"\\\n${0}: ERROR: Requred \"${what}\" not readable or absent. Abort.\"" $outputredirect
   exit 3
  fi
 done
}


# safety check as we later use 'rm -f' & 'mv -f' and find with these:
function check_vars() {
 eval "echo \"  Checking required variables are set..\"" $outputredirect
 for var in "$rundir" "$logdir" "$deploybase" "$OldLogsMoveTo" "$logfileprefix" "$logfilesuffix" \
             "$LogsKeepDays" "$src_topdir" "$prepare_log" ; do
  if [ -z "$var" ]; then
    eval "echo -e \"\\\n${0}: configuration error. One of requred variables is not set:\"" $outputredirect
    eval "echo \"     \\\$rundir \\\$logdir \\\$deploybase \\\$OldLogsMoveTo \\\$logfileprefix \\\$logfilesuffix \
 \\\$LogsKeepDays \\\$src_topdir \\\$prepare_log . \"" $outputredirect
    eval "echo \"Abort.\"" $outputredirect
    exit 4 
  fi
 done
 if [ "${rundir}" == "${logdir}" ]; then
  eval "echo -e \"\\\n${0}: ERROR: \\\$rundir cannot be same as \\\$logdir . Abort.\"" $outputredirect
  exit 5
 fi
 for dir in $rundir $logdir ; do 
  echo $prepare_log | grep $dir >/dev/null 2>/dev/null 3>/dev/null
  retc=$?
  if [ "${retc}" == "0" ]; then
   eval "echo -e \"\\\n${0}: ERROR: \\\$prepare_log cannot be placed below '${dir}' . Better set it under '/tmp'. Abort.\"" $outputredirect
   exit 6
  fi
 done
}
# end of function check_vars()

function start_Xvfb {
    xvfb_is_running=`ps awxu |grep Xvfb|grep -v grep|grep "x24 :${DISPLAY_NUM}"|wc -l`
    if [ A"${xvfb_is_running}" = "A0" ]; then
        eval "echo \"  Starting Xvfb ..\"" $outputredirect
        # this ensure that XInitThreads is called and so gl contexts are properly initialized.
        # reference: https://bugzilla.gnome.org/show_bug.cgi?id=747840
        export GST_GL_XINITTHREADS=1
        eval "sudo --preserve-env -n /usr/bin/Xvfb +render -noreset -screen 0 1024x768x24 :${DISPLAY_NUM} -ac" $outputredirect &
        # sometimes firefox reports no access to display. This should provide time for Xvfb to finish its start.
        sleep $XVfb_settle_seconds
    fi
}


# make sure test is executable
function check_is_deployed_and_make_executable() {
 local files="${@}"
 for file in $files ; do
  if [[ ! -e "${file}" ]]; then
    eval "echo -e \"\\\nERROR: '${file}' does not exist. Abort.\"" $outputredirect
    exit 7
  fi
  if [[ ! -x "${file}" ]]; then
   sudo -n chmod 755 "${file}" 
   retc=$?
   if [ "${retc}" != "0" ]; then
    eval "echo -e \"\\\nERROR: Cannot make '${file}' to be executable ('sudo -n chmod 755 ${file}' returned status '${retc}'). Abort.\"" $outputredirect
    exit 8
   fi
  fi
 done
}
# end of function check_is_deployed_and_make_executable()

# makes update for repo in `pwd` && cd $rundir. On error updating: remove contents, cd $rundir & clone it
# repository is passed as 1st param
function update_or_clone_on_error() {
   repository="$1"
   if [ -z "${repository}" ]; then
     echo "Incorrect use of update_or_clone_on_error() function from common_test_env.sh . Abort."
     exit 1
   fi
   OldGitPermMode=`sudo -n git config --get core.filemode`
   sudo -n git config core.filemode false # ignore permission changes for repo in `pwd`
   tmplog=`mktemp --tmpdir="/tmp" repository-update-XXXXXXX.log`
   sudo -n git pull 2>&1 | tee $tmplog # not via eval as it won't fill PIPESTATUS array.
   git_retc=${PIPESTATUS[0]}
   Add2prepareLogAndRemove $tmplog
   eval "sudo chmod -R a+rx ${rundir}/${validator_reponame}" $outputredirect
   sudo -n git config core.filemode $OldGitPermMode
   cd $rundir
   # in case of any error from git pull remove local copy and clone it from repo
   if [ "${git_retc}" != "0" ]; then
     eval "echo \"Update didn't pass. Trying to remove and clone..\"" $outputredirect
     eval "rm -vRf ./${validator_reponame}" $outputredirect
     eval "git clone ${repository}" $outputredirect
   fi
}
# end of function update_or_clone_on_error()

# apiblueprint documentation now sits in main repo, so just
# copy apiblueprint documentation to $rundir
function get_apiblueprints() {
 eval "echo \"Getting/updating apiblueprint documentation from our bitbucket repo..\"" $outputredirect
 local docdir
 echo "Using rundir $rundir ."
 for docdir in 02-API-Common 02-API-Details private avia 02-API-Policy ; do
   cd $rundir
   # copy from $doc_topdir/apiblueprint
   cp -r $deploybase/${doc_topdir}/apiblueprint/$docdir $rundir

   # check that finally we 've blueprint files used by dredd.
   if [[ ! -r "./${docdir}/apiary.apib" ]]; then
      eval "echo \"`pwd`/${docdir}/apiary.apib not found. Fail.\"" $outputredirect
      exit 2
     else
      echo "`pwd`/${docdir}/apiary.apib is ready." 
   fi
 done
}
# end of function get_apiblueprints()


# download api-blueprint-validator in $rundir, 
# apply changes from upstream (if any), apply our patches,
# build deps needed by api-blueprint-validator by 'npm i'
function get_and_build_apiblueprint_validator() {
 validator_reponame="api-blueprint-validator"
 our_branch="patches_accepted_for_cherehapa"
 repostr="https://${git_user}:${git_pass}@github.com/cherehapa/${validator_reponame}.git"
 upstream="https://github.com/JakubOnderka/api-blueprint-validator.git"
 cd ${rundir}
 if [[ -d "./${validator_reponame}/.git" ]]; then
   eval "echo -n \"Updating already downloaded repo '${validator_reponame}' from github..\"" $outputredirect
   cd $validator_reponame
   sudo -n git config core.filemode false # ignore permission changes for repo in `pwd`
   eval "sudo -n git checkout master" $outputredirect
   update_or_clone_on_error "${repostr}"
   cd $validator_reponame
   eval "sudo -n git checkout ${our_branch}" $outputredirect
   update_or_clone_on_error "${repostr}"
   eval "echo \" done.\"" $outputredirect
  else
   sudo rm -Rf ./$validator_reponame 2>/dev/null 
   eval "echo \"Cloning '${validator_reponame}' from github..\"" $outputredirect
   eval "git clone ${repostr}" $outputredirect
 fi
 # ensure download finished okay
 if [[ ! -d "./${validator_reponame}/.git" ]]; then
   eval "echo \"ERROR: Failed cloning repository 'github.com/cherehapa/${validator_reponame}' - no '${validator_reponame}/.git/' after git clone.\"" $outputredirect
   exit 1 
 fi
 cd $validator_reponame
 sudo -n git remote add upstream $upstream >/dev/null 2>/dev/null
 sudo -n git config core.filemode false # ignore permission changes for repo in `pwd`
 eval "git checkout master" $outputredirect
 eval "echo \"Applying changes from upstream (if any)..\"" $outputredirect
 # apply changes from upstream 
 tmplog=`mktemp --tmpdir="/tmp" UpdateApiblueprintValidator-XXXXXXX.log`
 git pull --rebase upstream master 2>&1 | tee $tmplog # not via eval as it won't fill PIPESTATUS array.
 pull_retc=${PIPESTATUS[0]}
 Add2prepareLogAndRemove $tmplog
 if [ "${pull_retc}" != "0" ]; then # this shouln't ever happen - we didn't touch master. Notify about this.
  echo "Pull with rebase on upstream in 'master' in cherehapa clone of api-blueprint-validator repo didn't return success. Please check." | \
 mail -s "WARNING: Our copy of $validator_reponame repo needs your attention: autorebase from upstream failed \
 (reported by '`basename ${0}`' (executed at '`hostname`' in '`pwd`'))." $mail_report_to
  eval "echo \"Autorebase on upstream failed. Getting back to our working branch '${our_branch}'..\"" $outputredirect
  eval "git reset --hard git reset --hard ORIG_HEAD" $outputredirect
 fi
 # merge with our our patches
 eval "git checkout $our_branch" $outputredirect
 tmplog=`mktemp --tmpdir="/tmp" UpdateApiblueprintValidator-XXXXXXX.log`
 git rebase master 2>&1 | tee $tmplog # not via eval as it won't fill PIPESTATUS array.
 rebase_retc=${PIPESTATUS[0]}
 Add2prepareLogAndRemove $tmplog
 if [ "${rebase_retc}" != "0" ]; then # newerst changes in upstream are incompatible with our branch - notify about this.
  echo "Rebase on upstream-rebased master in '${our_branch}' in cherehapa clone of api-blueprint-validator repo didn't return success. Please check." | \
 mail -s "WARNING: Our copy of $validator_reponame repo needs your attention: autorebase from upstream failed \
 (reported by '`basename ${0}`' (executed at '`hostname`' in '`pwd`'))." $mail_report_to
  eval "echo \"Autorebase on upstream failed. Getting back to our working branch '${our_branch}'..\"" $outputredirect
  # get back to working state
  eval "git reset --hard ORIG_HEAD" $outputredirect
 fi
 # build
 npm i
 npm_install_retc=$? 
 if [ "${npm_install_retc}" != "0" ]; then
   eval "echo \"WARNING: 'npm i' in `pwd` returned $npm_install_retc .\""
 fi
 eval "echo \"Checking for unmet dependencies with 'npm ls' ..\"" $outputredirect
 tmplog=`mktemp --tmpdir="/tmp" UpdateApiblueprintValidator-XXXXXXX.log`
 npm ls >/dev/null 2>&1 | tee $tmplog # not via eval as it won't fill PIPESTATUS array.
 npm_ls_retc=${PIPESTATUS[0]}
 Add2prepareLogAndRemove $tmplog
 if [ "${npm_ls_retc}" != "0" ]; then
   eval "echo \"'npm i' failed to build all dependencies for $validator_reponame . Abort.\"" $outputredirect
   exit 3
 fi
 cd $rundir
}

# end of function get_and_build_apiblueprint_validator
