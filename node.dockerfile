FROM armhf/debian

MAINTAINER David Reno

RUN apt-get update && apt-get -y install \
	build-essential \
	libzmq3-dbg \
	libzmq3-dev \
	libzmq3 \
	curl

RUN curl -sL https://deb.nodesource.com/setup_6.x | bash -
RUN apt-get update && apt-get -y install \
	nodejs 
	#npm

#ADD node_latest_armhf.deb node_latest_armhf.deb 
#RUN dpkg -i node_latest_armhf.deb

WORKDIR /
ADD comms comms
ENV app hsec-node
#ADD ${app} ${app}
#WORKDIR /${app}/${app}

# Upgrade node and npm to latest version
#RUN     npm cache clean
#RUN     npm install -g n
#RUN     n stable
#RUN     curl -L https://npmjs.org/install.sh | sh

#RUN npm init --y 
#RUN npm install basic-auth


#RUN 	npm install -g npm@latest
RUN	npm cache clean
RUN	npm init --y
RUN	npm install basic-auth
RUN	npm install zmq


#ENTRYPOINT ["/${app}/${app}/${app}.py"]
#RUN npm install zmq
ENTRYPOINT ["/bin/bash"]
#CMD [""]
