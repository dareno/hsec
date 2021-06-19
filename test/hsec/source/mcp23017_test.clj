(ns hsec.source.mcp23017-test
  (:require  [clojure.test :refer :all]
             [hsec.source.mcp23017 :as m]
             [clojure.core.async :as a]))

(deftest bitn
  (is (= (m/bitn 0 5) 1))
  (is (= (m/bitn 1 5) 0))
  (is (= (m/bitn 2 5) 1))
  (is (= (m/bitn 3 5) 0)))

(deftest bit-to-logic-level
  (is (= (m/bit-to-logic-level 1) :logic-high))
  (is (= (m/bit-to-logic-level 0) :logic-low)))

(deftest bit-to-interrupt-state
  (is (= (m/bit-to-interrupt-state 1) :interrupt))
  (is (= (m/bit-to-interrupt-state 0) :not-pending))
  (is (= (m/bit-to-interrupt-state nil) :not-pending)))

(deftest deserialize-register
  (let [m-test {:GP0 :logic-high, :GP1 :logic-high, :GP2 :logic-low,
                :GP3 :logic-high, :GP4 :logic-low,  :GP5 :logic-high,
                :GP6 :logic-low,  :GP7 :logic-low}]
    (is (= (m/deserialize-gpio-register 43) m-test)))
  (let [m-test {:GP0 :not-pending, :GP1 :not-pending, :GP2 :interrupt,
                :GP3 :not-pending, :GP4 :not-pending, :GP5 :not-pending,
                :GP6 :not-pending, :GP7 :not-pending}]
    (is (= (m/deserialize-register m/bit-to-interrupt-state 4) m-test))))

(deftest get-interrupt-path
  (let [interrupt-map {:a
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
                        :GP7 :not-pending}}]
    (is (= (m/get-interrupt-path interrupt-map) [:a :GP2]))))
