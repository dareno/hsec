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

#COPY .ssh/authorized_keys /root/.ssh/authorized_keys
#COPY .ssh/known_hosts     /root/.ssh/known_hosts
#COPY .ssh/id_rsa          /root/.ssh/id_rsa

ENV app hsec-state
ENV PYTHONPATH $PYTHONPATH:/

#ADD ${app} ${app}
#WORKDIR /${app}/${app}
#ENTRYPOINT ["/${app}/${app}/${app}.py"]
ENTRYPOINT ["/bin/bash"]
#CMD [""]

