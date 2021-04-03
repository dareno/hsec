(ns hsec.source.deserialize-test
  (:require  [clojure.test :refer :all]
             [hsec.source.deserialize :as d]))


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
