;; Code to monitor the GPIO pins. Pin 5 is used for interrupts from hardware.
;; When interrupts occur, events will be sent on a channel to the event handler.

(ns hsec.source.gpio
  (:require [dvlopt.linux.gpio :as gpio]
            [clojure.core.async :as a])
  (:import java.lang.AutoCloseable))

(defn add-interrupt [watch-options line-number]
  (assoc watch-options
         line-number
         {::gpio/edge-detection :rising
          ::gpio/direction      :input}))

(defn wait-for-events
  "Given GPIO lines to monitor and given a control-channel to listen to for
  when to stop, keep noticing interrupts on the GPIO lines until told to stop.
  When an interrupt is detected, put it on the event-channel."
  [line-numbers control-channel event-channel]
  (with-open [^AutoCloseable device  (gpio/device "/dev/gpiochip0")
              ^AutoCloseable watcher (gpio/watcher device
                                                   (reduce
                                                    add-interrupt
                                                    {}
                                                    line-numbers))]
    (loop []

      ;; block until an event or 100ms, then get a control message or timeout
      (let [event (gpio/event watcher 100)
            [m c] (a/alts!! [control-channel (a/timeout 10)])]

        ;; publish events if they occur
        (if event
          (do
            (println event)
            (a/>!! event-channel
                   (format "%d interrupt for line %d detected"
                           (::gpio/nano-timestamp event)
                           (::gpio/tag event)))))

        (if (= c control-channel)

          (do ;; there was a stop message, close the event-channel
            (println "gpio:" m "from control, closing event-channel and stopping.")
            (a/close! event-channel)
            "done") ;; for testing
          ;; if no control message, recur the loop
          (recur))))))

(comment ;; async testing
  (def line-numbers interrupt-list)
  (def device (gpio/device "/dev/gpiochip0"))
  (def watcher (gpio/watcher device
                             (reduce
                              add-interrupt
                              {}
                              line-numbers)))
  (gpio/close watcher)
  (gpio/close device)

  (def test-control-channel (a/chan (a/sliding-buffer 10)))
  (a/go (interrupts interrupt-list test-control-channel))
  (a/>!! test-control-channel "stop")

  (a/go (println (a/<! test-control-channel)))
  (a/go (println (a/<! (a/timeout 5000))))

  (close! test-control-channel)
  (def alt-result (alts!! [test-control-channel (timeout 20)]))
  (first alt-result)
  (second alt-result)


  (def interrupt-list [5])

  )
