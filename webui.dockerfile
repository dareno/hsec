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

RUN pip3 install \
	Flask 

COPY .ssh/authorized_keys /root/.ssh/authorized_keys
COPY .ssh/known_hosts     /root/.ssh/known_hosts
COPY .ssh/id_rsa          /root/.ssh/id_rsa

RUN git config --global user.name  'dareno'
RUN git config --global user.email 'dcreno@gmail.com'
WORKDIR /
RUN git clone git@github.com:dareno/comms.git
RUN git clone git@github.com:dareno/hsec-webui.git

ENV PYTHONPATH $PYTHONPATH:/

WORKDIR /hsec-webui/hsec-webui
#ENTRYPOINT ["/hsec-webui/hsec-webui/webui.py"]
ENTRYPOINT ["/usr/bin/python3"]
CMD ["/hsec-webui/hsec-webui/webui.py"]
#CMD [""]
