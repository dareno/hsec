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

    # Prepare our context and publisher
    context    = zmq.Context()
    subscriber = context.socket(zmq.SUB)
    subscriber.connect("tcp://localhost:5563")
    subscriber.setsockopt(zmq.SUBSCRIBE, b"State")
    subscriber.setsockopt(zmq.SUBSCRIBE, b"Events")

    q = queue.Queue(maxsize=0)
    worker = Thread(target=recv_msg, args=(q,subscriber,))
    worker.setDaemon(True)
    worker.start()

    try:
        while True:
            # Read envelope and address from queue
            try:
                [address, contents] = q.get(False)
            except queue.Empty:
                time.sleep(0.1)
            else:
                q.task_done()
                print("[%s] %s" % (address, contents))

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
