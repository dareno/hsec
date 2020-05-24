(ns hsec.sensor-test
  (:require  [clojure.test :refer :all]
             [hsec.sensor :as sensor]
             [hsec.mcp23017 :as chip]))

(deftest bit-to-open-closed
  (is (= (sensor/bit-to-open-closed 1) :open))
  (is (= (sensor/bit-to-open-closed 0) :closed)))

(deftest bitn
  (is (= (sensor/bitn 0 5) 1))
  (is (= (sensor/bitn 1 5) 0))
  (is (= (sensor/bitn 2 5) 1))
  (is (= (sensor/bitn 3 5) 0)))

(deftest make-state-from-byte
  (is (= (sensor/make-state-from-byte :a 43)
         {:a0 :open, :a1 :open, :a2 :closed, :a3 :open, :a4 :closed, :a5 :open, :a6 :closed, :a7 :closed})))

(deftest port-number-keyword
  (is (= (sensor/port-number-keyword :a 1) :a1)))

  ;; (is (= (chip/smbus-command bus-string slave-address command 0x42) ;; write
  ;;        nil))
  ;; (is (= (chip/smbus-command bus-string slave-address command)      ;; read
  ;;        0x42)))

