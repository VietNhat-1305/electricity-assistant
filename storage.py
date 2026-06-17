import json
import os
from typing import List

from models import Config, DEFAULT_DEVICES, Device, UsageEntry

_DIR     = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
_DEVICES = os.path.join(_DIR, "devices.json")
_USAGE   = os.path.join(_DIR, "usage.json")
_CONFIG  = os.path.join(_DIR, "config.json")


def _ensure() -> None:
    os.makedirs(_DIR, exist_ok=True)


# ── Devices ───────────────────────────────────────────────────

def load_devices() -> List[Device]:
    _ensure()
    if not os.path.exists(_DEVICES):
        save_devices(list(DEFAULT_DEVICES))
        return list(DEFAULT_DEVICES)
    with open(_DEVICES, encoding="utf-8") as f:
        return [Device(**d) for d in json.load(f)]


def save_devices(devices: List[Device]) -> None:
    _ensure()
    with open(_DEVICES, "w", encoding="utf-8") as f:
        json.dump([d.__dict__ for d in devices], f, ensure_ascii=False, indent=2)


# ── Usage log ─────────────────────────────────────────────────

def load_usage() -> List[UsageEntry]:
    _ensure()
    if not os.path.exists(_USAGE):
        return []
    with open(_USAGE, encoding="utf-8") as f:
        return [UsageEntry(**e) for e in json.load(f)]


def save_usage(entries: List[UsageEntry]) -> None:
    _ensure()
    with open(_USAGE, "w", encoding="utf-8") as f:
        json.dump([e.__dict__ for e in entries], f, ensure_ascii=False, indent=2)


# ── Config ────────────────────────────────────────────────────

def load_config() -> Config:
    _ensure()
    if not os.path.exists(_CONFIG):
        return Config()
    with open(_CONFIG, encoding="utf-8") as f:
        return Config(**json.load(f))


def save_config(cfg: Config) -> None:
    _ensure()
    with open(_CONFIG, "w", encoding="utf-8") as f:
        json.dump(cfg.__dict__, f, ensure_ascii=False, indent=2)
