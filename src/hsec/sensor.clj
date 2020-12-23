(ns hsec.sensor (:require
                 [hsec.mcp23017 :as mcp23017]
                 [hsec.gpio :as gpio]
                 [clojure.core.async :as a]))

(comment
  (use 'clojure.tools.deps.alpha.repl)
  (require '[clojure.tools.deps.alpha.repl :refer [add-lib]])
  (add-lib 'org.clojure/core.memoize {:mvn/version "0.7.1"})
  ,)

(defn start
  "Get the initial state of all sensors as well as the change event channel"
  [shutdown-signal events-out]
  )

(comment ;; calling mcp23017 functions

  ;; set initial chip configuration
  (def bus (mcp23017/setup-chip "/dev/i2c-1" 0x20))

  ;; get current PIR state
  (get-in (mcp23017/get-registers bus :gpio mcp23017/deserialize-gpio-integer)
          [:a :deserialized :GP2])

  ;; are interrupts pending?
  (get-in
   (mcp23017/get-registers bus :intf mcp23017/deserialize-interrupt-integer)
   [:a :deserialized])

  ;; get PIR activity at interrupt
  (get-in (mcp23017/get-registers bus :intcap mcp23017/deserialize-gpio-integer)
          [:a :deserialized :GP2])

  (mcp23017/shutdown-chip bus)

  )


(comment ;; async testing
  (def sensor-control-channel (a/chan (a/sliding-buffer 10)))
  (def event-channel (a/chan (a/sliding-buffer 10)))


  ;; start event processor
  (a/go (loop []
          (let [event (a/<! event-channel)]
            (if (= event nil)
              (println "event-processor: nil on event channel, shutting down")
              (do
                (println event)
                (println (get-in (mcp23017/get-registers
                                  bus
                                  :gpio mcp23017/deserialize-gpio-integer)
                                 [:a :deserialized :GP2]))
                (recur))))))

  ;; start interrupt sensor
  (a/go (gpio/interrupts [5] sensor-control-channel event-channel))

  (a/>!! sensor-control-channel "stop")
  (a/close! sensor-control-channel)
  (a/close! event-channel)
  ) ;; end comment
