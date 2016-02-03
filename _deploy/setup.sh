#!/usr/bin/env bash
#allow empty matching glob
shopt -s nullglob

#search for the right parent directory such that we have a common start directory
while [[ ! -f "run.sh" ]] && [[ ! -f "Vagrantfile" ]]
do
  cd ..
done

basedir=`pwd`

function sedeasy {
  sed -i "s/$(echo $1 | sed -e 's/\([[\/.*]\|\]\)/\\&/g')/$(echo $2 | sed -e 's/[\/&]/\\&/g')/g" $3
}

function isDebian {
    [ -f /etc/lsb-release ]
}

function isRedHat {
  [ -f /etc/redhat-release ]
}

function isRedHat {
  [ -f /etc/redhat-release ]
}

function install_redhat_anaconda {
  local ANACONDA="Anaconda2-2.4.1-Linux-x86_64.sh"
  wget "https://3230d63b5fc54e62148e-c95ac804525aac4b6dba79b00b39d1d3.ssl.cf1.rackcdn.com/${ANACONDA}"
  chmod +x ${ANACONDA}
  exec ./${ANACONDA}
}

function install_common_dependencies {
  echo "--- installing common  dependencies ---"
  cd /tmp #switch to tmp directory
  set -vx #to turn echoing on and

  isDebian && sudo apt-get install -y python-pip python-dev zlib1g-dev python-numpy python-scipy python-matplotlib wget
  isRedHat && sudo yum install -y zlib-devel wget

  if isRedHat ; then
    install_redhat_anaconda
  fi

  set +vx #to turn them both off
  cd ${basedir}
}

function install_dependencies {
  echo "--- installing dependencies ---"
  cd /tmp #switch to tmp directory
  set -vx #to turn echoing on and

  isDebian && [ -f debian.txt ] && sudo apt-get install -y `cat ${basedir}/debian.txt`
  isRedHat && [ -f redhat.txt ] && sudo yum install -y `cat ${basedir}/redhat.txt`

  set +vx #to turn them both off
  cd ${basedir}
}


function install_pip_dependencies {
  if [ -f requirements.txt ] ; then
    echo "--- installing pip dependencies ---"
    cd /tmp #switch to tmp directory
    pip install -r ${basedir}/requirements.txt
    set -vx #to turn echoing on and
    cd ${basedir}
  fi
}

function create_server_config {
  local name=$1
  cd /tmp #switch to tmp directory
  pip install gunicorn
  set -vx #to turn echoing on and
  cd ${basedir}

  cp gunicorn_start.in.sh gunicorn_start.sh
  sedeasy /var/www/caleydo_app ${basedir} gunicorn_start.sh
  sedeasy caleydo_app ${name} gunicorn_start.sh

  if isRedHat; then #use anaconda
    sedeasy "#ENV_DIR=~/anaco" "ENV_DIR=~/anaco" gunicorn_start.sh
    sedeasy "#ENV_ACTIVATE=acti" "ENV_ACTIVATE=acti" gunicorn_start.sh
  fi

  chmod +x gunicorn_start.sh

  #create the nginx config and enable the site
  if [ -d /etc/nginx ] ; then
    #gunicorn in socket file mode
    sedeasy "#BIND=unix" "BIND=unix" gunicorn_start.sh

    cp nginx.in.conf nginx.conf
    sedeasy /var/www/caleydo_app ${basedir} nginx.conf
    sedeasy caleydo_app ${name} nginx.conf
    sudo ln -s ${basedir}/nginx.conf /etc/nginx/sites-available/${name}
    sudo ln -s ${basedir}/nginx.conf /etc/nginx/sites-enabled/${name}
    sudo service nginx restart
  fi
}

function register_as_service {
  local name=$1
  #install supervisor
  if [ -x "$(command -v apt-get)" ]; then
    sudo apt-get install -y supervisor
  fi

  if [ -x "$(command -v yum)" ]; then
    sudo yum install -y supervisor
  fi

  cp supervisor.in.conf supervisor.conf
  sedeasy /var/www/caleydo_app ${basedir} supervisor.conf
  sedeasy caleydo_app ${name} supervisor.conf

  #create the supervisor config
  sudo ln -s ${basedir}/supervisor.conf /etc/supervisor/conf.d/${name}.conf
  #reread the list of elements
  sudo supervisorctl reread
  sudo supervisorctl update
}

