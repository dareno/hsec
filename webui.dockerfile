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

ENV app hsec-webui
ENV PYTHONPATH $PYTHONPATH:/

RUN pip3 install \
	Flask 

ENV app hsec-webui
ENV PYTHONPATH $PYTHONPATH:/

#ADD ${app} ${app}
#WORKDIR /${app}/${app}
#ENTRYPOINT ["/${app}/${app}/${app}.py"]
ENTRYPOINT ["/bin/bash"]
#CMD [""]
