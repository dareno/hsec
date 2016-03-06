# hsec
Home security project. Raspberry Pi using MCP23017 and GPIO with interrupts.

python3 sensor using RPi.GPIO to sense interupts. Reading I2C bus using smbus to get reed sensor status from MCP23017. 

TODO:
Publish results over zmq, PUB to SUB
Consume results in microservice to decide actions (e.g. alarm, email)
Front end to add reporting and state events (e.g. arm motion detectors, arm windows, arm doors)
