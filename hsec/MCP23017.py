#!/usr/bin/env python3.4

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

import smbus
import logging
log = logging.getLogger('hsec')

class Pin:
    
    def __init__(self, name, description=None):
        """
        To be initialized by a port which will know it's own name. Something like:
            <from port>
            self.pin( "GPA0", "Front Door")
            Refactor: Pins are not only for reed sensors. Take closed out of here and make it 
            a child class.
        """
        self.name = name
        self.description = description
        if self.description is None:
            self.enabled = False
        else:
            self.enabled = True
        self.closed = None # default to unknown state to ensure event creation 

    def print_self(self):
        if self.closed:
            print("%s:%s:%s:Closed" % (self.name, self.description, self.enabled))
        else:
            print("%s:%s:%s:Open" % (self.name, self.description, self.enabled))

    def set_enable(self,enable):
        self.enabled=enable
        return self

    def set_closed(self,closed):
        if self.closed != closed:
            if closed:
                print ("%s:%s is now closed" % ( self.name, self.description ))
            else:
                print ("%s:%s is now open" % ( self.name, self.description ))
        self.closed=closed
        return self

    def set_description(self,description):
        self.description = description
        return self

class Port:

    def __init__(self, bus, address, name, register_mapping, pullup_map):
        self.MAXPINS = 8
        self.BUS=bus
        self.DEVICE_ADDRESS=address
        self.name=name
        self.pins = []
        self.REGISTER = register_mapping
        self.PULLUP_MAP = pullup_map # some are done in hardware

        # create 8 pins which will be defined from main
        for x in range(0,self.MAXPINS):
            pin_name = self.name+str(x)
            self.pins.append(Pin(pin_name))

        # setup the pins for reading/input
        self.BUS.write_byte_data(self.DEVICE_ADDRESS, self.REGISTER['IODIR'], 0xFF) # 

        # Activate all internal pullup resistors
        self.BUS.write_byte_data(self.DEVICE_ADDRESS, self.REGISTER['GPPU'], self.PULLUP_MAP)

        # Activate Interrupt OnChange
        self.BUS.write_byte_data(self.DEVICE_ADDRESS, self.REGISTER['GPINTEN'], 0xFF)

        # Connect Interrupt-Pin with the other port (MIRROR)
        self.BUS.write_byte_data(self.DEVICE_ADDRESS, self.REGISTER['INTCON'], 0x40)


    def print_name(self):
        print ("port %s:" % self.name)

    def update_pin_enable_state(self):
        # Read GPIO-Byte from port
        # this line will reset the interrupt
        self.status_byte = self.BUS.read_byte_data(self.DEVICE_ADDRESS, self.REGISTER['GPIO'])
        #log.debug ("status byte: %s" % (format(self.status_byte,'08b')))
        # 1 means open, 0 means closed
        for x in range(0,self.MAXPINS):
            if ((self.status_byte & 1) == 0):
                self.pins[x].set_closed(True)
                #log.debug ("closed")
            else:
                self.pins[x].set_closed(False)
                #log.debug ("open")
            self.status_byte = self.status_byte >> 1   # shift gpio on port right one bit in prep for next loop
        #log.debug ("status byte: %s" % (format(self.status_byte,'08b')))

    def print_self(self):
        self.update_pin_enable_state()
        print ("port %s, status byte:%s" % (self.name, self.status_byte))
        for x in range(0,self.MAXPINS):
            self.pins[x].print_self()




    def read_port(self):
        pass

class MCP23017:

    def __init__(self, busId, address):
        """
        The HW designer knows the bus and address of the chip. He also knows the GPIO pin used for 
        the interrupt. 
        """
        self.bus = smbus.SMBus(busId)  # 0 = /dev/i2c-0 (port I2C0), 1 = /dev/i2c-1 (port I2C1)
        self.address = address
        log.debug ("creating an MCP23017 chip at bus %s address 0x%s" % (busId, format(address,'02x')))

        self.REGISTER_MAPPING = { 
            'A' : {
                'IODIR': 0X00,
                'IPOL': 0X02,
                'GPINTEN': 0X04,
                'DEFVAL': 0X06,
                'INTCON': 0X08,
                'IOCON': 0X0A,
                'GPPU': 0X0C,
                'INTF': 0X0E,
                'INTCAP': 0X10,
                'GPIO': 0X12,
                'OLAT': 0X14
              },
             'B': {
                'IODIR': 0X01,
                'IPOL': 0X03,
                'GPINTEN': 0X05,
                'DEFVAL': 0X07,
                'INTCON': 0X09,
                'IOCON': 0X0B,
                'GPPU': 0X0D,
                'INTF': 0X0F,
                'INTCAP': 0X11,
                'GPIO': 0X13,
                'OLAT': 0X15
              }
        }

        # setup port A, 0xFC means that the first two ports have HW pull up reistors
        self.portA = Port(self.bus, self.address, "GPA", self.REGISTER_MAPPING['A'], 0xFC)

        # setup port B, 0xFF means that none of the ports have HW pull up reistors
        self.portB = Port(self.bus, self.address, "GPB", self.REGISTER_MAPPING['B'], 0xFF)

    def print_self(self):
        print ("chip 0x%s:" % format(self.address,'02x'))
        self.portA.print_self();
        self.portB.print_self();

    def check_for_events(self):
        self.portA.update_pin_enable_state()
        self.portB.update_pin_enable_state()
