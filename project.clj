(defproject hsec "0.1.0-SNAPSHOT"
  :description "FIXME: write description"
  :url "http://example.com/FIXME"
  :license {:name "EPL-2.0 OR GPL-2.0-or-later WITH Classpath-exception-2.0"
            :url "https://www.eclipse.org/legal/epl-2.0/"}
  :dependencies [[org.clojure/clojure "1.10.1"]
                 ;;[clj-http "3.10.0"]
                 [dvlopt/linux.gpio "1.0.0"]
                 [dvlopt/linux.i2c "1.1.1"]
                 [org.clojure/core.async "1.3.610"]
                 [org.clojure/tools.deps.alpha "0.9.857"]]
  :main ^:skip-aot hsec.core
  :target-path "target/%s"
  :profiles {:uberjar {:aot :all}}
  :plugins [
            ;; [refactor-nrepl "2.5.0"]
            [cider/cider-nrepl "0.25.5"]
            ]
  )
