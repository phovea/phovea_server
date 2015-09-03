#!/usr/bin/env bash

function sedeasy {
  sed -i "s/$(echo $1 | sed -e 's/\([[\/.*]\|\]\)/\\&/g')/$(echo $2 | sed -e 's/[\/&]/\\&/g')/g" $3
}

function install_apt_dependencies {
  if [ -f debian.txt ] ; then
    echo "--- installing apt dependencies ---"
    wd="`pwd`"
    cd /tmp #switch to tmp directory
    set -vx #to turn echoing on and
    sudo apt-get install -y supervisor python-pip python-dev zlib1g-dev `cat ${wd}/debian.txt`
    set +vx #to turn them both off
    cd ${wd}
    rm debian.txt
  fi
}
function install_pip_dependencies {
  if [ -f requirements.txt ] ; then
    echo "--- installing pip dependencies ---"
    wd="`pwd`"
    cd /tmp #switch to tmp directory
    pip install -r ${wd}/requirements.txt
    set -vx #to turn echoing on and
    cd ${wd}
    rm requirements.txt
  fi
}

function create_server_config {
  local name=$1
  wd="`pwd`"
  cd /tmp #switch to tmp directory
  pip install gunicorn setproctitle
  set -vx #to turn echoing on and
  cd ${wd}

  cp gunicorn_start.in.sh gunicorn_start.sh
  sedeasy /var/www/caleydo_app ${wd} gunicorn_start.sh
  sedeasy caleydo_app ${name} gunicorn_start.sh
  chmod +x gunicorn_start.sh


  cp supervisor.in.conf supervisor.conf
  sedeasy /var/www/caleydo_app ${wd} supervisor.conf
  sedeasy caleydo_app ${name} supervisor.conf

  #create the supervisor config
  sudo ln -s ${wd}/supervisor.conf /etc/supervisor/conf.d/${name}.conf
  #reread the list of elements
  sudo supervisorctl reread
  sudo supervisorctl update

  #create the nginx config and enable the site
  if [ -d /etc/nginx ] ; then
    cp nginx.in.conf nginx.conf
    sedeasy /var/www/caleydo_app ${wd} nginx.conf
    sedeasy caleydo_app ${name} nginx.conf
    sudo ln -s ${wd}/nginx.conf /etc/nginx/sites-available/${name}
    sudo ln -s ${wd}/nginx.conf /etc/nginx/sites-enabled/${name}
    sudo service nginx restart
  fi
}

function activate_virtualenv {
  source venv/bin/activate
}

function create_virtualenv {
  echo "--- creating virtual environment ---"
  wd="`pwd`"
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

function create_run_script {
    echo "#!/usr/bin/env bash

./venv/bin/python plugins/caleydo_server --multithreaded
" > run.sh
}


#command switch
case "$1" in
update)
  install_apt_dependencies
  activate_virtualenv
  install_pip_dependencies
  deactivate_virtualenv
  ;;
create_config)
  name=${PWD##*/}
  create_server_config ${name}
  ;;
*)
  install_apt_dependencies
  create_virtualenv
  install_pip_dependencies
  create_run_script

  name=${PWD##*/}
  create_server_config ${name}

  deactivate_virtualenv
  ;;
esac