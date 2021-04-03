(ns hsec.source.gpio-test
  (:require  [clojure.test :refer :all]
             [hsec.source.gpio :as g]
             [clojure.core.async :as a]))

(deftest add-interrupt
  (is (= (reduce g/add-interrupt {} [5 6])
         {5 #:dvlopt.linux.gpio{:edge-detection :rising, :direction :input},
          6 #:dvlopt.linux.gpio{:edge-detection :rising, :direction :input}}))
  (is (= (reduce g/add-interrupt
                 {5 #:dvlopt.linux.gpio{:edge-detection :rising, :direction :input}}
                 [6])
         {5 #:dvlopt.linux.gpio{:edge-detection :rising, :direction :input},
          6 #:dvlopt.linux.gpio{:edge-detection :rising, :direction :input}})))

(deftest interrupts
  (do
    (def sensor-control-channel (a/chan (a/sliding-buffer 10)))
    (def event-channel (a/chan (a/sliding-buffer 10)))
    (def go-out-chan (a/go (g/wait-for-events [] sensor-control-channel event-channel)))
    (def timeout-channel (a/timeout 10000))
    (testing "channel should not have returned yet"
      ;; we're trying to take from the go channel but expecting it to not have
      ;; returned yet as it hasn't been "stop"ed. So we expect the timeout
      ;; channel to return and thus the first part of the return is the nil
      ;; message. This is a complexity of async testing.
      (is (= (first (a/alts!! [go-out-chan (a/timeout 1000)])) nil)))
    (a/>!! sensor-control-channel "stop")
    (def mc (a/alts!! [event-channel timeout-channel]))
    (def channel-should-be-event (second mc))
    (testing "channel should have stopped and sent done"
      ;; we're taking from the go channel to ensure it has sent it's completion
      ;; message. This is necessary due to async testing complexities.
      (is (= (a/<!! go-out-chan) "done")))
    ))
