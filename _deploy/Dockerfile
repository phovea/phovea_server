FROM ubuntu:trusty
MAINTAINER Samuel Gratzl <samuel-gratzl@gmx.at>

RUN apt-get update

#try to do common things
COPY ./setup.sh /var/www/caleydo_web/
COPY ./run.sh /var/www/caleydo_web/
WORKDIR /var/www/caleydo_web/
RUN chmod +x setup.sh
RUN ./setup.sh docker common
COPY ./gunicorn_start.in.sh /var/www/caleydo_web/
RUN ./setup.sh docker config

COPY . /var/www/caleydo_web/
RUN chmod +x setup.sh
#split in multiple steps for better layers
RUN ./setup.sh docker apt
RUN ./setup.sh docker pip
RUN ./setup.sh docker custom

EXPOSE 9000
CMD ["./start_caleydo.sh"]
