#!/usr/bin/env python3.4

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

import logging
import time
import RPi.GPIO as GPIO
from MCP23017 import MCP23017 #import my custom class
import channel

# need this so that the GPIO interrupt callback has access to the chip object
channelToChip = { 29 : None}


def configLogging():
    log = logging.getLogger('hsec')

    # has this already run? If so, don't add more handlers or you'll get duplicate logging
    if len(log.handlers):
        return

    # set level of output. DEBUG if in development.
    log.setLevel(logging.DEBUG)

    # create console handler and set level to debug
    ch = logging.StreamHandler()
    #ch.setLevel(logging.DEBUG)

    # create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # add formatter to ch
    ch.setFormatter(formatter)

    # add ch to logger
    log.addHandler(ch)


def interrupt_callback(channel):
    log = logging.getLogger('hsec')
    log.info("event detected")
    time.sleep(1) # give it a second
    channelToChip[29].check_for_events()
    channelToChip[29].print_self()
    # I think there's a race condition here where the interrupt may trigger after checking for
    # events but before exiting. In that case, the interrupt will stay high and there will not
    # be another rising edge. Would be nice to have an async call here...

def setup():

    # setup logging
    log = logging.getLogger('hsec')
    configLogging()
    

    # at this point, I know the hardware config and interrupt pins. I also know the sensor 
    # for each chip pin. I'll need a function for each interrupt ping that will look for
    # events and publish them. The event will be open/close on MCP.Pin.description.

    log.info("starting home security")
    chip1 = MCP23017(1,0x20)
    channelToChip[29] = chip1   # save this for interrupt_callback() to use

    # define pins
    chip1.portA.pins[0].set_description("Front Door").set_enable(True)
    chip1.portA.pins[1].set_description("Family Room PIR").set_enable(True)

    # print pin usage
    #chip1.portA.pins[0].print_self()
    #chip1.portA.pins[1].print_self()

    #chip1.print_self()

    # setup interrupt callback function
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(29,GPIO.IN,pull_up_down=GPIO.PUD_DOWN)
    #GPIO.add_event_detect(29,GPIO.RISING,callback=interrupt_callback,bouncetime=100)

    # GPIO5.Interrupt => chip1.lookForEvents()
    # chip1.showConfig() # print the pins with desc and the chip config.

    #channel = Channel()

    return chip1

def loop( chip1 ):
    log = logging.getLogger('hsec')
    try:
        # loop through logging calls to see the difference
        # new configurations make, until Ctrl+C is pressed
        while True:
            channel = GPIO.wait_for_edge(29, GPIO.RISING, timeout=5000)
            if channel is None:
                print('Timeout occurred')

                # manual check for interrupt in case missed by wait_for_edge
                # this doesn't work yet because I haven't changed check_for_events
                # to return a value
                #if chip1.check_for_events():
                    #log.warn('Events found after waiting_for_edge()=%s, race condition?')
            else:
                print('Edge detected on channel', channel)

                # this doesn't work yet because I haven't changed check_for_events
                # to return a value
                #if not chip1.check_for_events():
                    #log.warn('Events _not_ found after waiting_for_edge, race condition?')

            # either exited due to an event or timed out, look at the interrupt to see what happened
            chip1.check_for_events()
            
    except KeyboardInterrupt:
        # cleanup
        GPIO.cleanup()
        log.info("ending home security")
        log.shutdown()

if __name__ == '__main__':

    # setup returns a chip and passes it to loop.
    loop(setup())


