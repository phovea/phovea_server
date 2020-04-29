FROM python:3.7-buster
LABEL maintainer="contact@caleydo.org"

WORKDIR /phovea

ENV PHOVEA_ENV=production
ENV PHOVEA_SERVICE=api
ENV PHOVEA_CONFIG_PATH=config.json

RUN printf "deb http://deb.debian.org/debian/ buster main\ndeb-src http://deb.debian.org/debian/ buster main\ndeb http://deb.debian.org/debian-security/ buster/updates main\ndeb-src http://deb.debian.org/debian-security/ buster/updates main" > /etc/apt/sources.list
# install dependencies last step such that everything before can be cached
COPY requirements*.txt docker_packages.txt docker_script*.sh _docker_data* /tmp/
RUN (!(test -s /tmp/docker_packages.txt) || (apt-get update && \
    (cat /tmp/docker_packages.txt | xargs apt-get install -y))) && \
    (pip install --no-cache-dir -r /tmp/requirements.txt)
RUN (!(test -s /tmp/docker_script.sh) || (bash /tmp/docker_script.sh))


COPY ./build/source ./

# establish the runtime user
RUN useradd -l -M -U -s /bin/bash phovea && \
    chown -R phovea:phovea /phovea
USER phovea

# Create separate launch file (similar to phovea_server/__main__.py from repository root), because it is not included in build files
RUN printf "from phovea_server import launch\nlaunch.run()\n" > /phovea/launch.py

EXPOSE 9000
CMD python launch.py --env ${PHOVEA_ENV} ${PHOVEA_SERVICE}
