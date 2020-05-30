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

(defn port-number-keyword
  "given a keyword for the port and a number, return the keyword for the port"
  [port-keyword number]
  (keyword (str (name port-keyword) number)))

(defn bit-to-open-closed
  "convert bit status to keywords for open and closed doors"
  [bitcode]
  (if (= bitcode 1) :open :closed))

(defn bitn
  "return the nth most significant bit of a number"
  [n byte]
  (bit-shift-right (bit-and byte (bit-shift-left 1 n)) n))

(defn make-state-from-byte
  "given a port and byte with port status, return a map of the current state"
  [port status-byte]
  (into {} (map
            #(let [key (port-number-keyword port %)]
               {key (bit-to-open-closed (bitn % status-byte))})
            (range 0 8))))

(defn get-state
  "read both A and B ports of chip, return results"
  [bus port register]
  (make-state-from-byte port (smbus/read-byte bus (get-in registers [port register]))))

;;(make-state-from-byte :a (smbus/read-byte bus (get-in registers [:a :gpio])))

(defn setup-chip
  "Given a bus path and slave address:
  mirror interrupts and enable interupt on change for pin 2.
  Return the bus object for commands. The bus must be closed during shutdown."
  [bus-string slave-address]
  (let [bus (i2c/bus bus-string)]

    ;; this bus will always use the selected slave address for commands
    (i2c/select-slave bus slave-address)

    ;; set int mirror and active-high
    (smbus/write-byte bus (get-in register [:a :iocon]) 0x42)

    ;; enable int on ~pin 2~ all pins
    ;; (smbus/write-byte bus (get-in mcp23017/register [:a :gpinten]) 0x04)
    (smbus/write-byte bus (get-in register [:a :gpinten]) 0xff)

    ;; return the bus object for future reads/writes; must be closed later
    bus))

(defn shutdown-chip
  "prepare to cleanly exit"
  [bus]
  (i2c/close bus))

(comment
  ;; set initial chip configuration
  (def bus (setup-chip "/dev/i2c-1" 0x20))
  (def capabilities (i2c/capabilities bus))
  capabilities
  (smbus/read-byte bus (get-in register [:a :gpio]))

  ;; get state of bus :a :a2
  ;; currently
  (:a6 (get-state bus :a :gpio))
  ;; at time of interrupt
  (:a6 (get-state bus :a :intcap))

  ;; get the value of the interrupt flag. setup-chip sets it to gpio2 only
  (Integer/toBinaryString (smbus/read-byte bus (get-in registers [:a :intf])))

  ;; get the value of gpio port 2
  (bitn 2 (smbus/read-byte bus (get-in registers [:a :gpio])))

  ;; get the value of gpio port 2 when the interrupt occurred
  (bitn 2 (smbus/read-byte bus (get-in registers [:a :intcap])))

  (shutdown-chip bus)
  )
