FROM armhf/debian

MAINTAINER David Reno

RUN apt-get update && apt-get -y install \
	build-essential \
	git \
	i2c-tools \
	libffi-dev \
	libi2c-dev \
	python-dev \
	python3 \
	python3-pip \
	python3-zmq \
	vim 

RUN pip3 install \
	cffi \
	smbus-cffi \
	RPi.GPIO 

COPY .ssh/authorized_keys /root/.ssh/authorized_keys
COPY .ssh/known_hosts     /root/.ssh/known_hosts
COPY .ssh/id_rsa          /root/.ssh/id_rsa

RUN git config --global user.name  'dareno'
RUN git config --global user.email 'dcreno@gmail.com'
WORKDIR /app
RUN git clone git@github.com:dareno/comms.git
ENV UPDATED 24May2016a
RUN git clone git@github.com:dareno/hsec-trigger.git 

ENV PYTHONPATH $PYTHONPATH:/app/

WORKDIR /app/hsec-trigger/hsec-trigger
ENTRYPOINT ["/app/hsec-trigger/hsec-trigger/hsec-trigger.py"]
CMD [""]
