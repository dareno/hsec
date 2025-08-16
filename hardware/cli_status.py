from __future__ import annotations

import argparse
import os
import sys
import time
from dataclasses import dataclass
from typing import Dict, Optional

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:  # pragma: no cover
    tomllib = None  # type: ignore

from .mcp23017 import MCP23017

# Best-effort reuse from tests fixture (optional)
try:  # pragma: no cover - runtime convenience
    from tests.hardware.fixtures.devices import bit_at as _bit_at
except Exception:  # pragma: no cover
    _bit_at = None


def bit_at(value: int, index: int) -> int:
    if _bit_at is not None:
        return _bit_at(value, index)
    return (value >> index) & 0x1


@dataclass(frozen=True)
class PortSpec:
    name: str  # e.g., gpa1
    kind: str  # 'reed' or 'pir'
    label: Optional[str] = None


DEFAULT_PORTS: Dict[str, PortSpec] = {
    # Defaults align with our HIL tests; can be overridden via TOML config
    "gpa1": PortSpec("gpa1", kind="pir", label="PIR on GPA1"),
    "gpa3": PortSpec("gpa3", kind="reed", label="kitchen door"),
    "gpa4": PortSpec("gpa4", kind="reed", label="family-room door"),
    "gpa6": PortSpec("gpa6", kind="reed", label="front door"),
    "gpa7": PortSpec("gpa7", kind="reed", label="basement door"),
    "gpb7": PortSpec("gpb7", kind="reed", label="main bedroom windows"),
}


def load_ports_from_toml(path: str) -> Dict[str, PortSpec]:
    if tomllib is None:
        return {}
    try:
        with open(path, "rb") as f:
            data = tomllib.load(f)
    except FileNotFoundError:
        return {}
    except Exception:
        return {}

    out: Dict[str, PortSpec] = {}
    ports = data.get("ports", {})
    for key, cfg in ports.items():
        name = key.lower()
        kind = str(cfg.get("type", "reed")).lower()
        if kind not in ("reed", "pir"):
            kind = "reed"
        label = cfg.get("label")
        out[name] = PortSpec(name=name, kind=kind, label=label)
    return out


def detect_config() -> Dict[str, PortSpec]:
    # Priority: CLI --config > $HSEC_PORTS_TOML > ./hsec.ports.toml > ~/.config/hsec/ports.toml
    paths = []
    env_path = os.getenv("HSEC_PORTS_TOML")
    if env_path:
        paths.append(env_path)
    paths.append(os.path.join(os.getcwd(), "hsec.ports.toml"))
    xdg = os.getenv("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
    paths.append(os.path.join(xdg, "hsec", "ports.toml"))

    merged: Dict[str, PortSpec] = {}
    for p in paths:
        merged.update(load_ports_from_toml(p))
    if merged:
        return merged
    return DEFAULT_PORTS.copy()


def parse_args(argv: list[str]) -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        prog="hsec-status",
        description=(
            "Watch MCP23017 ports and display door/window (reed) and PIR status."
        ),
    )
    ap.add_argument("--bus", type=int, default=int(os.getenv("HSEC_I2C_BUS", "1")), help="I2C bus number (default from HSEC_I2C_BUS or 1)")
    ap.add_argument(
        "--addr",
        type=lambda s: int(s, 0),
        default=int(os.getenv("HSEC_MCP23017_ADDR", "0x20"), 0),
        help="MCP23017 I2C address (e.g., 0x20)",
    )
    ap.add_argument(
        "--interval",
        type=float,
        default=0.5,
        help="Refresh interval in seconds (default 0.5)",
    )
    ap.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to ports TOML. Overrides env and defaults if provided.",
    )
    ap.add_argument(
        "--clear",
        action="store_true",
        help="Clear screen between updates (ANSI).",
    )
    return ap.parse_args(argv)


def smbus_open(bus_num: int):
    try:
        from smbus2 import SMBus  # lazy import
    except Exception as e:  # pragma: no cover
        print(f"error: smbus2 not available: {e}")
        sys.exit(2)
    try:
        return SMBus(bus_num)
    except FileNotFoundError as e:
        print(f"error: I2C bus /dev/i2c-{bus_num} not available: {e}")
        sys.exit(2)


def name_to_port_bit(name: str) -> tuple[str, int]:
    n = name.lower()
    if not (n.startswith("gpa") or n.startswith("gpb")):
        raise ValueError(f"Invalid port name '{name}', expected gpaX/gpbX")
    port = "A" if n[2] == "a" else "B"
    try:
        bit = int(n[3:])
    except ValueError:
        raise ValueError(f"Invalid bit index in '{name}'") from None
    if bit < 0 or bit > 7:
        raise ValueError(f"Bit index out of range in '{name}'")
    return port, bit


def render_status(kind: str, level: int) -> str:
    if kind == "pir":
        return "motion" if level == 1 else "no motion"
    # default reed/contact
    return "open" if level == 1 else "closed"


def format_rows(port_specs: Dict[str, PortSpec], a_val: int, b_val: int) -> list[str]:
    rows: list[str] = []
    for key in sorted(port_specs.keys()):
        spec = port_specs[key]
        port, bit = name_to_port_bit(spec.name)
        v = a_val if port == "A" else b_val
        lvl = bit_at(v, bit)
        state = render_status(spec.kind, lvl)
        label = f"  [{spec.label}]" if spec.label else ""
        rows.append(f"{spec.name:<5} {state:<9}{label}")
    return rows


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)

    # Resolve port specs
    port_specs = load_ports_from_toml(args.config) if args.config else detect_config()

    # Open bus and device
    bus = smbus_open(args.bus)
    dev = MCP23017(bus=bus, device_address=args.addr)

    try:
        while True:
            a_val, b_val = dev.read_ports()
            if args.clear:
                # ANSI clear screen & home
                sys.stdout.write("\x1b[2J\x1b[H")
            ts = time.strftime("%Y-%m-%d %H:%M:%S")
            print(f"hsec-status  {ts}  (A=0b{a_val:08b}  B=0b{b_val:08b})")
            for line in format_rows(port_specs, a_val, b_val):
                print(line)
            sys.stdout.flush()
            time.sleep(max(0.05, args.interval))
    except KeyboardInterrupt:
        return 0
    finally:
        try:
            bus.close()
        except Exception:
            pass

    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
