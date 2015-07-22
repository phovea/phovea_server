#!/usr/bin/env bash

function install_apt_dependencies {
  if [ -f debian.txt ] ; then
    echo "--- installing apt dependencies ---"
    wd="`pwd`"
    cd /tmp #switch to tmp directory
    set -vx #to turn echoing on and
    sudo apt-get install -y python-pip python-dev zlib1g-dev cython `cat $wd/debian.txt`
    set +vx #to turn them both off
    cd $wd
    rm debian.txt
  fi
}
function install_pip_dependencies {
  if [ -f requirements.txt ] ; then
    echo "--- installing pip dependencies ---"
    wd="`pwd`"
    cd /tmp #switch to tmp directory
    sudo pip install -r $wd/requirements.txt
    set -vx #to turn echoing on and
    cd $wd
    rm requirements.txt
  fi
}

function create_virtualenv {
  echo "--- creating virtual environment ---"
  wd="`pwd`"
  sudo pip install virtualenv
  virtualenv venv
  source venv/bin/activate
}

function deactivate_virtualenv {
  deactivate
}

function create_run_script {
    echo "#!/usr/bin/env bash

venv/bin/python plugins/caleydo_server --multithreaded
" > run.sh
}

install_apt_dependencies
create_virtualenv
install_pip_dependencies
deactivate_virtualenv
create_run_script