#!/bin/bash
#
# Cкрипт для запуска acceptance_test.py с опцией не покупать полис для проверки корректности 
# деплоя на прод. 
#
# Может запускаться на любом хосте, не требует развернутого репозитория и конфигурационных файлов,
# всвязи с этим не использует common_test_env.sh.
#
# run_deploy_checks.sh  задуман как самостоятельный скрипт - он сам подтягивает всё нужные ему файлы из repo с учётом
# встроенных переменных. 
#
# Требует безпарольного sudo и доступа в git к che-all (строка по умолчанию "git@..." предополагает доступ по ключу)
# 
# Описание работы:
#           0)  создаёт используя sudo каталоги для запуска, для логов, перемещения старых логов, даёт текущему пользователю права на них
#           1)  берёт из репо ниже $src_dir файлы $src_files для запуска теста (в ~/ssh/config должен быть прописан ssh key для работы с repo), 
#           2)  копирует в текущий каталог готовый конфиг staging'а как ./config.json и остальные файлы необходимые для запуска, 
#               правит sed'ом отключая покупку полиса config.json  и в config.py указывая брать конфиг из $rundir
#           3)  запускает тест
#           4)  если код завершения теста не 0 - архивирует вывод теста и скриншоты в архив 
#               и отправляет его на $MAIL_REPORT_TO в противном случае завершает работу
#

#### vars
test_name="deploy_check" # used in file names 
# display number to create with Xvfb
DISPLAY_NUM=19
# path where we're usually deployed, used in prepare_config_py() + variables w/ dir definition 
deploybase=/var/www
# all logs and screenshots will be copied there. Must not be the same as rundir
logdir="${deploybase}/che-test/public_html"
# we extract files & run in $rundir
rundir="${deploybase}/che-test/deploy_check"
# old logs will be moved to $OldLogsMoveTo
OldLogsMoveTo=${logdir}/old_logs
# keep old logs this number of days, if 0 - do not keep logs
LogsKeepDays=0
#log file name modifier for different executions
logdatetime=`date +%Y%m%d_%T|tr ':' '_'`
logfileprefix="deploy_check"
logfilesuffix="log"
# finally log file name w/o path
logfile="${logfileprefix}.${logdatetime}.${logfilesuffix}"
# имя лога куда перенаправять вывод команд подготовки работы acceptance_test.py с опцией не покупать полис и конфигом прода
prepare_log_prefix="prepare"
prepare_log="/tmp/${prepare_log_prefix}.${test_name}.${logdatetime}.${logfilesuffix}"
# acceptance test name
acceptancetest="acceptance_test.py"
# 1st dir under repo root in path to python scripts used to run $acceptancetest
src_topdir="che-test"
# path relative to repository root to python scripts used to run $acceptancetest
src_dir="${src_topdir}/scripts/python-autotests"
# list of files required to run acceptance test, space-separated
src_files="$acceptancetest config.py common_test_functions.py config.staging.json"
prod_db_host="db.aws.che.lo"
prod_db_user="cheDB"
prod_db_passwd="nee7AhTohnah0ahp"
prod_db_name="cherehapa"
staging_db_host="db.staging.cherehapa.ru"
staging_db_user="chedb"
staging_db_passwd="Ohp8eiK4"
staging_db_name="cherehapa_funk"
# who will get email reports
mail_report_to="p4j2b8j3r1m8j5m8@cherehapa.slack.com,olli@cherehapa.ru"
# 'mail' utility option to make attachment - variant used in your system
attach_file_opt='-A' # 'mailutils' package /bin/mail option variant
#attach_file_opt='-a' # 'heirloom-mailx' package /bin/mail option variant
### do not edit vars below if unsure
repostr="ssh://git@bitbucket.org/tsystem-ondemand/che-all.git"
# list of commands used w/ sudo, space separated
sudo_cmds="chmod chown mkdir Xvfb"
# space separated list of external apss required in $PATH by this script or by executables it starts
dependencies="sudo which basename grep ps wc awk Xvfb sleep hostname mail sed mv rm cp ls mkdir chmod chown id tee firefox python nosetests google-chrome"

