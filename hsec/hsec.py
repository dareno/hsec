#!/usr/bin/env python3.4

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

import logging
import channel
import time
from MCP23017 import MCP23017 #import my custom class


def configLogging():
    log = logging.getLogger('hsec')
    log.setLevel(logging.DEBUG)

    # create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    # create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # add formatter to ch
    ch.setFormatter(formatter)

    # add ch to logger
    log.addHandler(ch)

def main():

    # setup logging
    log = logging.getLogger('hsec')
    configLogging()
    

    # at this point, I know the hardware config and interrupt pins. I also know the sensor 
    # for each chip pin. I'll need a function for each interrupt ping that will look for
    # events and publish them. The event will be open/close on MCP.Pin.description.

    log.info("starting home security")
    chip1 = MCP23017(1,0x20)

    # define pins
    chip1.portA.pins[0].set_description("Front Door").set_enable(True)
    chip1.portA.pins[1].set_description("Family Room PIR").set_enable(True)

    # print pin usage
    #chip1.portA.pins[0].print_self()
    #chip1.portA.pins[1].print_self()

    chip1.print_self()

    # GPIO5.Interrupt => chip1.lookForEvents()
    # chip1.showConfig() # print the pins with desc and the chip config.

    #channel = Channel()

    while True:
        chip1.check_for_events()
        time.sleep(0.10)
        break


    log.info("ending home security")



if __name__ == '__main__':
    main()
