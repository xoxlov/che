#!/bin/bash
#
# script to verify cherehapa documentation in apibluprint format.
#
# Copies apib files to $rundir, downloads compiles verifier utility, checks,
# applies our patches, builds it, then  runs verifier on apiary.apib files .
#
# This script should be executed manually on update of our apiblueprint 
# documentation.

###############################################################################
# variables
###############################################################################
prepare_log=`mktemp --tmpdir="/tmp" prepare-check-apiblueprint-XXXXXXX.log`
outputredirect=" 2>&1 3>&1 |tee -a ${prepare_log}"
# access to our clone of api-blueprint-validator repo with these l/p
git_user=cherehapa
git_pass=Toor6eex

# deployment root
deploybase=/var/www
rundir="${deploybase}/che-test/apiblueprint_documentation_check"
doc_topdir="${deploybase}/che-docs"

# list of commands used with sudo, space separated (always include "mkdir chown chmod" as its used by common_test_env.sh)
sudo_cmds="mkdir chown chmod git rm docker apt-get npm"
dependencies="basename tee which rm cp ls grep awk git pwd hostname mktemp tr sleep"


###############################################################################
# functions
###############################################################################
# Abort if one of these is not present in $PATH
function check_dependencies() {
    dependencies="${@}"
    eval "echo \"Checking required dependencies are available..\"" $outputredirect
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

function check_install_ruby_and_rake() {
    for what in "ruby rake" ; do
        unalias $what >/dev/null 2>/dev/null
        which $what 2>/dev/null >/dev/null
        retc=$?
        if [ "${retc}" != "0" ]; then
            sudo -H apt-get install --assume-yes ruby
            sudo -H apt-get install --assume-yes rake
        fi
    done
}

# check we're allowed to run sudo with each of commands passed to this function as parameter
# typical usage: check_sudo_access cmd1 cmd2 ... cmdN
function check_sudo_access() {
    sudo_cmds="${@}"
    eval "echo \"Checking we have access to sudo for utils we use it with..\"" $outputredirect
    for cmd in $sudo_cmds ; do
        cmd_path=`which $cmd`
        sudo -nl $cmd_path >/dev/null 2>/dev/null 3>/dev/null
        retc=$?
        if [ "${retc}" != "0" ]; then
            eval "echo -e \"\\\n`basename ${0}`: Looks like we are not allowed to run '${cmd_path}' with sudo.\\\nAbort.\\\n\"" $outputredirect
            eval "echo \"'sudo' in '${0}' is used in non-interactive mode & thus cannot ask password.\"" $outputredirect
            eval "echo -e \"Note, if you run '${0}' script interactively & know root password:\\\n\\\n run 'sudo ls' (or other allowed cmd) and then rerun `basename ${0}`.\\\n\"" $outputredirect
            eval "echo \"This is needed due to 'sudo' does not ask password if it was provided within little timeout earlier.\"" $outputredirect
            exit 2
        fi
    done
}

function prepare_dirs() {
    local params="${@}"
    eval "echo \"Creating directories..\"" $outputredirect
    uid=`id -u`
    for directory in $params ; do
        eval "echo -n  \"    '${directory}' .. \""
        echo
        if [[ ! -d "${directory}" ]]; then
            eval "sudo -n mkdir -p \"${directory}\"" $outputredirect
        fi
        eval "sudo -n chown $uid \"${directory}\"" $outputredirect
        eval "sudo -n chmod a+rx \"${directory}\"" $outputredirect
        eval "sudo -n chmod u+w  \"${directory}\"" $outputredirect
    done
    eval echo $outputredirect
}

function install_latest_node_gyp() {
    # ensure we have new node-gyp
    distribution=$(echo `cat /etc/os-release |grep ^ID=`|tr '=' ' '|awk -- '{print $2}')
    if [ "${distribution}" == "ubuntu" ]; then
        eval "sudo apt-get remove -y node-gyp"
    elif [ "${distribution}" == "fedora" ]; then
        eval "sudo rpm -e --force --nodeps node-gyp"
    fi
    sudo npm i -g node-gyp
}

# apiblueprint documentation now sits in main repo, so just
# copy apiblueprint documentation to $rundir
function get_apiblueprint_documentation() {
    eval "echo \"Getting/updating apiblueprint documentation from our bitbucket repo..\"" $outputredirect
    local docdir
    echo "Using rundir $rundir ."
    for docdir in `ls -l /var/www/che-docs/apiblueprint | grep "^d"| awk '{print $9}'`; do
        cd $rundir
        # copy from $doc_topdir/apiblueprint
        cp -r ${doc_topdir}/apiblueprint/$docdir $rundir
        # check that finally we have blueprint files used by dredd.
        if [[ ! -r "./${docdir}/apiary.apib" ]]; then
            eval "echo \"`pwd`/${docdir}/apiary.apib not found. Fail.\"" $outputredirect
            exit 2
        else
            echo "`pwd`/${docdir}/apiary.apib is ready."
        fi
    done
}

function add_to_prepareLog_and_remove() {
    file2operate=$1
    if [ -z "${file2operate}" ]; then
        echo "Incorrect use of add_to_prepareLog_and_remove() function. Abort."
        exit 1
    fi
    cat $file2operate >> $prepare_log
    rm -f $file2operate 2>/dev/null >/dev/null
}

# makes update for repo in `pwd` && cd $rundir. On error updating: remove contents, cd $rundir & clone it
# repository is passed as 1st param
function update_or_clone_on_error() {
    repository="$1"
    if [ -z "${repository}" ]; then
        echo "Incorrect use of update_or_clone_on_error() function. Abort."
        exit 1
    fi
    OldGitPermMode=`sudo -n git config --get core.filemode`
    sudo -n git config core.filemode false # ignore permission changes for repo in `pwd`
    tmplog=`mktemp --tmpdir="/tmp" repository-update-XXXXXXX.log`
    sudo -n git pull 2>&1 | tee $tmplog # not via eval as it will not fill PIPESTATUS array.
    git_retc=${PIPESTATUS[0]}
    add_to_prepareLog_and_remove $tmplog
    eval "sudo chmod -R a+rx ${rundir}/${validator_reponame}" $outputredirect
    sudo -n git config core.filemode $OldGitPermMode
    cd $rundir
    # in case of any error from git pull remove local copy and clone it from repo
    if [ "${git_retc}" != "0" ]; then
        eval "echo \"Update did not pass. Trying to remove and clone..\"" $outputredirect
        eval "rm -vRf ./${validator_reponame}" $outputredirect
        eval "git clone ${repository}" $outputredirect
    fi
}

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
    git pull --rebase upstream master 2>&1 | tee $tmplog # not via eval as it will not fill PIPESTATUS array.
    pull_retc=${PIPESTATUS[0]}
    add_to_prepareLog_and_remove $tmplog
    if [ "${pull_retc}" != "0" ]; then # this should not ever happen - we did not touch master. Notify about this.
        echo "Pull with rebase on upstream in 'master' in cherehapa clone of api-blueprint-validator repo did not return success. Please check." | mail -s "WARNING: Our copy of $validator_reponame repo needs your attention: autorebase from upstream failed (reported by '`basename ${0}`' (executed at '`hostname`' in '`pwd`'))." $mail_report_to
        eval "echo \"Autorebase on upstream failed. Getting back to our working branch '${our_branch}'..\"" $outputredirect
        eval "git reset --hard git reset --hard ORIG_HEAD" $outputredirect
    fi
    # merge with our our patches
    eval "git checkout $our_branch" $outputredirect
    tmplog=`mktemp --tmpdir="/tmp" UpdateApiblueprintValidator-XXXXXXX.log`
    git rebase master 2>&1 | tee $tmplog # not via eval as it will not fill PIPESTATUS array.
    rebase_retc=${PIPESTATUS[0]}
    add_to_prepareLog_and_remove $
    if [ "${rebase_retc}" != "0" ]; then # newerst changes in upstream are incompatible with our branch - notify about this.
        echo "Rebase on upstream-rebased master in '${our_branch}' in cherehapa clone of api-blueprint-validator repo did not return success. Please check." | mail -s "WARNING: Our copy of $validator_reponame repo needs your attention: autorebase from upstream failed (reported by '`basename ${0}`' (executed at '`hostname`' in '`pwd`'))." $mail_report_to
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
    npm ls >/dev/null 2>&1 | tee $tmplog # not via eval as it will not fill PIPESTATUS array.
    npm_ls_retc=${PIPESTATUS[0]}
    add_to_prepareLog_and_remove $tmplog
    if [ "${npm_ls_retc}" != "0" ]; then
        eval "echo \"'npm i' failed to build all dependencies for $validator_reponame. Abort.\"" $outputredirect
        exit 3
    fi
    cd $rundir
}