# how long to wait till Xvfb is ready w/ new display: some times firefox reports no access to display. This should provide time for Xvfb to finish its start.
XVfb_settle_seconds=4
outputredirect=" 2>&1 3>&1 |tee -a ${prepare_log}" 
# tar stdout tmp output file 
tartmplog=/tmp/tar_output.${logdatetime}.log
# required when console is not configured properly.
export PYTHONIOEnameG="UTF-8"
#### functions 

# make sure we've write access to logs
function check_logs_writable() {
 files="${@}"
 for file in $files ; do
   remove_after_touch="no"
   if [ ! -a "${file}" ]; then
    remove_after_touch="yes"
   fi
   touch $file >/dev/null 2>/dev/null 3>/dev/null
   retc=$?
   if [ "${retc}" != "0" ]; then
    eval "echo \"No write access: non-zero return from 'touch '${file}' . Abort.\"" $outputredirect
    exit 9
   fi
   if [ "${remove_after_touch}" == "yes" ]; then
     rm -f $file >/dev/null 2>/dev/null 3>/dev/null
   fi
 done
}

function rename_logs_by_format() {
 mv -f ./geckodriver.log ./geckodriver.${logdatetime}.log 2>/dev/null
 mv -f ./firefox.log ./firefox.${logdatetime}.log 2>/dev/null
}

# create virtual display with Xvfb
function start_Xvfb {
 xvfb_is_running=`ps awxu |grep Xvfb|grep -v grep|grep "x24 :${DISPLAY_NUM}"|wc -l`
 if [ A"${xvfb_is_running}" = "A0" ]; then
  eval "echo \"  Starting Xvfb ..\"" $outputredirect
  GST_GL_XINITTHREADS=1
  eval "sudo --preserve-env -n /usr/bin/Xvfb +render -noreset -screen 0 1024x768x24 :$DISPLAY_NUM -ac" $outputredirect &
  # some times firefox reports no access to display. This should provide time for Xvfb to finish its start.
  sleep $XVfb_settle_seconds
 fi
}

# Abort if one of these is not present in $PATH
function check_deps() {
 eval "echo \"  Checking required dependencies are available..\"" $outputredirect
 # firefox & python 're required by acceptance_test.py , everything else is $0 dependencies.
 for what in $dependencies ; do
  unalias $what >/dev/null 2>/dev/null
  which $what 2>/dev/null >/dev/null
  retc=$?
  if [ "${retc}" != "0" ]; then
   eval \"echo "${0}: Requred \"${what}\" utility not found. Abort.\"" $outputredirect
   exit 1
  fi
 done
}

# extract files from repo
function get_src_files_from_repo() {
 cd $rundir
 retc=$?
 if [ "${retc}" != "0" ]; then
  eval "echo \"Cannot 'cd' to '${rundir}'. Abort.\"" $outputredirect
  exit 6
 fi
 for filename in $src_files ; do 
  eval "git archive --remote=\"${repostr}\" HEAD: ${src_dir}/$filename | tar -x --overwrite --warning=no-timestamp" $outputredirect
  retc=$?
  if [ "${retc}" != "0" ]; then
   eval "echo -e \"* Permissions:\\\n-------cut------\"" $outputredirect
   eval "ls -ld ${rundir}" $outputredirect
   eval "echo \"-------cut------\"" $outputredirect
   eval "echo -e \"* Extended permissions via lsattr:\\\n-------cut------\"" $outputredirect
   eval "lsattr ${src_dir}/$file ${rundir}" $outputredirect
   eval "echo -e \"-------cut------\\\n\"" $outputredirect
   eval "echo \"Error: Cannot get source file $file from repo via command: 'git archive --remote=\"${repostr}\" HEAD: ${src_dir}/$filename | tar -x --overwrite --warning=no-timestamp' . Abort.\"" $outputredirect
   exit 4
  fi
  eval mv -f ${src_dir}/$filename ./$filename $outputredirect
 done
 eval rm -Rf "./${src_topdir}" $outputredirect # cleanup dirs made w/ tar
 eval mv -f config.staging.json config.json $outputredirect
}

