"""
MCP23017 register configuration loader and applier (Infrastructure / Hardware BC).

- Loads YAML from `config/mcp23017.yaml` (schema_version: 1)
- Normalizes to register bytes for BANK=0 addressing
- Applies configuration to a `hardware.mcp23017.MCP23017` instance

DDD placement: This module lives in Infrastructure (Hardware BC). It is a
pure adapter around the chip and external configuration; the Domain does not
reference it.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Literal, Optional, Tuple

try:
    import yaml  # type: ignore
except Exception as e:  # pragma: no cover
    raise RuntimeError(
        "PyYAML is required to load MCP23017 config. Install with 'pip install PyYAML'."
    ) from e

# BANK=0 register addresses (sequential)
IODIRA = 0x00
IODIRB = 0x01
IPOLA = 0x02
IPOLB = 0x03
GPINTENA = 0x04
GPINTENB = 0x05
DEFVALA = 0x06
DEFVALB = 0x07
INTCONA = 0x08
INTCONB = 0x09
IOCON = 0x0A  # (also at 0x0B)
GPPUA = 0x0C
GPPUB = 0x0D
INTCAPA = 0x10
INTCAPB = 0x11
GPIOA = 0x12
GPIOB = 0x13

ClearStrategy = Literal["read_ports", "read_intcap"]
IntMode = Literal["change", "compare_defval"]
PolarityHL = Literal["high", "low"]
DriverKind = Literal["push_pull", "open_drain"]


@dataclass(frozen=True)
class PortInterruptCfg:
    enable: int = 0xFF
    mode: IntMode = "change"
    defval: int = 0xFF


@dataclass(frozen=True)
class PortCfg:
    direction: int = 0xFF
    pullup: int = 0x00
    polarity_invert: int = 0x00
    interrupt: PortInterruptCfg = PortInterruptCfg()


@dataclass(frozen=True)
class IOCONCfg:
    bank: Literal["bank0", "bank1"] = "bank0"
    mirror: bool = True
    sequential_op: bool = True  # SEQOP=0 when True
    slew_rate_limit: bool = True  # DISSLW=0 when True
    hardware_addr_enable: bool = False  # MCP23S17 only
    open_drain: bool = False
    int_polarity: PolarityHL = "high"


@dataclass(frozen=True)
class InterruptMeta:
    pin: str = "BCM5"
    mirror_ports: bool = True
    driver: DriverKind = "push_pull"
    polarity: Literal["active_high", "active_low"] = "active_high"
    clear_on: ClearStrategy = "read_ports"


@dataclass(frozen=True)
class HardwareMeta:
    bus: int = 1
    address: int = 0x20


@dataclass(frozen=True)
class Config:
    schema_version: int
    chip: str
    hardware: HardwareMeta
    interrupt: InterruptMeta
    iocon: IOCONCfg
    ports: Dict[str, PortCfg]
    per_pins: Optional[list] = None
    post_setup_clear: bool = True


def _get(d: dict, path: Tuple[str, ...], default):
    cur = d
    for k in path:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur


def _bit_set(byte: int, bit: int, value: int) -> int:
    mask = 1 << bit
    return (byte | mask) if value else (byte & ~mask)


def _parse_pin(pin: str) -> Tuple[str, int]:
    p = pin.strip().lower()
    if not (p.startswith("gpa") or p.startswith("gpb")):
        raise ValueError(f"invalid pin '{pin}', expected GPAx/GPBx")
    port = "A" if p[2] == "a" else "B"
    idx = int(p[3:])
    if not (0 <= idx <= 7):
        raise ValueError(f"bit index out of range in '{pin}'")
    return port, idx


def load_yaml(path: str) -> Config:
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    schema_version = int(raw.get("schema_version", 1))
    chip = str(raw.get("chip", "MCP23017"))

    hw = HardwareMeta(
        bus=int(_get(raw, ("hardware", "i2c", "bus"), 1)),
        address=int(_get(raw, ("hardware", "i2c", "address"), 0x20)),
    )
    intr = InterruptMeta(
        pin=str(_get(raw, ("hardware", "interrupt", "pin"), "BCM5")),
        mirror_ports=bool(_get(raw, ("hardware", "interrupt", "mirror_ports"), True)),
        driver=str(_get(raw, ("hardware", "interrupt", "driver"), "push_pull")),
        polarity=str(_get(raw, ("hardware", "interrupt", "polarity"), "active_high")),
        clear_on=str(_get(raw, ("hardware", "interrupt", "clear_on"), "read_ports")),
    )
    iocon = IOCONCfg(
        bank=str(_get(raw, ("iocon", "bank"), "bank0")),
        mirror=bool(_get(raw, ("iocon", "mirror"), True)),
        sequential_op=bool(_get(raw, ("iocon", "sequential_op"), True)),
        slew_rate_limit=bool(_get(raw, ("iocon", "slew_rate_limit"), True)),
        hardware_addr_enable=bool(_get(raw, ("iocon", "hardware_addr_enable"), False)),
        open_drain=bool(_get(raw, ("iocon", "open_drain"), False)),
        int_polarity=str(_get(raw, ("iocon", "int_polarity"), "high")),
    )

    def _port(name: str) -> PortCfg:
        p = raw.get("ports", {}).get(name, {})
        intr_p = p.get("interrupt", {}) if isinstance(p, dict) else {}
        return PortCfg(
            direction=int(p.get("direction", 0xFF)),
            pullup=int(p.get("pullup", 0x00)),
            polarity_invert=int(p.get("polarity_invert", 0x00)),
            interrupt=PortInterruptCfg(
                enable=int(intr_p.get("enable", 0xFF)),
                mode=str(intr_p.get("mode", "change")),
                defval=int(intr_p.get("defval", 0xFF)),
            ),
        )

    ports = {"A": _port("A"), "B": _port("B")}

    cfg = Config(
        schema_version=schema_version,
        chip=chip,
        hardware=hw,
        interrupt=intr,
        iocon=iocon,
        ports=ports,
        per_pins=raw.get("per_pins"),
        post_setup_clear=bool(_get(raw, ("post_setup", "clear_interrupt"), True)),
    )
    return cfg


def _iocon_byte(cfg: IOCONCfg) -> int:
    b = 0
    if cfg.bank == "bank1":
        b |= 0x80
    if cfg.mirror:
        b |= 0x40
    # SEQOP: 1=disable sequential; we want True → enable → bit=0
    if not cfg.sequential_op:
        b |= 0x20
    # DISSLW: 1=disable slew rate; True means limit (enable SR) → bit=0
    if not cfg.slew_rate_limit:
        b |= 0x10
    # HAEN (SPI only); leave as 0
    if cfg.open_drain:
        b |= 0x04
    if cfg.int_polarity == "high":
        b |= 0x02
    return b


def _merge_per_pin_overrides(base: Dict[str, int], overrides: Optional[list]) -> Dict[str, int]:
    if not overrides:
        return base
    iodirA, iodirB = base[IODIRA], base[IODIRB]
    gppuA, gppuB = base[GPPUA], base[GPPUB]
    ipolA, ipolB = base[IPOLA], base[IPOLB]
    gpintA, gpintB = base[GPINTENA], base[GPINTENB]
    intconA, intconB = base[INTCONA], base[INTCONB]
    defvalA, defvalB = base[DEFVALA], base[DEFVALB]

    for item in overrides:
        pin = str(item.get("pin"))
        if not pin:
            continue
        port, bit = _parse_pin(pin)
        isA = port == "A"

        # Direction
        if "direction" in item:
            if isA:
                iodirA = _bit_set(iodirA, bit, 1 if item["direction"] else 0)
            else:
                iodirB = _bit_set(iodirB, bit, 1 if item["direction"] else 0)
        # Pull-up
        if "pullup" in item:
            if isA:
                gppuA = _bit_set(gppuA, bit, 1 if item["pullup"] else 0)
            else:
                gppuB = _bit_set(gppuB, bit, 1 if item["pullup"] else 0)
        # Polarity invert
        if "polarity_invert" in item:
            if isA:
                ipolA = _bit_set(ipolA, bit, 1 if item["polarity_invert"] else 0)
            else:
                ipolB = _bit_set(ipolB, bit, 1 if item["polarity_invert"] else 0)
        # Interrupt subfields
        intr = item.get("interrupt") or {}
        if "enable" in intr:
            if isA:
                gpintA = _bit_set(gpintA, bit, 1 if intr["enable"] else 0)
            else:
                gpintB = _bit_set(gpintB, bit, 1 if intr["enable"] else 0)
        if "mode" in intr:
            mode = str(intr["mode"]).lower()
            if mode not in ("change", "compare_defval"):
                mode = "change"
            bit_val = 1 if mode == "compare_defval" else 0
            if isA:
                intconA = _bit_set(intconA, bit, bit_val)
            else:
                intconB = _bit_set(intconB, bit, bit_val)
        if "defval" in intr:
            bit_val = 1 if int(intr["defval"]) else 0
            if isA:
                defvalA = _bit_set(defvalA, bit, bit_val)
            else:
                defvalB = _bit_set(defvalB, bit, bit_val)

    base.update(
        {
            IODIRA: iodirA,
            IODIRB: iodirB,
            GPPUA: gppuA,
            GPPUB: gppuB,
            IPOLA: ipolA,
            IPOLB: ipolB,
            GPINTENA: gpintA,
            GPINTENB: gpintB,
            INTCONA: intconA,
            INTCONB: intconB,
            DEFVALA: defvalA,
            DEFVALB: defvalB,
        }
    )
    return base


def compute_register_bytes(cfg: Config) -> Dict[int, int]:
    """Return a mapping of register address -> byte value according to cfg.

    Only includes registers we program explicitly (direction, pull-ups, polarity,
    interrupt enable/mode/defval, IOCON).
    """
    # Port defaults
    def _intcon(mode: IntMode) -> int:
        return 0x00 if mode == "change" else 0xFF

    base = {
        IODIRA: cfg.ports["A"].direction & 0xFF,
        IODIRB: cfg.ports["B"].direction & 0xFF,
        GPPUA: cfg.ports["A"].pullup & 0xFF,
        GPPUB: cfg.ports["B"].pullup & 0xFF,
        IPOLA: cfg.ports["A"].polarity_invert & 0xFF,
        IPOLB: cfg.ports["B"].polarity_invert & 0xFF,
        GPINTENA: cfg.ports["A"].interrupt.enable & 0xFF,
        GPINTENB: cfg.ports["B"].interrupt.enable & 0xFF,
        INTCONA: _intcon(cfg.ports["A"].interrupt.mode),
        INTCONB: _intcon(cfg.ports["B"].interrupt.mode),
        DEFVALA: cfg.ports["A"].interrupt.defval & 0xFF,
        DEFVALB: cfg.ports["B"].interrupt.defval & 0xFF,
        IOCON: _iocon_byte(cfg.iocon),
    }

    # Merge any per-pin overrides
    out = _merge_per_pin_overrides(base, cfg.per_pins)
    return out


def apply_config(dev, cfg: Config) -> None:
    """Write configuration to the device via its I2C bus.

    Args:
        dev: hardware.mcp23017.MCP23017 instance
        cfg: Config
    """
    regs = compute_register_bytes(cfg)
    bus = dev.bus
    addr = dev.device_address

    # Program IOCON first (polarity/driver/mirror)
    bus.write_byte_data(addr, IOCON, regs[IOCON])

    # Program per-port registers
    for reg in (IODIRA, IODIRB, IPOLA, IPOLB, GPPUA, GPPUB, DEFVALA, DEFVALB, INTCONA, INTCONB, GPINTENA, GPINTENB):
        bus.write_byte_data(addr, reg, regs[reg])

    # Optional initial clear
    if cfg.post_setup_clear:
        if cfg.interrupt.clear_on == "read_intcap":
            _ = bus.read_byte_data(addr, INTCAPA)
            _ = bus.read_byte_data(addr, INTCAPB)
        else:
            _ = dev.read_ports()


def load_and_apply(dev, path: str) -> Config:
    cfg = load_yaml(path)
    apply_config(dev, cfg)
    return cfg
