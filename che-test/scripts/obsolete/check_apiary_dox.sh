#!/bin/bash
#
# script to verify cherehapa documentation in apibluprint format.
#
# Copies apib files to $rundir, downloads compiles verifier utility, checks,
# applies our patches, builds it, then  runs verifier on apiary.apib files .
#
# This script should be executed manually on update of our apiblueprint 
# documentation.
#
# (c) olli@cherehapa.ru, (c) cherehapa /2016, 2017
#

# import common functions & variables
if [ -r "./common_test_env.sh" ]; then
 . ../../common_test_env.sh
else
  echo -e "No ./common_test_env.sh in `pwd` . Is env deployed correctly? Abort."
  exit 253
fi

## do not edit vars below if unsure
prepare_log=`mktemp --tmpdir="/tmp" prepare-check-apiblueprint-XXXXXXX.log`
# access to our clone of api-blueprint-validator repo w/ these l/p
git_user=cherehapa
git_pass=Toor6eex
rundir="${deploybase}/che-test/apiblueprint_documentation_check" 
# list of commands used w/ sudo, space separated (always include "mkdir chown chmod" as its used by common_test_env.sh)
sudo_cmds="mkdir chown chmod git rm docker apt-get npm"
dependencies="basename tee which rm cp ls grep awk git pwd ruby rake hostname mktemp tr sleep"

### start here

# repeat import to renew function definitions: outputredirect & some other variables used there were modified above between imports
. ../../common_test_env.sh

# local vars check
for var in "${rundir}" ; do
 if [ -z "${var}" ]; then
   eval "echo \" `basename ${0}`: configuration error. One of requred variables is not set:\""
   eval "echo \"   \\\$rundir  \"" 
   eval "echo \"Abort.\"" 
   exit 1 
 fi
done
check_deps $dependencies
check_sudo_access $sudo_cmds
prepare_dirs "${rundir}"

# ensure we have new node-gyp
distribution=$(echo `cat /etc/os-release |grep ^ID=`|tr '=' ' '|awk -- '{print $2}')
if [ "${distribution}" == "ubuntu" ]; then
  eval "sudo apt-get remove -y node-gyp" 
 elif [ "${distribution}" == "fedora" ]; then
  eval "sudo rpm -e --force --nodeps node-gyp" 
fi
sudo npm i -g node-gyp 

cd $rundir
get_apiblueprints

get_and_build_apiblueprint_validator

# now ready to verify documentation
dox_check_status=0
echo -e "\n--> Starting documentation check.."
failed_repos=""
for d in "02-API-Common" "02-API-Policy" "avia" "private" "02-API-Details"; do
 api-blueprint-validator/bin/api-blueprint-validator --fail-on-warnings=true --require-name=true ${d}/apiary.apib
 validator_retc=$?
 if [ "${validator_retc}" != "0" ]; then
   echo "ERROR: validation failed, 'api-blueprint-validator --fail-on-warnings=true --require-name=true ${d}/apiary.apib' returned non-zero exit status. Abort."
   dox_check_status="$dox_check_status $validator_retc"
   failed_repos="$failed_repos $d"
  else 
   echo "Passed validation for $d/apiary.apib ."
 fi
done
echo "--> Done (with exit codes ${dox_check_status} for appropriate repos '02-API-Common' '02-API-Policy' 'avia' 'private' '02-API-Details')."

if [ "$dox_check_status" != "0" ]; then
  echo -e "\nFailed checking apiblueprint documentation for: $failed_repos .\n"
 else
  echo -e "\nCheck of apiblueprint documentation was successfull.\n"
fi

exit $dox_check_status