# make production config from staging config 
function prepare_config_json() {
 eval "echo \"  Preparing config.json ..\"" $outputredirect
 cd $rundir
 retc=$?
 if [ "${retc}" != "0" ]; then
  eval "echo \"Cannot 'cd' to '${rundir}'. Abort.\"" $outputredirect
  exit 6
 fi
 if [ ! -r ./config.json ]; then
  eval "echo \"Error: no ./config.json in $rundir . Abort.\"" $outputredirect
  exit 99
 fi
 # set no buy
 grep acceptance_no_buy_option config.json >/dev/null
 retc=$?
 if [ "${retc}" != "0" ]; then
  eval "echo \"Error: config.json has no option 'acceptance_no_buy_option'. Abort.\"" $outputredirect
  exit 7
 fi
 grep acceptance_no_buy_option config.json |grep "true" >/dev/null
 retc=$?
 if [ "${retc}" != "0" ]; then # is not already 'true'
  eval "sed -i 's/\"acceptance_no_buy_option\"\s*:\s*false/\"acceptance_no_buy_option\":true/g' config.json" $outputredirect
  grep acceptance_no_buy_option config.json |grep "true" >/dev/null
  retc=$?
  if [ "${retc}" != "0" ]; then
   eval "echo \"failed to set option 'acceptance_no_buy_option' in '${rundir}/config.json'. Abort.\"" $outputredirect
   exit 8
  fi
 fi
 # set env_name 
 grep env_name config.json >/dev/null
 retc=$?
 if [ "${retc}" != "0" ]; then
  eval "echo \"config.json has no option 'env_name'. Abort.\"" $outputredirect
  exit 7
 fi
 eval "sed -i 's/\"env_name\"\s*:\s*\"staging\"/\"env_name\":\"production\"/g' config.json" $outputredirect
 grep env_name config.json|grep production >/dev/null
 retc=$?
 if [ "${retc}" != "0" ]; then
  eval "echo \"Error: unable to set 'env_name' to 'production' in config.json in $rundir'. Abort.\"" $outputredirect
  exit 7
 fi
 # set database host
 grep $staging_db_host config.json >/dev/null 
 retc=$?
 if [ "${retc}" != "0" ]; then
  eval "echo \"Error: config.json has no '${staging_db_host}' we base our modifications on. Abort.\"" $outputredirect
  exit 7
 fi
 eval "sed -i \"s@\\\"host\\\"\\\s*:\\\s*\\\"${staging_db_host}\\\"@\\\"host\\\":\\\"${prod_db_host}\\\"@g\" config.json" $outputredirect
 grep host config.json|grep -v production_db_host |grep $prod_db_host  >/dev/null
 retc=$?
 if [ "${retc}" != "0" ]; then
  eval "echo \"Error: unable to set database host to '${prod_db_host}' in config.json in ${rundir}'. Abort.\"" $outputredirect
  exit 7
 fi
 # set database user
 grep user config.json |grep $staging_db_user >/dev/null 
 retc=$?
 if [ "${retc}" != "0" ]; then
  eval "echo \"Error: config.json has no '${staging_db_user}' we base our modifications on. Abort.\"" $outputredirect
  exit 7
 fi
 eval "sed -i \"s@\\\"user\\\"\\\s*:\\\s*\\\"${staging_db_user}\\\"@\\\"user\\\":\\\"${prod_db_user}\\\"@g\" config.json" $outputredirect
 grep host config.json|grep -v production_db_host |grep $prod_db_host  >/dev/null
 retc=$?
 if [ "${retc}" != "0" ]; then
  eval "echo \"Error: unable to set database user to '${prod_db_user}' in config.json in ${rundir}'. Abort.\"" $outputredirect
  exit 7
 fi
 # set database passwd
 grep password config.json |grep $staging_db_passwd >/dev/null 
 retc=$?
 if [ "${retc}" != "0" ]; then
  eval "echo \"Error: config.json has no '${staging_db_passwd}' we base our modifications on. Abort.\"" $outputredirect
  exit 7
 fi
 eval "sed -i \"s@\\\"password\\\"\\\s*:\\\s*\\\"${staging_db_passwd}\\\"@\\\"password\\\":\\\"${prod_db_passwd}\\\"@g\" config.json" $outputredirect
 grep password config.json|grep $prod_db_passwd >/dev/null
 retc=$?
 if [ "${retc}" != "0" ]; then
  eval "echo \"Error: unable to set database password to '${prod_db_passwd}' in config.json in ${rundir}'. Abort.\"" $outputredirect
  exit 7
 fi
 # set database name
 grep database config.json |grep $staging_db_name >/dev/null 
 retc=$?
 if [ "${retc}" != "0" ]; then
  eval "echo \"Error: config.json has no '${staging_db_name}' we base our modifications on. Abort.\"" $outputredirect
  exit 7
 fi
 eval "sed -i \"s@\\\"database\\\"\\\s*:\\\s*\\\"${staging_db_name}\\\"@\\\"database\\\":\\\"${prod_db_name}\\\"@g\" config.json" $outputredirect
 grep database config.json|grep $prod_db_name >/dev/null
 retc=$?
 if [ "${retc}" != "0" ]; then
  eval "echo \"Error: unable to set database name to '${prod_db_name}' in config.json in ${rundir}'. Abort.\"" $outputredirect
  exit 7
 fi
 # replace all other staging hostname based with cherehapa.ru
 eval "sed -i \"s/staging.cherehapa.ru/cherehapa.ru/g\" config.json" $outputredirect
}

