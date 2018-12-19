#!/usr/bin/env bash

# go to the virtualenv dir and activate it
cd /var/www/che-test/scripts/autotests
source venvpython3/bin/activate

# set work dir
cd /var/www/che-test/scripts/dredd-api-testing

# copy apiblueprint docs to the work dir
for docdir in `ls -l /var/www/che-docs/apiblueprint | grep "^d"| awk '{print $9}'`
do
    cp -rf /var/www/che-docs/apiblueprint/$docdir .
done

# sometimes hooks hang and require kill before next run
hooks_pid=`ps ax| grep pyth| grep dredd-hooks-python| grep -v grep| awk -- '{print $1}'`
if [ ! -z \"${hooks_pid}\" ];
then
    kill -9 $hooks_pid 2>/dev/null;
fi

# run dredd, configuration is set in dredd.yml
dredd

# deactivate virtualenv
deactivate
