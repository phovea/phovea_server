FROM python:2.7

MAINTAINER Samuel Gratzl <samuel.gratzl@datavisyn.io>
WORKDIR /phovea
RUN printf "from phovea_server import launch\nlaunch.run()\n" > /phovea/launch.py

RUN apt-get update

# install dependencies last step such that everything before can be cached
COPY requirements*.txt docker_packages.txt ./
RUN (!(test -f docker_packages.txt) || (cat docker_packages.txt | xargs apt-get install -y)) && pip install --no-cache-dir -r requirements.txt

COPY ./build/source ./

ENV PHOVEA_ENV=production
ENV PHOVEA_SERVICE=api
CMD python launch.py --env ${PHOVEA_ENV} ${PHOVEA_SERVICE}
EXPOSE 80
