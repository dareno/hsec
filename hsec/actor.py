#!/usr/bin/env python3.4
"""
Receive events, decide what to do. Based on zguide.
"""
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

import zmq
import requests
import configparser

def main():
    """ main method """

    # Prepare our context and publisher
    context    = zmq.Context()
    subscriber = context.socket(zmq.SUB)
    subscriber.connect("tcp://localhost:5563")
    subscriber.setsockopt(zmq.SUBSCRIBE, b"State")
    subscriber.setsockopt(zmq.SUBSCRIBE, b"Events")

    config = configparser.ConfigParser()
    config.read('actor.cfg')
    #key = "something"
    key=config['maker.ifttt.com']['Key']

    while True:
        # Read envelope with address
        [address, contents] = subscriber.recv_multipart()
        #print("[%s] %s" % (address, contents))
        post = "https://maker.ifttt.com/trigger/front_door_opened/with/key/" + key
        print(post)
        print(requests.post(post))


    # We never get here but clean up anyhow
    subscriber.close()
    context.term()

if __name__ == "__main__":
    main()
