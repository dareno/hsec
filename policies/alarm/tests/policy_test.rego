package hsec.alarm.tests

import data.hsec.alarm as alarm

# Happy path: armed and changed → allow=true, reasons include armed & change

test_allow_when_armed_and_changed {
  input := {
    "operation": "alarm.evaluate",
    "state": {"prev": 0.0, "curr": 1.0},
    "config": {"armed": true}
  }
  alarm.allow with input as input
  some r
  r := alarm.reasons[_]
  r == "armed" or r == "change"
}

# Not armed → allow=false

test_deny_when_not_armed {
  input := {
    "operation": "alarm.evaluate",
    "state": {"prev": 0.0, "curr": 1.0},
    "config": {"armed": false}
  }
  not alarm.allow with input as input
}

# No change → allow=false even if armed

test_deny_when_no_change {
  input := {
    "operation": "alarm.evaluate",
    "state": {"prev": 0.0, "curr": 0.0},
    "config": {"armed": true}
  }
  not alarm.allow with input as input
}