# safety check as we later use 'rm -f' & 'mv -f' and find w/ these:
function check_vars() {
 eval "echo \"  Checking required variables are set..\"" $outputredirect
 for var in "${rundir}" "${src_dir}" "${logdir}" "${deploybase}" "${OldLogsMoveTo}" "${logfileprefix}" "${logfilesuffix}" \
             "${acceptancetest}" "${LogsKeepDays}" "${src_topdir}" "${prepare_log}" "${mail_report_to}" "${attach_file_opt}" ; do
  if [ -z "${var}" ]; then
    eval "echo \" ${0}: configuration error. One of requred variables is not set:\"" $outputredirect
    eval "echo \"     \\\$rundir \\\$src_dir \\\$logdir \\\$deploybase \\\$OldLogsMoveTo \\\$logfileprefix \\\$logfilesuffix \
 \\\$acceptancetest \\\$LogsKeepDays \\\$src_topdir \\\$prepare_log \\\$mail_report_to \\\$attach_file_opt . \"" $outputredirect
    eval "echo \"Abort.\"" $outputredirect
    exit 2 
  fi
 done
 if [ "${rundir}" == "${logdir}" ]; then
  eval "echo \"${0}: Error: \\\$rundir cannot be same as \\\$logdir . Abort.\"" $outputredirect
  exit 11
 fi
}

# check we're allowed to run sudo w/ each of $sudo_cmds
function check_sudo_access() {
 eval "echo \"  Checking we've access to sudo for utils we use it with..\"" $outputredirect
 for cmd in $sudo_cmds ; do 
  cmd_path=`which ${cmd}`
  sudo -nl $cmd_path >/dev/null 2>/dev/null 3>/dev/null
  retc=$?
  if [ "${retc}" != "0" ]; then
   eval "echo -e \"\\\n`basename ${0}`: Looks like we are not allowed to run '${cmd_path}' with sudo.\\\nAbort.\\\n\"" $outputredirect
   eval "echo \"'sudo' in '${0}' is used in non-interactive mode & thus cannot ask password.\"" $outputredirect
   eval "echo -e \"Note, if you run '${0}' script interactively & know root password:\\\n\\\n run 'sudo ls' (or other allowed cmd) and then rerun `basename ${0}`.\\\n\"" $outputredirect
   eval "echo \"This is needed due to 'sudo' doesn't ask password if it was provided within little timeout earlier.\"" $outputredirect
   exit 3
  fi
 done
}

# prepare dirs
function make_dirs() {
 eval "echo \"  Creating directories..\"" $outputredirect
 uid=`id -u`
 for d in "${logdir}" "${rundir}" "${OldLogsMoveTo}" ; do 
  eval 'sudo mkdir -p "${d}"' $outputredirect
  eval 'sudo chown $uid "${d}"' $outputredirect
  eval 'sudo chmod a+rx "${d}"' $outputredirect
  eval 'sudo chmod u+w  "${d}"' $outputredirect
 done
}

# make sure test is executable
function make_test_executable() {
 if [ ! -x ${rundir}/$acceptancetest ]; then
  eval sudo chmod 755 "${rundir}/${acceptancetest}" $outputredirect
  retc=$?
  if [ "${retc}" != "0" ]; then
   eval "echo \"Cannot make '${rundir}/${acceptancetest}' to be executable. Abort.\"" $outputredirect
   exit 5
  fi
 fi
}

