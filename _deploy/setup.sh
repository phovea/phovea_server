#!/usr/bin/env bash

#search for the right parent directory such that we have a common start directory
while [[ ! -f "run.sh" ]] && [[ ! -f "Vagrantfile" ]]
do
  cd ..
done

basedir=`pwd`

function sedeasy {
  sed -i "s/$(echo $1 | sed -e 's/\([[\/.*]\|\]\)/\\&/g')/$(echo $2 | sed -e 's/[\/&]/\\&/g')/g" $3
}

function install_apt_dependencies {
  if [ -f debian.txt ] ; then
    echo "--- installing apt dependencies ---"
    cd /tmp #switch to tmp directory
    set -vx #to turn echoing on and
    sudo apt-get install -y supervisor python-pip python-dev zlib1g-dev `cat ${basedir}/debian.txt`
    set +vx #to turn them both off
    cd ${basedir}
    rm debian.txt
  fi
}
function install_pip_dependencies {
  if [ -f requirements.txt ] ; then
    echo "--- installing pip dependencies ---"
    cd /tmp #switch to tmp directory
    pip install -r ${basedir}/requirements.txt
    set -vx #to turn echoing on and
    cd ${basedir}
    rm requirements.txt
  fi
}

function create_server_config {
  local name=$1
  cd /tmp #switch to tmp directory
  pip install gunicorn setproctitle
  set -vx #to turn echoing on and
  cd ${basedir}

  cp gunicorn_start.in.sh gunicorn_start.sh
  sedeasy /var/www/caleydo_app ${basedir} gunicorn_start.sh
  sedeasy caleydo_app ${name} gunicorn_start.sh
  chmod +x gunicorn_start.sh


  cp supervisor.in.conf supervisor.conf
  sedeasy /var/www/caleydo_app ${basedir} supervisor.conf
  sedeasy caleydo_app ${name} supervisor.conf

  #create the supervisor config
  sudo ln -s ${basedir}/supervisor.conf /etc/supervisor/conf.d/${name}.conf
  #reread the list of elements
  sudo supervisorctl reread
  sudo supervisorctl update

  #create the nginx config and enable the site
  if [ -d /etc/nginx ] ; then
    cp nginx.in.conf nginx.conf
    sedeasy /var/www/caleydo_app ${basedir} nginx.conf
    sedeasy caleydo_app ${name} nginx.conf
    sudo ln -s ${basedir}/nginx.conf /etc/nginx/sites-available/${name}
    sudo ln -s ${basedir}/nginx.conf /etc/nginx/sites-enabled/${name}
    sudo service nginx restart
  fi
}

function remove_server_config {
  local name=$1
  sudo rm /etc/supervisor/conf.d/${name}.conf
  #reread the list of elements
  sudo supervisorctl reread
  sudo supervisorctl update

  #remove the nginx config and disable the site
  if [ -d /etc/nginx ] ; then
    sudo service nginx stop
    sudo rm /etc/nginx/sites-available/${name}
    sudo rm /etc/nginx/sites-enabled/${name}
    sudo service nginx start
  fi
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
  sudo supervisorctl caleydo_web ${stop}
}

function setup {
  echo "setup"
  install_apt_dependencies
  create_virtualenv
  install_pip_dependencies
  create_run_script

  name=${PWD##*/}
  create_server_config ${name}

  deactivate_virtualenv
}

function update {
  echo "update"

  manage_server stop

  install_apt_dependencies
  activate_virtualenv
  install_pip_dependencies
  deactivate_virtualenv

  manage_server start
}

function uninstall {
  echo "uninstall"
  manage_server stop

  name=${PWD##*/}
  remove_server_config ${name}

  remove_virtualenv
}

function create_config {
  name=${PWD##*/}
  create_server_config ${name}
}

#command switch
case "$1" in
update)
  update
  ;;
create_config)
  create_config
  ;;
uninstall)
  uninstall
  ;;
*)
  setup
  ;;
esac