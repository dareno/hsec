FROM armhf/debian

MAINTAINER David Reno

RUN apt-get update && apt-get -y install \
	build-essential \
	git \
	python-dev \
	python3 \
	python3-pip \
	python3-zmq \
	vim 

COPY .ssh/authorized_keys /root/.ssh/authorized_keys
COPY .ssh/known_hosts     /root/.ssh/known_hosts
COPY .ssh/id_rsa          /root/.ssh/id_rsa

RUN git config --global user.name  'dareno'
RUN git config --global user.email 'dcreno@gmail.com'
WORKDIR /app
RUN git clone git@github.com:dareno/comms.git
ENV UPDATED 24May2016
RUN git clone git@github.com:dareno/hsec-state.git

ENV PYTHONPATH $PYTHONPATH:/app/

WORKDIR /app/hsec-state/hsec-state
ENTRYPOINT ["/app/hsec-state/hsec-state/hsec-state.py"]
CMD [""]
