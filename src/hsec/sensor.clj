(ns hsec.sensor
  (:require [dvlopt.linux.i2c       :as i2c]
            [dvlopt.linux.i2c.smbus :as smbus]
            [hsec.mcp23017          :as mcp23017]))
  ;; (:import java.lang.AutoCloseable))

(defn setup-chip
  "Given a bus path and slave address:
  mirror interrupts and enable interupt on change for pin 2.
  Return the bus object for commands. The bus must be closed during shutdown."
  [bus-string slave-address]
  (let [bus (i2c/bus bus-string)]

    ;; this bus will always use the selected slave address for commands
    (i2c/select-slave bus slave-address)

    ;; set int mirror and active-high
    (smbus/write-byte bus (get-in mcp23017/register [:a :iocon]) 0x42)

    ;; enable int on ~pin 2~ all pins
    ;; (smbus/write-byte bus (get-in mcp23017/register [:a :gpinten]) 0x04)
    (smbus/write-byte bus (get-in mcp23017/register [:a :gpinten]) 0xff)

    ;; return the bus object for future reads/writes; must be closed later
    bus))

(defn shutdown-chip
  "prepare to cleanly exit"
  [bus]
  (i2c/close bus))

(defn bitn
  "return the nth most significant bit of a number"
  [n byte]
  (bit-shift-right (bit-and byte (bit-shift-left 1 n)) n))

(defn start
  "Get the initial state of all sensors as well as the change event channel"
  [shutdown-signal events-out]
  )

(defn bit-to-open-closed
  "convert bit status to keywords for open and closed doors"
  [bitcode]
  (if (= bitcode 1) :open :closed))

(defn port-number-keyword
  "given a keyword for the port and a number, return the keyword for the port"
  [port-keyword number]
  (keyword (str (name port-keyword) number)))

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
  (make-state-from-byte port (smbus/read-byte bus (get-in mcp23017/register [port register]))))

(comment ;; REPL testing for development

  ;; set initial chip configuration
  (def bus (setup-chip "/dev/i2c-1" 0x20))
  (def capabilities (i2c/capabilities bus))
  capabilities
  (smbus/read-byte bus (get-in chip/register [:A :IOCON]))
   (smbus/read-byte bus (get-in mcp23017/register [:a :gpio]))

  ;; get state of bus :a
  ;; currently
  (get-state bus :a :gpio)
  ;; at time of interrupt
  (get-state bus :a :intcap)

  ;; get the value of the interrupt flag. setup-chip sets it to gpio2 only
  (Integer/toBinaryString (smbus/read-byte bus (get-in mcp23017/register [:a :intf])))

  ;; get the value of gpio port 2
  (bitn 2 (smbus/read-byte bus (get-in mcp23017/register [:a :gpio])))

  ;; get the value of gpio port 2 when the interrupt occurred
  (bitn 2 (smbus/read-byte bus (get-in mcp23017/register [:a :intcap])))

  (shutdown-chip bus)

  ) ;; end comment
