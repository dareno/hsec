(ns hsec.mcp23017-test
  (:require  [clojure.test :refer :all]
             [hsec.mcp23017 :as mcp]))

(deftest bit-to-open-closed
  (is (= (mcp/bit-to-open-closed 1) :open))
  (is (= (mcp/bit-to-open-closed 0) :closed)))

(deftest bitn
  (is (= (mcp/bitn 0 5) 1))
  (is (= (mcp/bitn 1 5) 0))
  (is (= (mcp/bitn 2 5) 1))
  (is (= (mcp/bitn 3 5) 0)))

(deftest make-state-from-byte
  (is (= (mcp/make-state-from-byte :a 43)
         {:a0 :open, :a1 :open, :a2 :closed, :a3 :open, :a4 :closed, :a5 :open, :a6 :closed, :a7 :closed})))

(deftest port-number-keyword
  (is (= (mcp/port-number-keyword :a 1) :a1)))

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
  
