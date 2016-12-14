FROM python:2.7

MAINTAINER Samuel Gratzl <samuel.gratzl@datavisyn.io>

WORKDIR /phovea
# install dependencies
COPY requirements*.txt docker_packages.txt ./
RUN pip install --no-cache-dir -r requirements.txt && (pip install --no-cache-dir -r requirements_dev.txt) && xargs -a <(awk '/^\s*[^#]/' docker_packages.txt) -r -- sudo apt-get install -y

EXPOSE 9000
CMD ["python", "phovea_server", "--use_reloader", "--env", "dev"]