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

ENV app dev
RUN groupadd -g 2000 -r ${app} && useradd -u 2000 -rm -g ${app} ${app}
RUN echo "set editing-mode vi" >> /etc/inputrc
USER ${app}
COPY .ssh/authorized_keys /home/${app}/.ssh/authorized_keys
COPY .ssh/known_hosts     /home/${app}/.ssh/known_hosts
COPY .ssh/id_rsa          /home/${app}/.ssh/id_rsa
COPY hsec/vimrc           /home/${app}/.vimrc
COPY hsec.crt             /home/${app}/
COPY hsec.key             /home/${app}/

RUN git config --global user.name  'dareno'
RUN git config --global user.email 'dcreno@gmail.com'

RUN echo "set -o vi" >> /home/${app}/.bashrc

ENV PYTHONPATH $PYTHONPATH:/

ENTRYPOINT ["/bin/bash"]
