;; All things specific to the mcp23017 chip. If you have to read the datasheet
;; or access the chip, it goes in this file. All else, no!
;; Datasheet: https://www.microchip.com/wwwproducts/en/MCP23017
;; The Microchip MCP23017 has 16-bit I/O port functionality via
;; two 8-bit ports (PORTA and PORTB). This should not be confused
;; with addressing modes BANK=0 or BANK=1.

(ns hsec.source.mcp23017
  (:require [dvlopt.linux.i2c       :as i2c]
            [dvlopt.linux.i2c.smbus :as smbus]))

(def registers
  {  ;; BANK=0 addressing (registers paired)
   :a  { ;; 'a' register, first 8 IO bits
        :iodir 0x00
        :ipol 0x02
        :gpinten 0x04
        :defval 0x06
        :intcon 0x08
        :iocon 0x0a
        :gppu 0x0c
        :intf 0x0e
        :intcap 0x10
        :gpio 0x12
        :olat 0x14
        }
   :b { ;; 'b' register, second 8 IO bits
       :iodir 0x01
       :ipol 0x03
       :gpinten 0x05
       :defval 0x07
       :intcon 0x09
       :iocon 0x0b
       :gppu 0x0d
       :intf 0x0f
       :intcap 0x11
       :gpio 0x13
       :olat 0x15
       }
   })

(def iocon-settings
  [
   0 ;; BANK: Controls how the registers are addressed
   ;; 1 = The registers associated with each port are separated into different
   ;;     banks.
   ;; 0 = The registers are in the same bank (addresses are sequential).

   1 ;; MIRROR: INT Pins Mirror bit
   ;; 1 = The INT pins are internally connected
   ;; 0 = The INT pins are not connected. INTA is associated with PORTA and INTB
   ;;     is associated with PORTB

   0 ;; SEQOP: Sequential Operation mode bit
   ;; 1 = Sequential operation disabled, address pointer does not increment.
   ;; 0 = Sequential operation enabled, address pointer increments.

   0 ;; DISSLW: Slew Rate control bit for SDA output
   ;; 1 = Slew rate disabled
   ;; 0 = Slew rate enabled

   0 ;; HAEN: Hardware Address Enable bit (MCP23S17 only) (Note 1)
   ;; 1 = Enables the MCP23S17 address pins.
   ;; 0 = Disables the MCP23S17 address pins.

   0 ;; ODR: Configures the INT pin as an open-drain output
   ;; 1 = Open-drain output (overrides the INTPOL bit.)
   ;; 0 = Active driver output (INTPOL bit sets the polarity.)

   1 ;; INTPOL: This bit sets the polarity of the INT output pin
   ;; 1 = Active-high
   ;; 0 = Active-low

   0 ;; Unimplemented: Read as ‘0’
])

(defn get-register
  "return the byte contents of a register"
  [bus port register]
  (let [address (get-in registers [port register])]
    (smbus/read-byte bus address)))

(comment ;; test get-register
  (def port :a)
  (def register :intf)
  (def address 14)
  )

(defn get-registers
  "return the byte contents of both :a and :b registers"
  [bus register
   ;; deserializer
   ]
  {:a (get-register bus :a register)
   :b (get-register bus :b register)
   ;; refactoring to remove the  deserialization part
   ;; (let [bank-a-integer (get-register bus :a register)
   ;;       bank-b-integer (get-register bus :b register)]
   ;;   {:a bank-a-integer
   ;;    {:value bank-a-integer :deserialized (deserializer bank-a-integer)}
   ;;    :b bank-b-integer
   ;;    {:value bank-b-integer :deserialized (deserializer bank-b-integer)}})
   })

(comment ;; test get-registers
  (def register :gpio)
  (def bank-a-integer (get-register bus :a :gpio))
  (deserialize-gpio-integer (get-register bus :a :gpio))
  (deserialize-interrupt-integer (get-register bus :a :intf))
  )

(defn setup-chip
  "Given a bus path and slave address:
  mirror interrupts and enable interrupt on change for all pins.
  Return the bus object for commands. The bus must be closed during shutdown."
  [bus-string slave-address]
  (let [bus (i2c/bus bus-string)]

    ;; this bus will always use the selected slave address for commands
    (i2c/select-slave bus slave-address)

    ;; setup the chip with settings defined above in the iocon-settings object
    ;; in particular, the interrupt pins should be mirrored and driven high
    ;; when there's an interrupt.
    (smbus/write-byte bus
                      (get-in registers [:a :iocon])
                      (Integer/parseInt (apply str iocon-settings) 2))

    ;; enable int on all pins
    ;; (smbus/write-byte bus (get-in mcp23017/register [:a :gpinten]) 0x04)
    (smbus/write-byte bus (get-in registers [:a :gpinten]) 0xff)
    (smbus/write-byte bus (get-in registers [:b :gpinten]) 0xff)
    ;; return the bus object for future reads/writes; must be closed later
    bus))

(defn shutdown-chip
  "prepare to cleanly exit"
  [bus]
  (i2c/close bus))
