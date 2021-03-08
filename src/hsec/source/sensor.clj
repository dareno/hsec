(ns hsec.source.sensor (:require
                        [hsec.source.mcp23017 :as mcp23017]
                        [hsec.source.gpio :as gpio]
                        [hsec.source.deserialize :as d]
                        [Clojure.core.async :as a]
                        ))

(comment ;; calling mcp23017 functions

  ;; set initial chip configuration
  (def bus (mcp23017/setup-chip "/dev/i2c-1" 0x20))

  ;; get current PIR state
  (:GP2 (d/deserialize-gpio-integer
        (get-in (mcp23017/get-registers bus :gpio) [:a])))

  ;; are interrupts pending?
  (d/deserialize-interrupt-integer (get-in
                                    (mcp23017/get-registers bus :intf) [:a]))

  ;; get PIR activity at interrupt
  (:GP2 (d/deserialize-gpio-integer (get-in
                                     (mcp23017/get-registers bus :intcap) [:a])))

  (mcp23017/shutdown-chip bus))


(comment ;; async testing
  (def sensor-control-channel (a/chan (a/sliding-buffer 10)))
  (def event-channel (a/chan (a/sliding-buffer 10)))

  ;; start event processor
  (a/go (loop []
          (let [event (a/<! event-channel)]
            (if (= event nil)
              (println "event-processor: nil on event channel, shutting down")
              (do ;; for each event
                (println event)
                (println (-> (mcp23017/get-registers bus :gpio)
                             (:a)
                             (d/deserialize-gpio-integer)
                             (:GP2)))
                (recur))))))

  ;; start interrupt sensor
  (a/go (gpio/interrupts [5] sensor-control-channel event-channel))

  ;; shutdown the event-noticed. Will close event channel.
  (a/>!! sensor-control-channel "stop")

  ;; when done testing, close channels
  (a/close! sensor-control-channel)
  ;; (a/close! event-channel) ;; only the producer should close a channel
  ) ;; end comment