function prepare_config_py() {
 eval "echo \"  Preparing config.py ..\"" $outputredirect
 # set config.json source
 grep hostconfig config.py >/dev/null
 retc=$?
 if [ "${retc}" != "0" ]; then
  eval "echo \"config.py has no string defining 'hostconfig'. Abort.\"" $outputredirect
  exit 9
 fi
 eval "sed -i \"s@hostconfig\\\s*\\=\\\s*\\\"${deploybase}/${src_dir}/config.json\\\"@hostconfig\\=\\\"${rundir}/config.json\\\"@g\" config.py" $outputredirect
 grep hostconfig config.py | grep ${rundir}/config.json >/dev/null
 retc=$?
 if [ "${retc}" != "0" ]; then
  eval "echo \"failed to set hostconfig in '${rundir}/config.py'. Abort.\"" $outputredirect
  exit 10
 fi 
} 

#### here we start
check_vars
check_deps
check_sudo_access
make_dirs
cd $rundir
check_logs_writable $prepare_log $tartmplog ./$logfile
get_src_files_from_repo
make_test_executable
prepare_config_json
prepare_config_py

logfiles="${logfileprefix}.\\*.$logfilesuffix ${prepare_log_prefix}.\\*.$logfilesuffix geckodriver.\\*.log \\*.png"

# remove logs older than $LogsKeepDays
eval "echo \"  removing too old files in '${rundir}' and '${OldLogsMoveTo}'..\"" $outputredirect
for filename in $logfiles ; do
 eval "find \"${OldLogsMoveTo}\" -maxdepth 1 \! -newermt \"`date --date \"$logskeepdays days ago\"`\" -type f -name \"${filename}\" -exec rm -vf '{}' \;" $outputredirect
done
# move old logs not removed above to $OldLogsMoveTo
eval "echo \"  Moving files left in '${logdir}' into '${OldLogsMoveTo}' dir ..\"" $outputredirect
for filename in $logfiles ; do
 eval "find \"${logdir}\" -maxdepth 1 -type f -name \"${filename}\" -exec mv -vf '{}' \"${OldLogsMoveTo}\" \; " $outputredirect
done

# prepare display
start_Xvfb

eval "echo \"  Starting $acceptancetest test (buyng policy disabled)..\"" $outpudredirec
DISPLAY=:$DISPLAY_NUM GST_GL_XINITTHREADS=1 ./$acceptancetest 2>&1 3>&1 | tee -a ./$logfile
test_retc=$?

rename_logs_by_format

if [ "${test_retc}" != "0" ]; then
  eval "echo \"ALERT: $acceptancetest test run FAILED (at $logdatetime w/ disabled policy buying, executed on host '`hostname`').\"" $outputredirect
  files2tar=""
  for f in "${prepare_log}" "${logfile}" "geckodriver.${logdatetime}.log" "firefox.${logdatetime}.log" *.png ; do
   if [ -r $f ]; then 
    files2tar="$files2tar ${f}"
   fi
  done
  eval "echo \"  Creating archive with files generated during this run..\"" $outputredirect
  tar --warning=no-timestamp -czvf failed_test_logs.${logdatetime}.tar.gz $files2tar  2>&1 3>&1 |tee $tartmplog
  cat $tartmplog >> $prepare_log
  rm -f $tartmplog
  eval "echo \"  Mailing logs to '${mail_report_to}' .. \"" $outputredirect
  eval "echo 'ALERT: PRODUCTION DEPLOYMENT TEST FAILED! See logs in attachment'|mail  $attach_file_opt \"./failed_test_logs.${logdatetime}.tar.gz\" -s \"ALERT: $acceptancetest deployment test failed.\" ${mail_report_to}" $outputredirect
  rm -f ./failed_test_logs.${logdatetime}.tar.gz # cleenup tgz - no need in local duplicates
fi
files2mv=""
for f in "${prepare_log}" "./${logfile}" "./geckodriver.${logdatetime}.log" "./firefox.${logdatetime}.log" ./*.png ; do
  if [ -r $f ]; then 
    files2mv="$files2mv ${f}"
   fi
  done
mv -f $files2mv $logdir 

exit $test_retc
