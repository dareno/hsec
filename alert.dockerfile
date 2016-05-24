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
        pyicloud 

COPY .ssh/authorized_keys /root/.ssh/authorized_keys
COPY .ssh/known_hosts     /root/.ssh/known_hosts
COPY .ssh/id_rsa          /root/.ssh/id_rsa
COPY keyring_pass.cfg     /root/.local/share/python_keyring/keyring_pass.cfg
COPY dcrenogmailcom       /tmp/pyicloud/dcrenogmailcom

RUN git config --global user.name  'dareno'
RUN git config --global user.email 'dcreno@gmail.com'
WORKDIR /
RUN git clone git@github.com:dareno/comms.git
ENV UPDATED 24May2016a
RUN git clone git@github.com:dareno/hsec-alert.git

ENV PYTHONPATH $PYTHONPATH:/
ENV ICLOUD_ALERT_ACCOUNT 'dcreno@gmail.com'
ENV ICLOUD_ALERT_DEVICE_ID_LIST "['bWDeAzn7SXb8FBu3xi9yUy7xc8k6ox0UwJLl022ihalCuJ9hRhhcReHYVNSUzmWV']"

WORKDIR /hsec-alert/hsec-alert
ENTRYPOINT ["/hsec-alert/hsec-alert/hsec-alert.py"]
#CMD [""]
