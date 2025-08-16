package hsec.alarm

# Minimal alarm evaluation policy.
# Intentionally simple to avoid freezing schema; expands over time.

default allow = false

# Operation must be the expected alarm evaluation call.
operation_is_alarm {
  input.operation == "alarm.evaluate"
}

# Sensor state changed (edge detect)
changed {
  input.state.prev != input.state.curr
}

# System (or subject) is armed.
# Accept either a flat boolean or nested structure for flexibility.
is_armed {
  input.config.armed == true
}

allow {
  operation_is_alarm
  is_armed
  changed
}

# Optional: expose reasons for transparency. These do not affect allow directly.
reasons["armed"] {
  is_armed
}

reasons["change"] {
  changed
}
