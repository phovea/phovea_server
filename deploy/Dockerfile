FROM python:2.7

MAINTAINER Samuel Gratzl <samuel.gratzl@datavisyn.io>
WORKDIR /phovea

RUN apt-get update

# install dependencies last step such that everything before can be cached
COPY requirements*.txt docker_packages.txt ./
RUN (!(test -f docker_packages.txt) || (cat docker_packages.txt | xargs apt-get install -y)) && pip install --no-cache-dir -r requirements.txt

COPY ./build/source ./phovea/

ARG env=production
CMD ["python", "phovea_server", "--env", $env, "api"]
EXPOSE 80