#!/usr/bin/env python3.4
"""
Receive events, decide what to do. Based on zguide.
"""
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

import requests             # for webhooks
import configparser         # for reading config
import time
import comms.comms as comms # for getting a channel to the sensor


def main():
    """ main method """

    # get key for ifttt maker recipe
    config = configparser.ConfigParser()
    config.read('actor.cfg')
    key=config['maker.ifttt.com']['Key']

    # create object for communication to sensor system
    comm_channel = comms.SubChannel("tcp://localhost:5563", ['events','state'])

    try:
        while True:
            # Read envelope and address from queue
            rv = comm_channel.get()
            if rv is not None:
                [address, contents] = rv
                print("[%s] %s" % (address, contents))
                post = "https://maker.ifttt.com/trigger/front_door_opened/with/key/" + key
                print(post)
                #print(requests.post(post))
            else:
                time.sleep(0.1)
            print("doing stuff")
            time.sleep(1)
            # trigger an event

    except KeyboardInterrupt:
        q.join(timeout=1)

    # clean up zmq connection
    subscriber.close()
    context.term()

if __name__ == "__main__":
    main()
