(ns hsec.trigger
  (:gen-class)
  (:require [dvlopt.linux.i2c       :as i2c]
            [dvlopt.linux.i2c.smbus :as smbus]
            [hsec.mcp23017          :as mcp23017])
  (:import java.lang.AutoCloseable))


(defn smbus-command
  "read or write on an smbus"
  [bus-string slave-address command & [value]]
  (let [bus (i2c/bus bus-string)]
    (i2c/select-slave bus slave-address)
    (if value
      (def status (smbus/write-byte bus command value))
      (def status (smbus/read-byte bus command)))
    (i2c/close bus)
    status))

(defn setup-chip
  "mirror interrupts and enable interupt on change for pin 2"
  [bus-string slave-address]

  ;; set int mirror and active-high
  (smbus-command bus-string slave-address
                 (get-in mcp23017/register [:A :IOCON]) 0x42) 

  ;; enable int on pin 2
  (smbus-command bus-string slave-address
                 (get-in mcp23017/register [:A :GPINTEN]) 0x04))

(comment
  ;; set initial chip configuration
  (setup-chip "/dev/i2c-1" 0x20)

  ;; get bus capabilities
  (let [bus (i2c/bus "/dev/i2c-1")]
    (def capabilities (i2c/capabilities bus))
    (i2c/close bus)
    capabilities)

  ;; get the value of the interrupt flag. setup-chip sets it to gpio2 only
  (Integer/toBinaryString (smbus-command "/dev/i2c-1" 0x20
                                         (get-in mcp23017/register [:A :INTF])))

  ;; get the value of gpio port 2
  (bitn 2 (smbus-command "/dev/i2c-1" 0x20
                         (get-in mcp23017/register [:A :GPIO])))

  ;; get the valu of gpio port 2 when the interrupt occurred
  (bitn 2 (smbus-command "/dev/i2c-1" 0x20
                         (get-in mcp23017/register [:A :INTCAP])))

  ) ;; end comment
