Description
-----------
Home security project. Raspberry Pi using MCP23017 and GPIO with interrupts. Currently re-writing from Python into Clojure.

The vision is to have an easy to maintain, home security system with no service fees. Maybe not super practical, but a fun exercise. Also, super-useful when done. 

The Hardware (humble beginnings...)
-----------------------------------
### Overview
Here's an overview shot in an amazing cardboard case...
![Raspberry Pi with MCP21017](https://github.com/dareno/hsec/blob/master/img/hardware.jpg "Raspberry Pi with MCP21017")

### Port Expander sub-module
Schematic and board exports for just the port expander module. There's a connector for 3.3V, GND, I2C and interrupt wires. These will connect to the appropriate RPi pins.
![Port Expander Schematic](https://github.com/dareno/hsec/blob/master/img/port%20expander%20submodle%20schematic.png "Port Expander Schematic")

I drew the blue "bottom" traces with the intent that I would use the through-hole, bare-wire leads to make those connections. The red "top" traces will be on the bottom too but with insulated wire to cross the bare, blue wires. J1 through J4 have extra room around them so that you can use any screw terminals. JP1 is a shrouded and keyed connector to prevent misconfiguration, but I left pin 10 free in case it got plugged in backwards somehow (don't want power applied to an unsuspecting pin).

![Port Expander Board](https://github.com/dareno/hsec/blob/master/img/port%20expander%20submodle%20board.png "Port Expander Board")

### Installed
Now installed in a case with sensors fed to the port expander.
![Installed](https://github.com/dareno/hsec/blob/master/img/overview.jpg "Installed")

Technology
----------
* Raspberry Pi because it's small, low power, and runs linux so I don't have to re-invent the wheel on a microcontroller.
* Clojure because it's more expressive
* MCP23017 because it's a cheap port expander and there are examples
* i2c bus for IC to IC communication because there are examples
* smbus standard over i2c because there are examples

Components
--------------
* sensor - notice sensor events and send to state
* state - receive sensor and control events (e.g. "arm the system"), update state and send changes to alert
* alert - route state changes through all the appropriate channels (e.g. iCloud, house klaxon)
* webui - web app for control (e.g. arm/disarm)

How To Use
----------
coming soon...
