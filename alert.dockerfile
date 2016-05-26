FROM armhf/debian

MAINTAINER David Reno

RUN apt-get update && apt-get -y install \
	#build-essential \
	#git \
	#python-dev \
	#python3 \
	python3-pip \
	python3-zmq 
	#vim 

WORKDIR /
ADD comms comms

RUN pip3 install \
        pyicloud 

COPY keyring_pass.cfg     /root/.local/share/python_keyring/keyring_pass.cfg
COPY dcrenogmailcom       /tmp/pyicloud/dcrenogmailcom

ENV app hsec-alert
ENV PYTHONPATH $PYTHONPATH:/
ENV ICLOUD_ALERT_ACCOUNT 'dcreno@gmail.com'
ENV ICLOUD_ALERT_DEVICE_ID_LIST "['bWDeAzn7SXb8FBu3xi9yUy7xc8k6ox0UwJLl022ihalCuJ9hRhhcReHYVNSUzmWV']"

#ADD ${app} ${app}
#WORKDIR /${app}/${app}
#ENTRYPOINT ["/${app}/${app}/${app}.py"]
ENTRYPOINT ["/bin/bash"]
#CMD [""]
