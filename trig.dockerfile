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

RUN apt-get update && apt-get -y install \
	#build-essential \
	#git \
	i2c-tools \
	libffi-dev \
	libi2c-dev 
	#python-dev \
	#python3 \
	#python3-pip \
	#python3-zmq \
	#vim 

RUN pip3 install \
	cffi \
	smbus-cffi \
	RPi.GPIO 

ENV app hsec-trig
ENV PYTHONPATH $PYTHONPATH:/

#ADD ${app} ${app}
#WORKDIR /${app}/${app}
#ENTRYPOINT ["/${app}/${app}/${app}.py"]
ENTRYPOINT ["/bin/bash"]
#CMD [""]


