#!/usr/bin/env python3
"""
Tro Ly Tiet Kiem Dien - Phong Tro Sinh Vien
Mon: Thuat Toan | DP Group Knapsack vs Greedy
Chay: pip install rich  ->  python app.py
"""

import json
import math
import os
import sys
from dataclasses import dataclass, field
from datetime import date
from typing import List, Tuple

# Force UTF-8 cho Windows terminal
if sys.platform == "win32":
    os.system("chcp 65001 >nul 2>&1")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, FloatPrompt, IntPrompt, Prompt
from rich.table import Table

# ══════════════════════════════════════════════════════════════
# MODELS
# ══════════════════════════════════════════════════════════════

@dataclass
class Device:
    id: str
    name: str
    power_w: int            # Cong suat (Watt)
    priority: int           # Muc uu tien 1-5 (5 = khong the thieu)
    max_daily_hours: float  # Gio toi da su dung / ngay
    category: str

    def kwh(self, hours: float) -> float:
        return self.power_w * hours / 1000


@dataclass
class UsageEntry:
    device_id: str
    date: str   # YYYY-MM-DD
    hours: float
    note: str = ""


@dataclass
class Config:
    daily_budget_kwh: float = 2.0
    electricity_rate: float = 3500.0   # VND/kWh
    peak_hours: List[int] = field(default_factory=lambda: [17, 18, 19, 20, 21])


DEFAULT_DEVICES: List[Device] = [
    Device("ac",      "Dieu hoa",         900,  4,  8.0, "cooling"),
    Device("fan",     "Quat dien",          55,  5, 12.0, "cooling"),
    Device("light",   "Den LED",            15,  5, 12.0, "lighting"),
    Device("laptop",  "Laptop",             65,  5, 10.0, "computing"),
    Device("phone",   "Sac dien thoai",     10,  4,  4.0, "computing"),
    Device("heater",  "Binh nuoc nong",   2000,  3,  1.0, "heating"),
    Device("tv",      "Tivi",              100,  2,  4.0, "entertainment"),
    Device("rice",    "Noi com dien",      700,  5,  1.0, "cooking"),
    Device("fridge",  "Tu lanh mini",       80,  3, 24.0, "cooling"),
    Device("washing", "May giat",          500,  4,  1.0, "cleaning"),
]

# ══════════════════════════════════════════════════════════════
# STORAGE
# ══════════════════════════════════════════════════════════════

_DIR     = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
_DEVICES = os.path.join(_DIR, "devices.json")
_USAGE   = os.path.join(_DIR, "usage.json")
_CONFIG  = os.path.join(_DIR, "config.json")


def _ensure() -> None:
    os.makedirs(_DIR, exist_ok=True)


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


# ══════════════════════════════════════════════════════════════
# ALGORITHMS
# ══════════════════════════════════════════════════════════════
#
# BAI TOAN: GROUP KNAPSACK (Ba lo nhom)
# ─────────────────────────────────────
# Input:
#   n thiet bi, moi thiet bi i co:
#     power_w[i]  : cong suat (Watt)
#     priority[i] : muc uu tien (1-5)
#     max_hours[i]: gio toi da / ngay
#   W : ngan sach dien / ngay (kWh)
#
# Voi moi thiet bi i, chon h[i] trong {0, 0.5, 1, ..., max_h[i]}
#   Chi phi: cost(i,h) = power_w[i] x h / 1000  (kWh)
#   Loi ich: val(i,h)  = priority[i] x h         (diem thoai mai)
#
# Muc tieu: Toi da hoa sum(val(i,h[i]))
#           sao cho   sum(cost(i,h[i])) <= W
#
# Thuat toan 1 - DP (Group Knapsack): Optimal | O(n x W/d x H/step)
# Thuat toan 2 - Greedy (pri/watt)  : Xap xi  | O(n log n)
# ══════════════════════════════════════════════════════════════

BUDGET_UNIT = 0.01  # kWh / don vi ngan sach trong bang DP
HOUR_STEP   = 0.5   # buoc gio (0.5h = 30 phut)


