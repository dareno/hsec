#!/usr/bin/env python3.4
"""
This class is responsible for sending messages about changing events.
"""
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

import datetime
import time
import zmq
import json

class CommChannel:
    """
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
        self.publisher.send_multipart([b"State",b"some state"])

