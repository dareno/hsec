#!/usr/bin/env python3.4
"""
This class is responsible for sending messages about changing events. 
ZMQ is the communication technology and is entirely abstracted by this class.

Should probably generalize the two classes to send and receive classes.
"""
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

import datetime
import time
import zmq
import json
import queue
from threading import Thread

class SenseChannel:
    """
    Only the sensor uses this class.
    Use a message queue technology to share events.
    Based on http://zguide.zeromq.org/py:psenvpub
    """

    def __init__(self):

        # prepare context and publisher
        self.context     = zmq.Context()
        self.publisher   = self.context.socket(zmq.PUB)
        self.publisher.bind("tcp://*:5563")

    def share_events(self, events):
        events_to_send = json.dumps(events)
        #print(datetime.datetime.now().time()," ", events_to_send)
        #print(events_to_send.encode('utf-8'))
        self.publisher.send_multipart([b"Events",events_to_send.encode('utf-8')])
        #self.publisher.send_multipart([b"State",b"some state"])

class ActChannel:
    """
    Only the actor uses this class.
    """

    def recv_msg(self):
        """
        Block until messages are received, put them in the queue
        """

        while True:
            # get the envelope and message, put it on the shared queue
            [address, contents] = self.subscriber.recv_multipart()
            self.q.put([address,contents])
            # unlock the queue for others to read from
            #q.task_done()


    def __init__(self):

        # Prepare our context and publisher
        self.context    = zmq.Context()
        self.subscriber = self.context.socket(zmq.SUB)
        self.subscriber.connect("tcp://localhost:5563")
        self.subscriber.setsockopt(zmq.SUBSCRIBE, b"State")
        self.subscriber.setsockopt(zmq.SUBSCRIBE, b"Events")

        self.q = queue.Queue(maxsize=0)
        self.worker = Thread( target=self.recv_msg )
        self.worker.setDaemon(True)
        self.worker.start()
    
    
        # clean up zmq connection
        #subscriber.close()
        #context.term()
    
    def get(self):
        # Read envelope and address from queue
        try:
            # get something off the queue, but don't wait for it
            [address, contents] = self.q.get(False)
        except queue.Empty:
            # raise an exception?
            time.sleep(.1)
            return None
            #time.sleep(0.1)
        else:
            self.q.task_done()
            #print("[%s] %s" % (address, contents))
            return [address,contents]