@dataclass
class ScheduleItem:
    device: Device
    hours: float

    @property
    def kwh(self) -> float:
        return self.device.kwh(self.hours)

    @property
    def comfort(self) -> float:
        return self.device.priority * self.hours


@dataclass
class OptResult:
    schedule: List[ScheduleItem]
    total_comfort: float
    total_kwh: float
    algorithm: str
    complexity: str

    def total_cost(self, rate: float) -> float:
        return self.total_kwh * rate


def _options(dev: Device) -> List[Tuple[int, float, float]]:
    """Sinh cac lua chon (cost_units, comfort_value, hours) cho thiet bi."""
    result = []
    h = HOUR_STEP
    while h <= dev.max_daily_hours + 1e-9:
        # int(x + 0.5) thay round() de tranh banker's rounding cua Python 3
        cost_u = max(1, int(dev.kwh(h) / BUDGET_UNIT + 0.5))
        result.append((cost_u, dev.priority * h, h))
        h += HOUR_STEP
    return result


def dp_optimize(devices: List[Device], budget_kwh: float) -> OptResult:
    """
    Quy hoach dong - Group Knapsack.

    Trang thai:
      dp[i][j] = diem thoai mai toi da khi xet i thiet bi dau,
                 voi ngan sach j x BUDGET_UNIT kWh.

    Chuyen trang thai:
      dp[i+1][j] = max(
          dp[i][j],                               # khong dung thiet bi i
          max_h( dp[i][j - cost(i,h)] + val(i,h) ) # dung h gio
      )

    Truy vet:
      choice[i][j] = so gio chon cho thiet bi i khi dp[i+1][j] toi uu.

    Do phuc tap:
      Time : O(n x (W/d) x (max_h/step))
      Space: O(n x W/d)
      Vi du: n=10, W=2kWh, d=0.01, max_h=12h, step=0.5 -> ~96.000 phep tinh
    """
    n = len(devices)
    W = int(budget_kwh / BUDGET_UNIT) + 1

    dp     = [[0.0] * W for _ in range(n + 1)]
    choice = [[0.0] * W for _ in range(n)]

    for i, dev in enumerate(devices):
        opts = _options(dev)
        for j in range(W):
            dp[i + 1][j] = dp[i][j]   # mac dinh: khong dung thiet bi i
            choice[i][j] = 0.0
            for cost_u, val, h in opts:
                if j >= cost_u:
                    candidate = dp[i][j - cost_u] + val
                    if candidate > dp[i + 1][j]:
                        dp[i + 1][j] = candidate
                        choice[i][j] = h

    best_j = max(range(W), key=lambda j: dp[n][j])

    # Truy vet lich su dung tu bang choice
    schedule: List[ScheduleItem] = []
    j = best_j
    for i in range(n - 1, -1, -1):
        h = choice[i][j]
        if h > 0:
            cost_u = max(1, int(devices[i].kwh(h) / BUDGET_UNIT + 0.5))
            schedule.append(ScheduleItem(devices[i], h))
            j -= cost_u

    n_opts = max((len(_options(d)) for d in devices), default=1)
    return OptResult(
        schedule=sorted(schedule, key=lambda x: -x.comfort),
        total_comfort=dp[n][best_j],
        total_kwh=sum(s.kwh for s in schedule),
        algorithm="DP - Group Knapsack",
        complexity=(
            f"Time O(n*W/d*H/step) = O({n}*{W}*{n_opts}) ~ {n*W*n_opts:,} phep tinh | "
            f"Space O(n*W/d) = O({n}*{W}) = {n*W:,} o nho"
        ),
    )


