(ns hsec.core
  (:require [hsec.mcp23017 :as mcp23017]))

mcp23017/registers

(defn -main
  "I don't do a whole lot ... yet."
  [& args]
  (println "Hello, World!"))

(def names
  {
   :pir {:address {:mcp0 {:port :a2}}}
   :door-kitchen {:address {:mcp0 {:port :a3}}}
   :door-family-room {:address {:mcp0 {:port :a4}}}
   :door-front {:address {:mcp0 {:port :a6}}}
   :door-basement {:address {:mcp0 {:port :a7}}}
   })

(def zones
  {
   :Doors { :armed false :members '( :a4 :a6 :a7 ) }
   :Upper-Windows { :armed false :members '(  ) }
   :Lower-Windows { :armed false :members '(  ) }
   :Inside-Motion { :armed false :members '( :a2 ) }
   })

(defn address-of
  "given a name path vector, return a HW address"
  [name]
  (get-in names [name :address]))

(comment
  (address-of :door-front))

(defn name-of
  "given a HW addresss, return the name"
  [address-of]
  )

;; create control-channel and use go block to pass to sensor
;; consider interface between sensor and state
