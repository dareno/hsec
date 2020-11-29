;; All things specific to the mcp23017 chip. If you have to read the datasheet
;; or access the chip, it goes in this file. All else, no!
;; Datasheet: https://www.microchip.com/wwwproducts/en/MCP23017

(ns hsec.mcp23017
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

(comment
  ;;obsolete
  (defn port-number-keyword
    "given a keyword for the port and a number, return the keyword for the port
   example: :a 2 => :a2"
    [port-keyword number]
    (keyword (str (name port-keyword) number)))
  )

(defn bit-to-open-closed
  "convert bit to datasheet meaning"
  [bitcode]
  (if (= bitcode 1) :logic-high :logic-low))

(defn bit-to-interrupt-state
  "convert bit status to keywords for open and closed doors"
  [bitcode]
  (if (= bitcode 1) :interrupt :not-pending))

(defn bitn
  "return the nth most significant bit of a number"
  [n byte]
  (bit-shift-right (bit-and byte (bit-shift-left 1 n)) n))

(comment ;; obsolete

  (defn make-state-from-byte
    "given a port and byte with port status, return a map of the current state"
    [port status-byte state-words]
    (into {} (map
              #(let [key (port-number-keyword port %)]
                 {key (state-words (bitn % status-byte))})
              (range 0 8))))
  )

(defn deserialize-register
  "Given an integer, convert it into an object with keyword names like GP0."
  [status-byte state-words]
  (into {} (map
            #(let [key (keyword (str "GP" %))]
               {key (state-words (bitn % status-byte))})
            (range 0 8))))

(comment ;; test deserialize-register
  (deserialize-register 43 bit-to-open-closed)
  (deserialize-register 4 bit-to-interrupt-state))

(comment ;; obsolete

  (defn gpio-state-from-byte
    "given a port and byte with port status, return a map of the current state"
    [port status-byte]
    (make-state-from-byte port status-byte bit-to-open-closed)))


(defn deserialize-gpio-integer
  "Given an integer status byte, return an object with logic levels per pin."
  [status-byte]
  (deserialize-register status-byte bit-to-open-closed))

(comment ;; obsolete

  (defn int-state-from-byte
    "given a port and byte with port status, return a map of the current state"
    [port status-byte]
    (make-state-from-byte port status-byte bit-to-interrupt-state)))

(defn deserialize-interrupt-integer
  "Given an integer status byte, return an object describing which pin caused
  the interrupt. Note that other pins may have been active since the interrupt.
  Therefore, state must be updated for all pins after an interrupt regardless
  as to which pin caused the interrupt."
  [status-byte]
  (deserialize-register status-byte bit-to-interrupt-state))

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
  "return the byte contents of both :a and :b registers. Use the deserializer
  to store the integer value as a semantic object with the right descriptive
  keys."
  [bus register deserializer]
  (let [bank-a-integer (get-register bus :a register)
        bank-b-integer (get-register bus :b register)]
    {:a {:value bank-a-integer :deserialized (deserializer bank-a-integer)}
     :b {:value bank-b-integer :deserialized (deserializer bank-b-integer)}}))
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

(comment ;; example usage
  ;; set initial chip configuration
  (def bus (setup-chip "/dev/i2c-1" 0x20))

  ;; get current PIR state
  (get-in (get-registers bus :gpio deserialize-gpio-integer) [:a :deserialized :GP2])

  ;; get PIR activity at interrupt
  (get-in (get-registers bus :intcap deserialize-gpio-integer) [:a :deserialized :GP2])

  ;; get the value of the interrupt flag.
  (Integer/toBinaryString (smbus/read-byte bus (get-in registers [:a :intf])))

  (comment ;; obsolete
    ;;old stuff, have higher-level functions now

    (def capabilities (i2c/capabilities bus))
    capabilities
    (smbus/read-byte bus (get-in registers [:a :gpio]))

    ;; get the value of gpio port 2
    (bitn 2 (smbus/read-byte bus (get-in registers [:a :gpio])))

    ;; get the value of gpio port 2 when the interrupt occurred
    (bitn 2 (smbus/read-byte bus (get-in registers [:a :intcap]))))

  (shutdown-chip bus)
  )
