;; All things specific to the mcp23017 chip. If you have to read the datasheet
;; or access the chip, it goes in this file. All else, no!
;; Datasheet: https://www.microchip.com/wwwproducts/en/MCP23017
;; The Microchip MCP23017 has 16-bit I/O port functionality via
;; two 8-bit ports (PORTA and PORTB). This should not be confused
;; with addressing modes BANK=0 or BANK=1.
(ns hsec.source.mcp23017
  (:require [dvlopt.linux.i2c       :as i2c]
            [dvlopt.linux.i2c.smbus :as smbus]))

;; actually a util function, here until separate ns required
(defn bitn
  "return the nth most significant bit of a number"
  [n byte]
  (bit-shift-right (bit-and byte (bit-shift-left 1 n)) n))

(defn fmap
  "Run f on each value in map m. Borrowed from
  https://stackoverflow.com/questions/1676891/mapping-a-function-on-the-values-of-a-map-in-clojure"
  [f m]
  (into (empty m) (for [[k v] m] [k (f v)])))

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

(defn bit-to-logic-level
  "convert logic bit to datasheet meaning"
  [bitcode]
  (if (= bitcode 1) :logic-high :logic-low))

(defn bit-to-interrupt-state
  "convert interrupt bit to datasheet meaning"
  [bitcode]
  (if (= bitcode 1) :interrupt :not-pending))

(defn deserialize-register
  "Given an integer, convert it into an object with keyword names like GP0."
  [
   state-words   ;; a fn to deserialize the bit
   status-byte   ;; an integer to decode as a binary bitmap
   ]
  (into {} (map
            #(let [key (keyword (str "GP" %))]
               {key (state-words (bitn % status-byte))})
            (range 0 8))))

(def deserialize-gpio-register
  (partial deserialize-register bit-to-logic-level))

(def deserialize-intf-register
  (partial deserialize-register bit-to-interrupt-state))

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

(defn get-register
  "return the byte contents of a register (action)"
  [bus port register]
  (let [address (get-in registers [port register])] ;; lookup register address
    (smbus/read-byte bus address)))                 ;; return the value there

(defn get-registers
  "return the byte contents of both :a and :b registers (action)"
  [bus register]
  {:a (get-register bus :a register)
   :b (get-register bus :b register)})

(defn get-irq-registers
  "Return all the registers needed to deduce what changed related to an
  interrupt occurence."
  [bus]
  (do
    (def intf (get-registers bus :intf))
    (def intcap (get-registers bus :intcap))
    (def gpio (get-registers bus :gpio))
    {:intf intf :intcap intcap :gpio gpio}))

(defn get-all
  "Return a map of all GPO ports and their logic state. Resets
  interrupts so this is an action."
  [bus]
  (comment
    (def bus (setup-chip "/dev/i2c-1" 0x20))
    (shutdown-chip bus)
    (def deserialize-gpio-register (partial deserialize-register bit-to-logic-level))
    (def gpio-registers (get-registers bus :gpio))
    )

  (let [gpio-registers (get-registers bus :gpio)]

    ;; transform the map of gpio ports from a bitmap value to a map value
    (fmap deserialize-gpio-register gpio-registers)))

(defn filter-map
  "remove entries in a map that don't have the value 'interrupt"
  [m]
  (into {} (filter (fn [[k v]] (= v :interrupt)) m))
  )

(comment
  (filter-map (:a irq-map))
)

(defn get-interrupt-path
  "given a 'port->interrupt' with port and nested value of pin->interrupt-value,
  return the path to the :interrupt pin"
  [m]
  (let
      [result (->> m
                   (fmap filter-map)
                   (filter (fn [[k v]] (not-empty v)))
                   (into {})
                   )
       port (first (keys result))
       pin (first (keys (get-in result [port])))
       ]
    [port pin]
    ))

(comment
  (def m {:a
          {:GP0 :not-pending,
           :GP1 :not-pending,
           :GP2 :interrupt,
           :GP3 :not-pending,
           :GP4 :not-pending,
           :GP5 :not-pending,
           :GP6 :not-pending,
           :GP7 :not-pending},
          :b
          {:GP0 :not-pending,
           :GP1 :not-pending,
           :GP2 :not-pending,
           :GP3 :not-pending,
           :GP4 :not-pending,
           :GP5 :not-pending,
           :GP6 :not-pending,
           :GP7 :not-pending}})
  (get-interrupt-path m)

  (def result (->> m
                   (fmap filter-map)
                   (filter (fn [[k v]] (not-empty v)))
                   (into {})
                   ))
  (def port (first (keys result)))
  (def pin (first (keys (get-in result [port]))))
  )


(defn get-changed-pins
  ;; consider refactoring this to take the register map. would ease testing
  "Return a map of GPIO ports changed since interrupt and their logic state.
  Resets interrupts so not idempotent (this is an action)."
  [registers]
  ;; 1. Read INTFA and INTFB to identify the port/pin combo that caused the
  ;;    interrupt.
  ;; 2. Use INTCAPA and INTCAPB to identify the initial state and new event on
  ;;    the pin that caused the interrupt.
  ;; 3. Read GPIOA and GPIOB and use saved INTCAPs to identify any other events
  ;;    that have since occurred.
  ;; 4. return this set of events
  ;;
  ;; N.B. Theoreticaly, pins could change rapidly between the initial interrupt
  ;;      capture and gpio read. This hardware is probably inappropriate for
  ;;      capturing all events related to rapidly flapping pins but should
  ;;      suffice for anything related to sensing mechanical change.
  (->> (:intf registers) ;; keys: :intf, :intcap, and :gpio
       (fmap deserialize-intf-register) ;; integer values to maps
       (get-interrupt-path)             ;; e.g. '[:a :GP2]'
       ))

(comment
  ;; sensor:

  (filter-map (:a irq-map))
  (def bus hsec.source.sensor/bus)


  (def sample-registers (get-irq-registers bus))
  (def registers sample-registers)
  (get-changed-pins registers)
)
