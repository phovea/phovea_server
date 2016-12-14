FROM python:2.7

MAINTAINER Samuel Gratzl <samuel.gratzl@datavisyn.io>

# install node
RUN curl -sL https://deb.nodesource.com/setup_6.x | bash -
RUN apt-get install -y nodejs

EXPOSE 9000
CMD ["python", "phovea_server", "--use_reloader", "--env", "dev"]

WORKDIR /phovea

# install dependencies last step such that everything before can be cached
COPY requirements*.txt docker_packages.txt ./
RUN pip install --no-cache-dir -r requirements.txt && (pip install --no-cache-dir -r requirements_dev.txt) && xargs -a <(awk '/^\s*[^#]/' docker_packages.txt) -r -- sudo apt-get install -y