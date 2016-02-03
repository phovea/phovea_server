#!/bin/bash

NAME="caleydo_app"                                  # Name of the application
WEB_DIR=/var/www/caleydo_app             # Django project directory
USER=`whoami`             # the user to run as
PORT=9000
BIND_PORT=0.0.0.0:${PORT}
BIND=${BIND_PORT}

SOCKFILE=/var/www/caleydo_app/run/gunicorn.sock  # we will communicate using this unix socket
#BIND=unix:${SOCKFILE}

GROUP=data-www                                     # the group to run as
NUM_WORKERS=3                                     # how many worker processes should Gunicorn spawn
CALEYDO_WSGI_MODULE=wsgi                     # WSGI module name

echo "Starting $NAME as `whoami`"

# Activate the virtual environment
cd ${WEB_DIR}

VENV_NAME=venv

#virtualenv variant
ENV_DIR=./${VENV_NAME}
ENV_ACTIVATE=./${VENV_NAME}/bin/activate

#conda variant
#ENV_DIR=~/anaconda2/envs/${VENV_NAME}
#ENV_ACTIVATE=activate ${VENV_NAME}

source ${ENV_ACTIVATE}

# Create the run directory if it doesn't exist
RUNDIR=$(dirname ${SOCKFILE})
test -d ${RUNDIR} || mkdir -p ${RUNDIR}

# Start your Django Unicorn
# Programs meant to be run under supervisor should not daemonize themselves (do not use --daemon)
#--group=${GROUP}

exec ${ENV_DIR}/bin/gunicorn ${CALEYDO_WSGI_MODULE}:application \
  -k flask_sockets.worker \
  --name ${NAME} \
  --workers ${NUM_WORKERS} \
  --user=${USER} \
  --bind=${BIND} \
  --log-level=info \
  --log-file=-
