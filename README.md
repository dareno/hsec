Description
-----------
Home security project. Raspberry Pi using MCP23017 and GPIO with interrupts. This project is implemented with microservices, this is the overview documentation which references the components sited below in the Architecture section. 

The vision is to have an easy to maintain, home security system with no service fees. Maybe not super practical, but a fun exercise. Also, super-useful when done. 

The Hardware (humble beginnings...)
-----------------------------------
### Overview
Here's an overview shot in an amazing cardboard case...
![Raspberry Pi with MCP21017](https://github.com/dareno/hsec/blob/master/img/hardware.jpg "Raspberry Pi with MCP21017")

### Port Expander sub-module
Schematic and board exports for just the port expander module. There's a connector for 3.3V, GND, I2C and interrupt wires. These will connect to the appropriate RPi pins.
![Port Expander Schematic](https://github.com/dareno/hsec/blob/master/img/port expander submodle schematic.png "Port Expander Schematic")

I drew the blue "bottom" traces with the intent that I would use the through-hole, bare-wire leads to make those connections. The red "top" traces will be on the bottom too but with insulated wire to cross the bare, blue wires. J1 through J4 have extra room around them so that you can use any screw terminals. JP1 is a shrouded and keyed connector to prevent misconfiguration, but I left pin 10 free in case it got plugged in backwards somehow (don't want power applied to an unsuspecting pin).

![Port Expander Board](https://github.com/dareno/hsec/blob/master/img/port expander submodle board.png "Port Expander Board")

### Installed
Now installed in a case with sensors fed to the port expander.
![Installed](https://github.com/dareno/hsec/blob/master/img/overview.jpg "Installed")


Technology
----------
* Raspberry Pi because it's small, low power, and runs linux so I don't have to re-invent the wheel on a microcontroller.
* Python for Raspberry Pi stuff because it's common in the ecosystem
* Python3 because it's new
* MCP23017 because it's a cheap port expander and there are examples
* i2c bus for IC to IC communication because there are examples
* smbus standard over i2c because there are examples
* RPi.GPIO because I can use it to process interrupts on the MCP23017
* zmq because I don't need a broker process making this lighter weight for a RPi. 

Architecture
------------
* hsec-trigger - notice sensor events and send to hsec-state
* hsec-state - receive sensor and control events (e.g. "arm the system"), update state and send changes to hsec-alert
* hsec-alert - route state changes through all the appropriate channels (e.g. iCloud, house klaxon)
* commchannel.py - encapsulate messaging technology (e.g. ZeroMQ)
* MCP23017.py - encapsulate i2c/smbus IC commands 


To Do
-----
* update main loop to use a distinct thread per device (only 1 device/MCP today)
* iPhone app to add reporting and state events (e.g. arm motion detectors, arm windows, arm doors)

How To Use
----------
```
####################
## RPi config
####################

#download raspbian minimal to your laptop and write image to sd card : 
https://www.raspberrypi.org/downloads/raspbian/
# sudo dd bs=1m if=path_of_your_image.img of=/dev/rdisk2 # DON'T COPY/PASTE, VERIFY TARGET DISK

# boot, able to ssh straight to RPi
# ssh pi@192.168.1.165 # check your router for IP address

# enlarge file system and enable i2c
sudo raspi-config

# ssh from pi to pi to create .ssh
ssh localhost

# setup passwordless login
scp /Users/david/.ssh/id_rsa.pub pi@192.168.1.165:/home/pi/.ssh/authorized_keys

# add set -o vi to end of profile
sudo vi /etc/profile 

# update raspbian
sudo apt-get -y update && sudo apt-get -y upgrade

# install screen and dev tools
sudo apt-get install -y screen \
  git \
  python3 \
  python3-pip \
  python3-zmq \
  python-dev \
  vim 


# setup docker host
sudo wget https://downloads.hypriot.com/docker-hypriot_1.10.3-1_armhf.deb
sudo dpkg -i docker-hypriot_1.10.3-1_armhf.deb
sudo systemctl enable docker # enable auto start of daemon
#sudo docker run armhf/debian /bin/echo 'Hello World'

# don't need this, just for troubleshooting...
# sudo apt-get -y install build-essential libi2c-dev i2c-tools python-dev libffi-dev module-init-tools

# get source for inclusion in docker containers
git config --global user.name  'dareno'
git config --global user.email 'dcreno@gmail.com'
git clone git@github.com:dareno/comms.git
git clone git@github.com:dareno/hsec-trigger.git 
git clone git@github.com:dareno/hsec-state.git
git clone git@github.com:dareno/hsec-alert.git
git clone git@github.com:dareno/hsec-webui.git

# done with Raspbian configuration, now launch the container and configure

####################
## Docker config
####################
# create an isolated docker network for peer-to-peer communication
# containers that join this network can find each other via DNS
sudo docker network create --driver bridge isolated_nw

# build the containers from the dockerfiles
sudo docker build -t alert -f alert.dockerfile . && sudo docker build -t state -f state.dockerfile . && sudo docker build -t trigger -f trig.dockerfile . && sudo docker build -t webui -f webui.dockerfile .

# run the containers attached interactively, with psuedo-terminals for debug. 

# Trigger needs special OS access
# thanks dummdida... http://dummdida.tumblr.com/post/117157045170/modprobe-in-a-docker-container
APP="trigger" bash -c 'sudo docker run -it --net isolated_nw -v /home/pi/hsec-${APP}:/hsec-${APP} --name ${APP}1 --hostname ${APP}1 --privileged --cap-add=ALL -v /dev:/dev -v /lib/modules:/lib/modules ${APP}'

# alert
APP="alert"   bash -c 'sudo docker run -it --net isolated_nw -v /home/pi/hsec-${APP}:/hsec-${APP} --name ${APP}1 --hostname ${APP}1 ${APP}'

# state
APP="state"   bash -c 'sudo docker run -it --net isolated_nw -v /home/pi/hsec-${APP}:/hsec-${APP} --name ${APP}1 --hostname ${APP}1 ${APP}'

# webui listens on port 5000: 
APP="webui"   bash -c 'sudo docker run -it --net isolated_nw -v /home/pi/hsec-${APP}:/hsec-${APP} --name ${APP}1 --hostname ${APP}1 -p 5000:5000 ${APP}'

# dev container with vim and other tools
APP="dev"   bash -c 'sudo docker run -it --net isolated_nw -v /home/pi/hsec-${APP}:/hsec-${APP} --name ${APP}1 --hostname ${APP}1 ${APP}'


############################################################
## Notes...
############################################################
# optional, verify RPi.GPIO
# python3
#>>> import sys
#>>> sys.path.append("/usr/local/lib/python3.4/dist-packages/")
#>>> import RPi.GPIO as GPIO
#>>> 

# create ~/.vimrc
syntax on
filetype indent plugin on
set modeline
```
