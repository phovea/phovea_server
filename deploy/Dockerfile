FROM python:2.7

MAINTAINER Samuel Gratzl <samuel.gratzl@datavisyn.io>
WORKDIR /phovea

# create dirs and install supervisor
RUN mkdir -p /phovea/app /phovea/run && apt-get update && apt-get install -y supervisor
CMD ["supervisord", "-n"]

RUN pip install -U gunicorn
COPY ./deploy/gunicorn_config.py /phovea/
EXPOSE 80

COPY ./deploy/supervisord.conf /etc/supervisor/conf.d/phovea_service.conf

# install dependencies last step such that everything before can be cached
COPY requirements*.txt docker_packages.txt ./
RUN (!(test -f docker_packages.txt) || (cat docker_packages.txt | xargs apt-get install -y)) && pip install --no-cache-dir -r requirements.txt

COPY ./build/source ./app/