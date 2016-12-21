FROM skiftcreative/supervisor:2.7

MAINTAINER Samuel Gratzl <samuel.gratzl@datavisyn.io>
# add testing repository
RUN (echo -e "http://dl-cdn.alpinelinux.org/alpine/edge/main\nhttp://dl-cdn.alpinelinux.org/alpine/edge/community\nhttp://dl-cdn.alpinelinux.org/alpine/edge/testing" > /etc/apk/repositories) && apk update

WORKDIR /phovea

RUN mkdir -p /phovea/app /phovea/run

# install dependencies last step such that everything before can be cached
COPY requirements*.txt docker_packages.txt ./
RUN (!(test -f docker_packages.txt) || (cat docker_packages.txt | xargs apk add)) && pip install --no-cache-dir -r requirements.txt

COPY ./deploy/supervisord.conf /etc/supervisor/conf.d/phovea_service.conf
COPY ./build/source ./app/
