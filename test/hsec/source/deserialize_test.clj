(ns hsec.source.deserialize-test
  (:require  [clojure.test :refer :all]
             [hsec.source.deserialize :as d]))

(deftest bit-to-logic-level
  (is (= (d/bit-to-logic-level 1) :logic-high))
  (is (= (d/bit-to-logic-level 0) :logic-low)))

(deftest bitn
  (is (= (d/bitn 0 5) 1))
  (is (= (d/bitn 1 5) 0))
  (is (= (d/bitn 2 5) 1))
  (is (= (d/bitn 3 5) 0)))

(deftest bit-to-interrupt-state
  (is (= (d/bit-to-interrupt-state 1) :interrupt))
  (is (= (d/bit-to-interrupt-state 0) :not-pending))
  (is (= (d/bit-to-interrupt-state nil) :not-pending)))

(deftest deserialize-register
  (is (= (d/deserialize-register 43 d/bit-to-logic-level)
         {:GP0 :logic-high, :GP1 :logic-high, :GP2 :logic-low,
          :GP3 :logic-high, :GP4 :logic-low,  :GP5 :logic-high,
          :GP6 :logic-low,  :GP7 :logic-low}))
  (is (= (d/deserialize-register 4 d/bit-to-interrupt-state)
         {:GP0 :not-pending, :GP1 :not-pending, :GP2 :interrupt,
          :GP3 :not-pending, :GP4 :not-pending, :GP5 :not-pending,
          :GP6 :not-pending, :GP7 :not-pending})))

;; (deftest port-number-keyword
;;   (is (= (d/port-number-keyword :a 1) :a1)))

  ;; (is (= (chip/smbus-command bus-string slave-address command 0x42) ;; write
  ;;        nil))
  ;; (is (= (chip/smbus-command bus-string slave-address command)      ;; read
  ;;        0x42)))

;; (deftest read-and-write-iocon
;;   ;; set IOCON register to 0x42 and then read it, expecting the same value
;;   (let [bus-string "/dev/i2c-1" ;; Linux path to i2c device
;;         slave-address 0x20      ;; Hardware configured to this address
;;         command (get-in chip/register [:A :IOCON])] ;; the address/command of the register
;;     (is (= (chip/smbus-command bus-string slave-address command 0x42) ;; write
;;            nil))
;;     (is (= (chip/smbus-command bus-string slave-address command)      ;; read
;;            0x42))))
