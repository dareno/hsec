#!/usr/bin/env python3.4
"""
Receive events, decide what to do. Based on zguide.
"""
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

import zmq
import requests
import configparser
import queue
from threading import Thread
import time
import commchannel

def recv_msg(q, subscriber):
    """
    Block until messages are received, put them in the queue
    """

    while True:
        # get the envelope and message, put it on the shared queue
        [address, contents] = subscriber.recv_multipart()
        q.put([address,contents])
        # unlock the queue for others to read from
        #q.task_done()


def main():
    """ main method """

    # get key for ifttt maker recipe
    config = configparser.ConfigParser()
    config.read('actor.cfg')
    key=config['maker.ifttt.com']['Key']

    # create object for communication to sensor system
    comm_channel = commchannel.ActChannel()

    try:
        while True:
            # Read envelope and address from queue
            rv = comm_channel.get()
            if rv is not None:
                [address, contents] = rv
                print("[%s] %s" % (address, contents))
            else:
                time.sleep(0.1)
            print("doing stuff")
            time.sleep(1)
            # trigger an event
            #post = "https://maker.ifttt.com/trigger/front_door_opened/with/key/" + key
            #print(post)
            #print(requests.post(post))

    except KeyboardInterrupt:
        q.join(timeout=1)

    # clean up zmq connection
    subscriber.close()
    context.term()

if __name__ == "__main__":
    main()
