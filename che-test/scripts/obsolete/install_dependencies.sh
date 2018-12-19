#!/bin/bash
#
# устанавливает пакеты необходимые автотестам. Запускать до всех автотестов.
# предполагает безпарольное sudo или запуск от рута, заточен на системы с apt (debian/ubuntu).
#
# packages used in autotests
sudo -H apt-get -y install python-mysql.connector
sudo -H apt-get -y install python-pip
sudo -H pip install --upgrade pip
# By default our admin uses mailutils providing similar functionality as heirloom-mailx: /bin/mail,
# though mailutils 'll install MTA as dependency.  heirloom-mailx is not MTA-dependant package. 
# If uncomment it - comment out 'mailutils' installation .
#sudo -H apt-get -y install heirloom-mailx
sudo -H apt-get -y install mailutils
sudo -H pip install -U dredd-hooks
sudo -H pip install -U PyYAML
sudo -H apt-get -y install python-dev
sudo -H pip install -U selenium
sudo -H pip install -U nose
sudo -H pip install -U elementium
sudo -H pip install -U jsonschema
sudo -H apt-get -y -qq install libffi-dev
sudo -H apt-get -y install libssl-dev
sudo -H pip install -U cryptography
sudo -H apt-get -y install npm
sudo -H npm install -g nightwatch
sudo -H npm install -g dredd
sudo -H pip install -U datetime
sudo -H pip install -U requests 
sudo -H pip install -U spur
sudo -H pip install -U temp-mail
sudo -H pip install -U email
sudo -H pip install -U dnspython
sudo -H pip install -U nose-html-report
sudo -H pip install -U nose-html-reporting
sudo -H pip install -U python-dateutil
sudo -H pip install -U urllib3[secure]
sudo -H pip install -U TempMail
sudo -H apt-get -y install firefox

### ensure we have new node-gyp
distribution=$(echo `cat /etc/os-release |grep ^ID=`|tr '=' ' '|awk -- '{print $2}')
if [ "$distribution" == "ubuntu" ]; then
   sudo apt-get remove -y node-gyp
 elif [ "$distribution" == "fedora" ]; then
   sudo rpm -e --force --nodeps node-gyp
fi
sudo npm i -g node-gyp
##

sudo chmod 755 /usr/local/bin/dredd-hooks-python

# download geckodriver for firefox browser (versions below 48) and make it available
# download and install marionette ff driver for selenium
marionette_version=0.19.1
wget -nv https://github.com/mozilla/geckodriver/releases/download/v${marionette_version}/geckodriver-v${marionette_version}-linux64.tar.gz
tar xzf geckodriver-v${marionette_version}-linux64.tar.gz
rm -f geckodriver-v${marionette_version}-linux64.tar.gz
chmod 755 geckodriver
sudo killall wires 2>/dev/null
# older selenium expects 'wires' in PATH
sudo mv -f geckodriver /usr/local/bin/wires
sudo chown root: /usr/local/bin/wires
# newer selenium expects 'geckodriver' in PATH
sudo ln -s /usr/local/bin/wires /usr/local/bin/geckodriver 2>/dev/null

# make python wait more for firefox profile load
for f in /usr/local/lib/python2.7/dist-packages/selenium/webdriver/firefox/webdriver.py /usr/local/lib/python2.7/dist-packages/selenium/webdriver/firefox/firefox_binary.py ; do 
sudo sed -i "s/timeout=30/timeout=60/g" $f
done