def greedy_optimize(devices: List[Device], budget_kwh: float) -> OptResult:
    """
    Greedy: sap xep thiet bi theo ti le priority / power_w (giam dan).

    Y tuong: thiet bi uu tien cao, cong suat thap -> "hieu qua" hon.
    Lan luot cap phat ngan sach cho tung thiet bi theo thu tu do.

    Luu y: Greedy KHONG dam bao toi uu toan cuc (xem counterexample).

    Do phuc tap:
      Time : O(n log n)
      Space: O(n)
    """
    schedule: List[ScheduleItem] = []
    remaining = budget_kwh

    for dev in sorted(devices, key=lambda d: d.priority / d.power_w, reverse=True):
        if remaining < 1e-9:
            break
        hours = min(dev.max_daily_hours, remaining / (dev.power_w / 1000))
        hours = math.floor(hours / HOUR_STEP) * HOUR_STEP  # lam tron XUONG, khong vuot budget
        if hours >= HOUR_STEP:
            schedule.append(ScheduleItem(dev, hours))
            remaining -= dev.kwh(hours)

    return OptResult(
        schedule=sorted(schedule, key=lambda x: -x.comfort),
        total_comfort=sum(s.comfort for s in schedule),
        total_kwh=sum(s.kwh for s in schedule),
        algorithm="Greedy - Ti le Uu tien / Cong suat",
        complexity="Time O(n log n) | Space O(n)",
    )


def counterexample_demo() -> dict:
    """
    Phan vi du: Greedy thua DP trong 0/1 Knapsack.

    Budget = 0.30 kWh

    Thiet bi A - Loa Bluetooth: 200W, priority=3, max=1h
      ratio = 3/200 = 0.0150  (Greedy chon TRUOC vi ratio cao hon)
      cost  = 0.20 kWh | value = 3

    Thiet bi B - Dieu hoa nho: 300W, priority=4, max=1h
      ratio = 4/300 = 0.0133  (Greedy chon sau)
      cost  = 0.30 kWh | value = 4

    Greedy: chon A (0.20 kWh, +3 diem) -> con 0.10 kWh
            B can 0.30 kWh -> khong du -> bo qua
            Ket qua: 3 diem

    DP:     bo qua A, chon B (0.30 kWh, +4 diem)
            Ket qua: 4 diem  =>  DP THANG GREEDY!
    """
    loa  = Device("loa_demo", "Loa Bluetooth (demo)", 200, 3, 1.0, "entertainment")
    dh   = Device("dh_demo",  "Dieu hoa nho (demo)",  300, 4, 1.0, "cooling")
    devs = [loa, dh]
    dp_r = dp_optimize(devs, 0.30)
    gr_r = greedy_optimize(devs, 0.30)
    return {"dp": dp_r, "greedy": gr_r, "dp_wins": dp_r.total_comfort > gr_r.total_comfort + 1e-6}


def peak_aware_schedule(schedule: List[ScheduleItem], peak_hours: List[int]) -> dict:
    """
    Phan bo gio su dung thiet bi tranh gio cao diem.
    Thiet bi cong suat cao (>=500W) -> day sang gio thap diem truoc.
    """
    peak_set = set(peak_hours)
    off_peak = [h for h in range(24) if h not in peak_set]
    peak_asc = sorted(peak_hours)
    result   = {}
    for item in schedule:
        slots = []
        left  = item.hours
        pool  = off_peak if item.device.power_w >= 500 else (off_peak + peak_asc)
        for h in pool:
            if left < 1e-9:
                break
            used = min(1.0, left)
            slots.append((h, used))
            left -= used
        result[item.device.id] = slots
    return result


# ══════════════════════════════════════════════════════════════
# UI
# ══════════════════════════════════════════════════════════════

console = Console(highlight=False)

PRIORITY_LABEL = {
    5: "[green]5/5[/green]", 4: "[cyan]4/5[/cyan]",
    3: "[yellow]3/5[/yellow]", 2: "[white]2/5[/white]", 1: "[dim]1/5[/dim]",
}


def clear() -> None:
    console.clear()


def pause() -> None:
    console.print("\n[dim]Nhan Enter de tiep tuc...[/dim]")
    input()


def header() -> None:
    console.print(Panel.fit(
        "[bold cyan]TRO LY TIET KIEM DIEN[/bold cyan]\n"
        "[dim]Phong tro sinh vien  |  DP Group Knapsack + Greedy[/dim]",
        border_style="cyan", padding=(0, 4),
    ))


