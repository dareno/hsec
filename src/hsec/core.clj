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
  "given a name path vector, get a HW address"
  [name]
  (get-in names [name :address]))
(address-of :door-front)

