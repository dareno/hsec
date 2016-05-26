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

WORKDIR /

COPY .ssh/authorized_keys /root/.ssh/authorized_keys
COPY .ssh/known_hosts     /root/.ssh/known_hosts
COPY .ssh/id_rsa          /root/.ssh/id_rsa
COPY vimrc                /root/.vimrc

RUN git config --global user.name  'dareno'
RUN git config --global user.email 'dcreno@gmail.com'

RUN echo "set -o vi" >> /.bashrc
RUN echo "set editing-mode vi" >> /etc/inputrc

ENV app dev
ENV PYTHONPATH $PYTHONPATH:/

ENTRYPOINT ["/bin/bash"]