def main_menu() -> str:
    rows = [
        ("1", "Quan ly thiet bi dien"),
        ("2", "Ghi nhat ky su dung hom nay"),
        ("3", "Thong ke dien nang"),
        ("4", "Toi uu lich su dung  [bold](DP vs Greedy)[/bold]"),
        ("5", "Lich dung tranh gio cao diem"),
        ("6", "Cai dat"),
        ("0", "Thoat"),
    ]
    t = Table(box=box.ROUNDED, border_style="cyan", show_header=False, padding=(0, 1))
    t.add_column(width=4, style="bold yellow", no_wrap=True)
    t.add_column()
    for k, v in rows:
        t.add_row(f"[{k}]", v)
    console.print(t)
    return Prompt.ask("[bold]Chon[/bold]", choices=["0","1","2","3","4","5","6"])


# ── 1. Quan ly thiet bi ───────────────────────────────────────

def menu_devices() -> None:
    while True:
        clear(); header()
        devices = load_devices()
        t = Table(title="Danh Sach Thiet Bi", box=box.SIMPLE_HEAD, header_style="bold cyan")
        t.add_column("ID", style="dim", width=10)
        t.add_column("Ten thiet bi", min_width=20)
        t.add_column("Cong suat", justify="right")
        t.add_column("Uu tien", justify="center")
        t.add_column("Max gio/ngay", justify="right")
        t.add_column("Loai", style="dim")
        for d in devices:
            t.add_row(d.id, d.name, f"{d.power_w}W",
                      PRIORITY_LABEL.get(d.priority, str(d.priority)),
                      f"{d.max_daily_hours}h", d.category)
        console.print(t)
        console.print("\n[1] Them  [2] Xoa  [3] Khoi phuc mac dinh  [0] Quay lai")
        ch = Prompt.ask("Chon", choices=["0","1","2","3"])
        if ch == "0":
            break
        elif ch == "1":
            dev_id = Prompt.ask("  ID (viet lien, khong dau)")
            if any(d.id == dev_id for d in devices):
                console.print("[red]  ID da ton tai![/red]"); pause(); continue
            name     = Prompt.ask("  Ten thiet bi")
            power    = IntPrompt.ask("  Cong suat (Watt)")
            priority = IntPrompt.ask("  Muc uu tien 1-5", default=3)
            max_h    = FloatPrompt.ask("  Gio toi da / ngay", default=8.0)
            category = Prompt.ask("  Loai", default="other")
            devices.append(Device(dev_id, name, power, max(1, min(5, priority)), max_h, category))
            save_devices(devices)
            console.print("[green]  Da them![/green]"); pause()
        elif ch == "2":
            dev_id = Prompt.ask("Nhap ID thiet bi can xoa")
            idx = next((i for i, d in enumerate(devices) if d.id == dev_id), None)
            if idx is None:
                console.print("[red]Khong tim thay.[/red]")
            else:
                console.print(f"[yellow]Da xoa: {devices.pop(idx).name}[/yellow]")
                save_devices(devices)
            pause()
        elif ch == "3":
            if Confirm.ask("Khoi phuc danh sach mac dinh?"):
                save_devices(list(DEFAULT_DEVICES))
                console.print("[green]Da khoi phuc![/green]"); pause()


# ── 2. Nhat ky su dung ───────────────────────────────────────

