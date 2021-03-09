;; Code to assist with deserializing RPi I2C registers to objects.
(ns hsec.source.deserialize)

(comment ;;obsolete
  (defn port-number-keyword
    "given a keyword for the port and a number, return the keyword for the port
   example: :a 2 => :a2"
    [port-keyword number]
    (keyword (str (name port-keyword) number)))
  )

(defn bit-to-logic-level
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

(comment ;; obsolete

  (defn gpio-state-from-byte
    "given a port and byte with port status, return a map of the current state"
    [port status-byte]
    (make-state-from-byte port status-byte bit-to-logic-level)))

(comment ;; obsolete?
  (defn deserialize-gpio-integer
    "Given an integer status byte, return an object with logic levels per pin."
    [status-byte]
    (deserialize-register status-byte bit-to-logic-level)))

(comment ;; obsolete
  (defn int-state-from-byte
    "given a port and byte with port status, return a map of the current state"
    [port status-byte]
    (make-state-from-byte port status-byte bit-to-interrupt-state)))

(comment ;; obsolete?
  (defn deserialize-interrupt-integer
    "Given an integer status byte, return an object describing which pin caused
  the interrupt. Note that other pins may have been active since the interrupt.
  Therefore, state must be updated for all pins after an interrupt regardless
  as to which pin caused the interrupt."
    [status-byte]
    (deserialize-register status-byte bit-to-interrupt-state)))
