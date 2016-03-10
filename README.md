Description
-----------
Home security project. Raspberry Pi using MCP23017 and GPIO with interrupts.

The vision is to have a microservice architecture, home security system with no service fees. Maybe not super practical, but a fun exercise. Also, super-useful when done. 

The Hardware (humble beginnings...)
-----------------------------------
<img src="https://github.com/dareno/hsec/blob/master/img/hardware.jpg" alt="Raspberry Pi with MCP21017" width="153">

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
* hsec.py - look for events on the hardware and share them
* actor.py - listen for reported events, do something. (e.g. call my phone)


To Do
-----
* finish config from configfile instead of hard-coded chip config
* iPhone app to add reporting and state events (e.g. arm motion detectors, arm windows, arm doors)