def menu_usage() -> None:
    clear(); header()
    devices = load_devices()
    usage   = load_usage()
    config  = load_config()
    today   = date.today().isoformat()

    console.print(f"[bold]Ghi nhat ky - [cyan]{today}[/cyan][/bold]\n")

    today_log = [e for e in usage if e.date == today]
    if today_log:
        dev_map = {d.id: d for d in devices}
        t = Table(box=box.SIMPLE, header_style="bold", title="Da ghi hom nay")
        t.add_column("Thiet bi")
        t.add_column("Gio", justify="right")
        t.add_column("kWh", justify="right")
        t.add_column("Chi phi (VND)", justify="right")
        total_kwh = 0.0
        for e in today_log:
            dev = dev_map.get(e.device_id)
            kwh = dev.kwh(e.hours) if dev else 0.0
            total_kwh += kwh
            t.add_row(dev.name if dev else e.device_id, f"{e.hours}h",
                      f"{kwh:.3f}", f"{kwh * config.electricity_rate:,.0f}")
        t.add_section()
        t.add_row("[bold]Tong[/bold]", "",
                  f"[bold]{total_kwh:.3f}[/bold]",
                  f"[bold]{total_kwh * config.electricity_rate:,.0f}[/bold]")
        console.print(t)
        if total_kwh <= config.daily_budget_kwh:
            console.print("  Trang thai: [green]Trong ngan sach[/green]\n")
        else:
            console.print(f"  Trang thai: [red]Vuot {total_kwh - config.daily_budget_kwh:.2f} kWh![/red]\n")

    console.print("[dim]Nhap so gio da dung (de trong = bo qua):[/dim]")
    changed = False
    for dev in devices:
        h_str = Prompt.ask(
            f"  {dev.name} [dim]({dev.power_w}W, toi da {dev.max_daily_hours}h)[/dim]",
            default="").strip()
        if not h_str:
            continue
        try:
            hours = float(h_str)
            if not (0 <= hours <= dev.max_daily_hours):
                console.print(f"[red]    Gio khong hop le (0-{dev.max_daily_hours}h)[/red]"); continue
            usage = [e for e in usage if not (e.date == today and e.device_id == dev.id)]
            if hours > 0:
                usage.append(UsageEntry(dev.id, today, hours))
            changed = True
        except ValueError:
            console.print("[red]    Bo qua (khong phai so)[/red]")

    if changed:
        save_usage(usage)
        console.print("\n[green]Da luu nhat ky![/green]")
    pause()


# ── 3. Thong ke ──────────────────────────────────────────────

def menu_stats() -> None:
    clear(); header()
    devices = load_devices()
    usage   = load_usage()
    config  = load_config()
    dev_map = {d.id: d for d in devices}

    if not usage:
        console.print("[yellow]Chua co du lieu. Hay ghi nhat ky truoc.[/yellow]")
        pause(); return

    console.print("[bold cyan]Thong ke theo ngay (14 ngay gan nhat):[/bold cyan]")
    t = Table(box=box.SIMPLE_HEAD, header_style="bold")
    t.add_column("Ngay"); t.add_column("kWh", justify="right")
    t.add_column("Chi phi (VND)", justify="right"); t.add_column("Trang thai", justify="center")
    dates = sorted(set(e.date for e in usage))[-14:]
    for d in dates:
        kwh = sum(dev_map[e.device_id].kwh(e.hours)
                  for e in usage if e.date == d and e.device_id in dev_map)
        t.add_row(d, f"{kwh:.2f}", f"{kwh * config.electricity_rate:,.0f}",
                  "[green]Tot[/green]" if kwh <= config.daily_budget_kwh else "[red]Vuot![/red]")
    console.print(t)

    console.print("\n[bold cyan]Tong dien theo thiet bi:[/bold cyan]")
    t2 = Table(box=box.SIMPLE, header_style="bold")
    t2.add_column("Thiet bi"); t2.add_column("Tong gio", justify="right")
    t2.add_column("Tong kWh", justify="right"); t2.add_column("Chi phi (VND)", justify="right")
    for dev in sorted(devices, key=lambda d: -sum(e.hours for e in usage if e.device_id == d.id)):
        total_h = sum(e.hours for e in usage if e.device_id == dev.id)
        if total_h == 0:
            continue
        kwh = dev.kwh(total_h)
        t2.add_row(dev.name, f"{total_h:.1f}h", f"{kwh:.2f}", f"{kwh * config.electricity_rate:,.0f}")
    console.print(t2)

    if dates:
        avg = sum(dev_map[e.device_id].kwh(e.hours)
                  for e in usage if e.device_id in dev_map) / len(dates)
        console.print(f"\n  Trung binh/ngay: [bold]{avg:.2f}[/bold] kWh  "
                      f"->  Uoc tinh/thang: [bold cyan]{avg * 30 * config.electricity_rate:,.0f}[/bold cyan] VND")
    pause()


# ── 4. Toi uu DP vs Greedy ────────────────────────────────────

