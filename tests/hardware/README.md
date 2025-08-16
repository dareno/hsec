# Hardware-in-the-loop (HIL) tests

## Environment variables
- HSEC_I2C_BUS (default: 1)
- HSEC_MCP23017_ADDR (default: 0x20)
- HSEC_INT_GPIO (optional; BCM number for Pi INT line)

## Install deps
```
uv sync --group test --group hardware
```

## Run hardware tests
```
uv run pytest -m hardware
```

## Notes
- Default test runs exclude hardware via pytest addopts.
- INT line uses Raspberry Pi internal pull-down; debounce ~50 ms.
- MCP23017 in any-change mode; consider INTCAP for latched reads.
