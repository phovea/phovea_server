FROM skiftcreative/supervisor:2.7

MAINTAINER Samuel Gratzl <samuel.gratzl@datavisyn.io>

RUN mkdir -p /phovea/app /phovea/run
WORKDIR /phovea

COPY ./deploy/supervisord.conf /etc/supervisor/conf.d/phovea_service.conf
COPY ./deploy/gunicorn_config.py ./

# install dependencies last step such that everything before can be cached
COPY requirements*.txt docker_packages.txt ./
RUN (!(test -f docker_packages.txt) || (cat docker_packages.txt | xargs apt-get install -y)) && pip install --no-cache-dir -r requirements.txt

COPY . ./app/
EXPOSE 9000