def menu_optimize() -> None:
    clear(); header()
    devices = load_devices()
    config  = load_config()

    console.print(Panel(
        "[bold]Toi Uu Lich Su Dung Dien[/bold]\n\n"
        "So sanh hai thuat toan:\n"
        "  [cyan](1) DP Group Knapsack[/cyan]  --  Toi uu toan cuc,  O(n x W x H)\n"
        "  [yellow](2) Greedy (pri/watt)[/yellow]   --  Xap xi nhanh,   O(n log n)",
        border_style="blue", padding=(0, 2),
    ))

    budget = FloatPrompt.ask("\nNgan sach dien / ngay (kWh)", default=config.daily_budget_kwh)
    console.print()

    dp_res = dp_optimize(devices, budget)
    gr_res = greedy_optimize(devices, budget)

    _print_result(dp_res, config.electricity_rate, "cyan")
    _print_result(gr_res, config.electricity_rate, "yellow")

    diff = dp_res.total_comfort - gr_res.total_comfort
    body = (
        f"  [cyan]DP[/cyan]     comfort: [bold]{dp_res.total_comfort:.1f}[/bold]"
        f"  dien: {dp_res.total_kwh:.2f} kWh"
        f"  chi phi: {dp_res.total_cost(config.electricity_rate):,.0f} VND\n"
        f"  [yellow]Greedy[/yellow] comfort: [bold]{gr_res.total_comfort:.1f}[/bold]"
        f"  dien: {gr_res.total_kwh:.2f} kWh"
        f"  chi phi: {gr_res.total_cost(config.electricity_rate):,.0f} VND\n\n"
    )
    if diff > 1e-3:
        body += f"  [green]DP tot hon Greedy +{diff:.1f} diem ({diff / max(gr_res.total_comfort, 1e-9) * 100:.1f}%)[/green]"
    elif diff < -1e-3:
        body += f"  [yellow]Greedy tot hon DP +{-diff:.1f} diem (hiem gap)[/yellow]"
    else:
        body += "  [dim]Hai thuat toan cho ket qua bang nhau trong truong hop nay.[/dim]"

    console.print(Panel(body, title="[bold]Ket qua so sanh[/bold]", border_style="green", padding=(0, 2)))

    if Confirm.ask("\nXem phan vi du DP tot hon Greedy?", default=False):
        demo = counterexample_demo()
        console.print(Panel(
            f"[bold]Phan vi du: Greedy that bai trong 0/1 Knapsack[/bold]\n\n"
            f"Budget: 0.30 kWh\n\n"
            f"  Loa Bluetooth: 200W, pri=3  -> ratio=3/200=0.0150  [yellow](Greedy chon TRUOC)[/yellow]\n"
            f"  Dieu hoa nho : 300W, pri=4  -> ratio=4/300=0.0133  [dim](Greedy bo qua)[/dim]\n\n"
            f"  [yellow]Greedy[/yellow]: chon Loa (0.20kWh,+3diem) -> con 0.10kWh -> Dieu hoa can 0.30 -> khong du\n"
            f"           Tong: [bold yellow]{demo['greedy'].total_comfort:.0f} diem[/bold yellow]\n\n"
            f"  [cyan]DP[/cyan]    : bo qua Loa, chon Dieu hoa (0.30kWh,+4diem)\n"
            f"           Tong: [bold cyan]{demo['dp'].total_comfort:.0f} diem[/bold cyan]\n\n"
            f"  [green]=> DP tot hon Greedy +{demo['dp'].total_comfort - demo['greedy'].total_comfort:.0f} diem![/green]\n\n"
            f"  Nguyen nhan: Greedy 'tham lam' chon item ti le cao truoc, can mat budget\n"
            f"  khien khong con cho item co gia tri thuc su cao hon.",
            title="[bold red]Counter-example[/bold red]", border_style="red", padding=(0, 2),
        ))
    pause()


def _print_result(res: OptResult, rate: float, style: str) -> None:
    t = Table(title=f"[{style}]{res.algorithm}[/{style}]",
              box=box.ROUNDED, header_style=f"bold {style}")
    t.add_column("Thiet bi", min_width=20)
    t.add_column("Gio",     justify="right")
    t.add_column("kWh",     justify="right")
    t.add_column("Comfort", justify="right")
    for item in res.schedule:
        t.add_row(item.device.name, f"{item.hours}h", f"{item.kwh:.3f}", f"{item.comfort:.1f}")
    t.add_section()
    t.add_row("[bold]Tong[/bold]", "",
              f"[bold]{res.total_kwh:.3f}[/bold]", f"[bold]{res.total_comfort:.1f}[/bold]")
    console.print(t)
    console.print(
        f"  Chi phi: [bold]{res.total_cost(rate):,.0f}[/bold] VND/ngay  "
        f"[dim]({res.total_cost(rate) * 30:,.0f} VND/thang)[/dim]\n"
        f"  [dim]Do phuc tap: {res.complexity}[/dim]\n"
    )


