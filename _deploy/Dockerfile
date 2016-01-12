FROM ubuntu:trusty
MAINTAINER Samuel Gratzl <samuel-gratzl@gmx.at>

RUN apt-get update

COPY . /var/www/caleydo_web/
WORKDIR /var/www/caleydo_web/
RUN chmod +x setup.sh
RUN ./setup.sh docker

EXPOSE 9000
CMD ["./gunicorn_start.sh"]
