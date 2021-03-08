;; All things specific to the mcp23017 chip. If you have to read the datasheet
;; or access the chip, it goes in this file. All else, no!
;; Datasheet: https://www.microchip.com/wwwproducts/en/MCP23017

(ns hsec.source.mcp23017
  (:require [dvlopt.linux.i2c       :as i2c]
            [dvlopt.linux.i2c.smbus :as smbus]))

(def registers
  {
   :a  { ;; addressing mode 'a'
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
   :b { ;; addressing mode 'b'
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

    ;; set int mirror and active-high
    ;; The 4 bit causes the interrupt pins to be internally connected so
    ;; that either interrupt causes both to be on.
    ;; The active-high causes an interrupt to have high polarity when active.
    ;; The IOCON register is shared between :a and :b so it only needs to be
    ;; set for one bank.
    (smbus/write-byte bus (get-in registers [:a :iocon]) 0x42)

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