function remove_server_config {
  local name=$1
  #remove the nginx config and disable the site
  if [ -d /etc/nginx ] ; then
    sudo service nginx stop
    sudo rm /etc/nginx/sites-available/${name}
    sudo rm /etc/nginx/sites-enabled/${name}
    sudo service nginx start
  fi
}

function unregister_from_service {
  local name=$1
  sudo rm /etc/supervisor/conf.d/${name}.conf
  #reread the list of elements
  sudo supervisorctl reread
  sudo supervisorctl update
}

function activate_virtualenv {
  source venv/bin/activate
}

function create_virtualenv {
  echo "--- creating virtual environment ---"
  if hash virtualenv 2>/dev/null; then
     echo "virtualenv already installed"
  else
    sudo pip install virtualenv
  fi
  virtualenv --system-site-packages venv
  activate_virtualenv
}

function deactivate_virtualenv {
  deactivate
}

function remove_virtualenv {
  echo "--- removing virtual environment ---"
  rm -rf venv
}

function create_run_script {
  echo "#!/usr/bin/env bash

./venv/bin/python plugins/caleydo_server --multithreaded
" > run.sh
}

function manage_server {
  local cmd=${1:-stop}
  sudo supervisorctl ${cmd} caleydo_web
}

function run_custom_setup_scripts {
  local cmd=${1:-setup}
  for script in setup_*.sh ; do
    echo "--- run setup script: ${script}"
    #chmod +x ./${script}
    ( exec ./${script} ${cmd})
  done
}

function setup {
  echo "setup"
  install_common_apt_dependencies
  install_apt_dependencies
  install_common_yum_dependencies
  install_yum_dependencies

  create_virtualenv
  install_pip_dependencies
  create_run_script

  name=${PWD##*/}
  create_server_config ${name}
  register_as_service ${name}

  deactivate_virtualenv

  run_custom_setup_scripts setup
}

function setup_docker {
  #more fine granular for docker layers
  local cmd=${1:-all}
  case "$1" in
  common)
    install_common_apt_dependencies
    create_run_script
    create_virtualenv
    ;;
  config)
    name=${PWD##*/}
    activate_virtualenv
    create_server_config ${name}
    #register_as_service ${name}
    ;;
  apt)
    install_apt_dependencies
    ;;
  pip)
    activate_virtualenv
    install_pip_dependencies
    deactivate_virtualenv
    ;;
  custom)
    run_custom_setup_scripts setup
    ;;
  *)
    echo "setup_docker"
    install_common_apt_dependencies
    install_apt_dependencies

    create_run_script

    create_virtualenv

    name=${PWD##*/}
    create_server_config ${name}
    #register_as_service ${name}

    install_pip_dependencies

    deactivate_virtualenv

    run_custom_setup_scripts setup
    ;;
  esac

}

function pre_update {
  echo "pre update"
  rm -rf libs plugins scripts static setup_*.sh
}

function update {
  echo "update"

  manage_server stop

  install_common_apt_dependencies
  install_apt_dependencies
  install_common_yum_dependencies
  install_yum_dependencies

  activate_virtualenv
  install_pip_dependencies
  deactivate_virtualenv

  run_custom_setup_scripts update

  manage_server start
}

function uninstall {
  echo "uninstall"
  manage_server stop

  run_custom_setup_scripts uninstall

  name=${PWD##*/}
  remove_server_config ${name}
  unregister_from_service ${name}

  remove_virtualenv
}

function create_config {
  name=${PWD##*/}
  create_server_config ${name}
}

#command switch
case "$1" in
docker)
  shift
  setup_docker $@
  ;;
pre_update)
  shift
  pre_update $@
  ;;
update)
  shift
  update $@
  ;;
create_config)
  cshift
  reate_config $@
  ;;
uninstall)
  shift
  uninstall $@
  ;;
start|restart|stop)
  manage_server $1
  ;;
*)
  setup
  ;;
esac
