(ns hsec.sensor (:require
                 [hsec.mcp23017 :as mcp23017]
                 [clojure.core.async
                  :as a
                  :refer [>! <! >!! <!! go chan buffer close! thread
                          alts! alts!! timeout]]))

(defn start
  "Get the initial state of all sensors as well as the change event channel"
  [shutdown-signal events-out]
  )

(comment ;; calling mcp23017 functions

  ;; set initial chip configuration
  (def bus (mcp23017/setup-chip "/dev/i2c-1" 0x20))

  ;; get current PIR state
  (get-in (mcp23017/get-registers bus :gpio mcp23017/deserialize-gpio-integer)
          [:a :deserialized])

  ;; get PIR activity at interrupt
  (get-in (mcp23017/get-registers bus :intcap mcp23017/deserialize-gpio-integer)
          [:a :deserialized])

  (mcp23017/shutdown-chip bus)

  )


(comment ;; async testing
  (def echo-chan (chan))
  (go (println (<! echo-chan)))
  (>!! echo-chan "ketchup")

  (thread (println (<!! echo-chan)))
  (>!! echo-chan "mustard")


  (close! echo-chan)
  ) ;; end comment