###############################################################################
# start here
###############################################################################
check_install_ruby_and_rake
check_dependencies $dependencies
check_sudo_access $sudo_cmds
prepare_dirs "${rundir}"
install_latest_node_gyp
cd $rundir
get_apiblueprint_documentation
get_and_build_apiblueprint_validator

# now ready to verify documentation
docs_check_status=0
echo -e "\n--> Starting documentation check.."
# go through API docs directories from /var/www/che-docs/apiblueprint
failed_repos=""
for directory in `ls -l /var/www/che-docs/apiblueprint | grep "^d"| awk '{print $9}'`; do
    api-blueprint-validator/bin/api-blueprint-validator --fail-on-warnings=true --require-name=true ${directory}/apiary.apib
    validator_retc=$?
    if [ "${validator_retc}" != "0" ]; then
        echo "ERROR: validation failed, 'api-blueprint-validator --fail-on-warnings=true --require-name=true ${directory}/apiary.apib' returned non-zero exit status."
        docs_check_status="$docs_check_status $validator_retc"
        failed_repos="$failed_repos ${directory}"
    else
        echo "Passed validation for ${directory}/apiary.apib."
    fi
done

# make string list of API docs directories and print checks return codes
docdirs=""
for directory in `ls -l /var/www/che-docs/apiblueprint | grep "^d"| awk '{print $9}'`; do
    docdirs="$docdirs '${directory}'"
done
echo "--> Done (with exit codes ${docs_check_status} for appropriate repos ${docdirs})."

# print overall check status
if [ "$docs_check_status" != "0" ]; then
    echo -e "\nFailed checking apiblueprint documentation for: $failed_repos.\n"
else
    echo -e "\nCheck of apiblueprint documentation was successfull.\n"
fi

exit $docs_check_status