# ── 5. Lich tranh gio cao diem ────────────────────────────────

def menu_peak() -> None:
    clear(); header()
    devices = load_devices()
    config  = load_config()

    console.print("[bold]Phan Bo Gio Dung Dien - Tranh Gio Cao Diem[/bold]")
    console.print(f"Gio cao diem: [red]{' '.join(str(h)+'h' for h in config.peak_hours)}[/red]\n")

    budget = FloatPrompt.ask("Ngan sach / ngay (kWh)", default=config.daily_budget_kwh)
    dp_res = dp_optimize(devices, budget)
    sched  = peak_aware_schedule(dp_res.schedule, config.peak_hours)

    console.print("\n[bold cyan]Timeline 24 gio (moi o = 1 gio):[/bold cyan]\n")
    console.print(f"  {'Thiet bi':<20} {''.join(f'{h:02d}' for h in range(24))}")
    console.print(f"  {'':<20} {'--' * 24}")
    for item in dp_res.schedule:
        peak_set = set(config.peak_hours)
        row = ["  "] * 24
        for h in peak_set:
            if 0 <= h < 24:
                row[h] = "!!"
        for (sh, dur) in sched.get(item.device.id, []):
            for h in range(sh, min(sh + int(dur + 0.5), 24)):
                row[h] = "##"
        bar = "".join(
            f"[green]##[/green]" if c == "##" else
            f"[red]!![/red]"    if c == "!!" else
            f"[dim]..[/dim]"    for c in row
        )
        console.print(f"  {item.device.name:<20} {bar}  [dim]{item.hours}h - {item.kwh:.2f}kWh[/dim]")

    console.print("\n  Chu thich: [green]##[/green] dung dien  [red]!![/red] gio cao diem  [dim]..[/dim] khong dung\n")
    pause()


# ── 6. Cai dat ───────────────────────────────────────────────

def menu_settings() -> None:
    clear(); header()
    config = load_config()
    console.print("[bold]Cai Dat Hien Tai:[/bold]\n")
    console.print(f"  Ngan sach / ngay : [cyan]{config.daily_budget_kwh}[/cyan] kWh")
    console.print(f"  Gia dien          : [cyan]{config.electricity_rate:,.0f}[/cyan] VND/kWh")
    console.print(f"  Gio cao diem      : [red]{', '.join(str(h)+'h' for h in config.peak_hours)}[/red]\n")
    if not Confirm.ask("Cap nhat cai dat?"):
        return
    config.daily_budget_kwh = FloatPrompt.ask("Ngan sach / ngay (kWh)", default=config.daily_budget_kwh)
    config.electricity_rate = FloatPrompt.ask("Gia dien (VND/kWh)", default=config.electricity_rate)
    peak_str = Prompt.ask("Gio cao diem (cach nhau bang dau phay)",
                          default=",".join(str(h) for h in config.peak_hours))
    try:
        config.peak_hours = [int(x.strip()) for x in peak_str.split(",")]
    except ValueError:
        console.print("[red]Dinh dang khong hop le, giu nguyen.[/red]")
    save_config(config)
    console.print("[green]Da luu cai dat![/green]")
    pause()


# ══════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════

def main() -> None:
    dispatch = {
        "1": menu_devices, "2": menu_usage, "3": menu_stats,
        "4": menu_optimize, "5": menu_peak, "6": menu_settings,
    }
    while True:
        clear(); header()
        ch = main_menu()
        if ch == "0":
            console.print("\n[cyan]Tam biet! Tiet kiem dien nhe![/cyan]\n")
            break
        dispatch[ch]()


if __name__ == "__main__":
    main()
