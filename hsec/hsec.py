#!/usr/bin/env python3.4

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

import logging
import time
import RPi.GPIO as GPIO
from MCP23017 import MCP23017 #import my custom class
import datetime

def configLogging():
    log = logging.getLogger('hsec')

    # has this already run? If so, don't add more handlers or you'll get duplicate logging
    if len(log.handlers):
        return

    # set level of output. DEBUG if in development.
    log.setLevel(logging.INFO)

    # create console handler and set level to debug
    ch = logging.StreamHandler()
    #ch.setLevel(logging.DEBUG)

    # create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # add formatter to ch
    ch.setFormatter(formatter)

    # add ch to logger
    log.addHandler(ch)

def setup():

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

    # setup interrupt callback function
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(29,GPIO.IN,pull_up_down=GPIO.PUD_DOWN)
    #GPIO.add_event_detect(29,GPIO.RISING,callback=interrupt_callback,bouncetime=100)

    return chip1

def loop( chip1 ):
    log = logging.getLogger('hsec')
    try:
        # loop through logging calls to see the difference
        # new configurations make, until Ctrl+C is pressed

        # initialize channel because GPIO.wait_for_edge seems to return None
        # until a valid channel is detected and then 0 afterwards.
        channel=0
        while True:

            # print any events
            events = chip1.get_events()
            if len(events)>0:
                print(datetime.datetime.now().time()," ", events)

            channel = GPIO.wait_for_edge(29, GPIO.RISING, timeout=1)
            #print("wait_for_edge()=", channel)

            
    except KeyboardInterrupt:
        # cleanup
        GPIO.cleanup()
        log.info("ending home security")
        log.shutdown()

if __name__ == '__main__':

    # setup returns a chip and passes it to loop.
    loop(setup())


