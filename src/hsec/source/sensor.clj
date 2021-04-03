;; Takes all raw events, deserialize based on config information
;; and write high-level events to an event channel. Include control
;; events.

(ns hsec.source.sensor (:require
                        [hsec.source.mcp23017 :as m]
                        [hsec.source.gpio :as gpio]
                        ;; [hsec.source.deserialize :as d]
                        [clojure.core.async :as a]
                        ))

(defn get-event-channel
  "Return a channel for control and sensor events. Use provided
  configuration to deserialize."
  [configuration control-channel event-channel]

  ;; inputs:
  ;;   configuration: a map between GP0-GP7 and named sensors
  ;;   control-channel: listen to this for higher-level shutdown
  ;;                    requests. Also, shutdown requests may come
  ;;                    from the child control.
  ;;   event-channel: write high-level events here. Close this when
  ;;                  shutting down.
  ;;
  ;; create channels for control
  ;; create channels for sensor events
  ;; startup sensor event getter
  ;; read sensor events, deserialize and write into event-channel
  ;; read control events, deserialize and write into event-channel

  )

(comment ;; calling m functions

  ;; get current PIR state
  (:GP2 (d/deserialize-register
         (get-in (m/get-registers bus :gpio) [:a])
         d/bit-to-logic-level))

  ;; are interrupts pending?
  (:GP2(d/deserialize-register
        (get-in (m/get-registers bus :intf) [:a])
        d/bit-to-interrupt-state))

  ;; partial testing

  (:GP2 (d/deserialize-register
        (get-in (get-registers-with-bus :intf) [:a])
        d/bit-to-interrupt-state))
  (:GP2 (d/deserialize-register
         (get-in (get-registers-with-bus :gpio) [:a])
         d/bit-to-logic-level))
  (defn handler
    "handle a new event"
    []

    )

  ;; get PIR activity at interrupt
  (:GP2 (d/deserialize-register
         (get-in (m/get-registers bus :intcap) [:a])
         d/bit-to-logic-level))

  (m/shutdown-chip bus)
  )

;; set initial chip configuration and create a fn with
(def bus (m/setup-chip "/dev/i2c-1" 0x20))
(def get-registers-with-bus (partial m/get-registers bus))
(comment
  (m/get-all bus)
  )

(defn m-handler
  "called on interrupts corresponding to an M chip.
  This should probably be a composition of functions.
  1. m/get-changes
  2. deserialize
  3. write to event-channel"
  [get-change-since-irq]
  (println (->
            ;; (m/get-registers bus :gpio) ;; stub for get initial data
            (get-change-since-irq)
            (:a)
            (d/deserialize-register d/bit-to-logic-level)
            (:GP2))))

(comment ;; async testing
  (def interrupt-list [5])
  (def sensor-control-channel (a/chan (a/sliding-buffer 10)))
  (def event-channel (a/chan (a/sliding-buffer 10)))

  ;; start handler
  (a/go (loop []
          (let [event (a/<! event-channel)]
            (if (= event nil)
              (println "event-processor: nil on event channel, shutting down")
              (do ;; for each event
                (println event)
                (println (-> (m/get-registers bus :gpio)
                             (:a)
                             (d/deserialize-register d/bit-to-logic-level)
                             (:GP2)))
                (recur))))))

  ;; start interrupt sensor
  (a/go (gpio/wait-for-events interrupt-list
                              sensor-control-channel
                              event-channel))

  ;; shutdown the event-noticed. Will close event channel.
  (a/>!! sensor-control-channel "stop")

  ;; when done testing, close channels
  (a/close! sensor-control-channel)
  ;; (a/close! event-channel) ;; only the producer should close a channel
  ) ;; end comment
