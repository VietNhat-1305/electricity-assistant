#!/usr/bin/env python3
"""
Tro Ly Tiet Kiem Dien - Phong Tro Sinh Vien
Mon: Thuat Toan | DP Group Knapsack vs Greedy
"""

import os
import sys

# Force UTF-8 cho Windows terminal (cmd / PowerShell)
if sys.platform == "win32":
    os.system("chcp 65001 >nul 2>&1")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from datetime import date

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, FloatPrompt, IntPrompt, Prompt
from rich.table import Table

import algorithms
import storage
from models import DEFAULT_DEVICES, Device, UsageEntry

console = Console(highlight=False)

PRIORITY_LABEL = {
    5: "[green]5/5[/green]",
    4: "[cyan]4/5[/cyan]",
    3: "[yellow]3/5[/yellow]",
    2: "[white]2/5[/white]",
    1: "[dim]1/5[/dim]",
}


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────

def clear() -> None:
    console.clear()


def pause() -> None:
    console.print("\n[dim]Nhan Enter de tiep tuc...[/dim]")
    input()


def header() -> None:
    console.print(Panel.fit(
        "[bold cyan]TRO LY TIET KIEM DIEN[/bold cyan]\n"
        "[dim]Phong tro sinh vien  |  DP Group Knapsack + Greedy[/dim]",
        border_style="cyan",
        padding=(0, 4),
    ))


# ─────────────────────────────────────────────────────────────
# Menu chinh
# ─────────────────────────────────────────────────────────────

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
    return Prompt.ask("[bold]Chon[/bold]", choices=["0", "1", "2", "3", "4", "5", "6"])


# ─────────────────────────────────────────────────────────────
# 1. Quan ly thiet bi
# ─────────────────────────────────────────────────────────────

def _show_devices(devices: list) -> None:
    t = Table(title="Danh Sach Thiet Bi", box=box.SIMPLE_HEAD, header_style="bold cyan")
    t.add_column("ID",          style="dim", width=10)
    t.add_column("Ten thiet bi", min_width=20)
    t.add_column("Cong suat",   justify="right")
    t.add_column("Uu tien",     justify="center")
    t.add_column("Max gio/ngay", justify="right")
    t.add_column("Loai",        style="dim")
    for d in devices:
        t.add_row(
            d.id, d.name, f"{d.power_w}W",
            PRIORITY_LABEL.get(d.priority, str(d.priority)),
            f"{d.max_daily_hours}h", d.category,
        )
    console.print(t)


def menu_devices() -> None:
    while True:
        clear(); header()
        devices = storage.load_devices()
        _show_devices(devices)
        console.print("\n[1] Them  [2] Xoa  [3] Khoi phuc mac dinh  [0] Quay lai")
        ch = Prompt.ask("Chon", choices=["0", "1", "2", "3"])
        if ch == "0":
            break
        elif ch == "1":
            _add_device(devices)
        elif ch == "2":
            _del_device(devices)
        elif ch == "3":
            if Confirm.ask("Khoi phuc danh sach thiet bi mac dinh?"):
                storage.save_devices(list(DEFAULT_DEVICES))
                console.print("[green]Da khoi phuc![/green]")
                pause()


def _add_device(devices: list) -> None:
    console.print("\n[bold]Them thiet bi moi:[/bold]")
    dev_id = Prompt.ask("  ID (viet lien, khong dau, vi du: iron)")
    if any(d.id == dev_id for d in devices):
        console.print("[red]  ID da ton tai![/red]"); pause(); return
    name     = Prompt.ask("  Ten thiet bi")
    power    = IntPrompt.ask("  Cong suat (Watt)")
    priority = IntPrompt.ask("  Muc uu tien 1-5", default=3)
    max_h    = FloatPrompt.ask("  Gio toi da / ngay", default=8.0)
    category = Prompt.ask("  Loai", default="other")
    devices.append(Device(dev_id, name, power, max(1, min(5, priority)), max_h, category))
    storage.save_devices(devices)
    console.print("[green]  Da them![/green]"); pause()


def _del_device(devices: list) -> None:
    dev_id = Prompt.ask("Nhap ID thiet bi can xoa")
    idx = next((i for i, d in enumerate(devices) if d.id == dev_id), None)
    if idx is None:
        console.print("[red]Khong tim thay ID nay.[/red]")
    else:
        console.print(f"[yellow]Da xoa: {devices.pop(idx).name}[/yellow]")
        storage.save_devices(devices)
    pause()


# ─────────────────────────────────────────────────────────────
# 2. Nhat ky su dung
# ─────────────────────────────────────────────────────────────

def menu_usage() -> None:
    clear(); header()
    devices = storage.load_devices()
    usage   = storage.load_usage()
    config  = storage.load_config()
    today   = date.today().isoformat()

    console.print(f"[bold]Ghi nhat ky su dung - [cyan]{today}[/cyan][/bold]\n")

    today_log = [e for e in usage if e.date == today]
    if today_log:
        dev_map = {d.id: d for d in devices}
        t = Table(box=box.SIMPLE, header_style="bold", title="Da ghi hom nay")
        t.add_column("Thiet bi")
        t.add_column("Gio",          justify="right")
        t.add_column("kWh",          justify="right")
        t.add_column("Chi phi (VND)", justify="right")
        total_kwh = 0.0
        for e in today_log:
            dev = dev_map.get(e.device_id)
            name = dev.name if dev else e.device_id
            kwh  = dev.kwh(e.hours) if dev else 0.0
            total_kwh += kwh
            t.add_row(name, f"{e.hours}h", f"{kwh:.3f}",
                      f"{kwh * config.electricity_rate:,.0f}")
        t.add_section()
        t.add_row("[bold]Tong[/bold]", "",
                  f"[bold]{total_kwh:.3f}[/bold]",
                  f"[bold]{total_kwh * config.electricity_rate:,.0f}[/bold]")
        console.print(t)
        if total_kwh <= config.daily_budget_kwh:
            console.print("  Trang thai: [green]Trong ngan sach[/green]\n")
        else:
            over = total_kwh - config.daily_budget_kwh
            console.print(f"  Trang thai: [red]Vuot {over:.2f} kWh![/red]\n")

    console.print("[dim]Nhap so gio da dung (de trong = bo qua):[/dim]")
    changed = False
    for dev in devices:
        h_str = Prompt.ask(
            f"  {dev.name} [dim]({dev.power_w}W, toi da {dev.max_daily_hours}h)[/dim]",
            default="",
        ).strip()
        if not h_str:
            continue
        try:
            hours = float(h_str)
            if hours < 0 or hours > dev.max_daily_hours:
                console.print(f"[red]    Gio khong hop le (0 - {dev.max_daily_hours}h)[/red]")
                continue
            usage = [e for e in usage if not (e.date == today and e.device_id == dev.id)]
            if hours > 0:
                usage.append(UsageEntry(dev.id, today, hours))
            changed = True
        except ValueError:
            console.print("[red]    Bo qua (khong phai so)[/red]")

    if changed:
        storage.save_usage(usage)
        console.print("\n[green]Da luu nhat ky![/green]")
    pause()


# ─────────────────────────────────────────────────────────────
# 3. Thong ke
# ─────────────────────────────────────────────────────────────

def menu_stats() -> None:
    clear(); header()
    devices = storage.load_devices()
    usage   = storage.load_usage()
    config  = storage.load_config()
    dev_map = {d.id: d for d in devices}

    if not usage:
        console.print("[yellow]Chua co du lieu. Hay ghi nhat ky su dung truoc.[/yellow]")
        pause(); return

    console.print("[bold cyan]Thong ke theo ngay (14 ngay gan nhat):[/bold cyan]")
    t = Table(box=box.SIMPLE_HEAD, header_style="bold")
    t.add_column("Ngay")
    t.add_column("kWh",          justify="right")
    t.add_column("Chi phi (VND)", justify="right")
    t.add_column("Trang thai",   justify="center")

    dates = sorted(set(e.date for e in usage))[-14:]
    for d in dates:
        kwh = sum(
            dev_map[e.device_id].kwh(e.hours)
            for e in usage if e.date == d and e.device_id in dev_map
        )
        ok = kwh <= config.daily_budget_kwh
        t.add_row(
            d, f"{kwh:.2f}", f"{kwh * config.electricity_rate:,.0f}",
            "[green]Tot[/green]" if ok else "[red]Vuot![/red]",
        )
    console.print(t)

    console.print("\n[bold cyan]Tong dien theo thiet bi:[/bold cyan]")
    t2 = Table(box=box.SIMPLE, header_style="bold")
    t2.add_column("Thiet bi")
    t2.add_column("Tong gio",    justify="right")
    t2.add_column("Tong kWh",    justify="right")
    t2.add_column("Chi phi (VND)", justify="right")

    for dev in sorted(devices, key=lambda d: -sum(
            e.hours for e in usage if e.device_id == d.id)):
        total_h = sum(e.hours for e in usage if e.device_id == dev.id)
        if total_h == 0:
            continue
        kwh  = dev.kwh(total_h)
        cost = kwh * config.electricity_rate
        t2.add_row(dev.name, f"{total_h:.1f}h", f"{kwh:.2f}", f"{cost:,.0f}")
    console.print(t2)

    if dates:
        n_days  = len(dates)
        avg_kwh = sum(
            dev_map[e.device_id].kwh(e.hours)
            for e in usage if e.device_id in dev_map
        ) / n_days
        est = avg_kwh * 30 * config.electricity_rate
        console.print(
            f"\n  Trung binh/ngay: [bold]{avg_kwh:.2f}[/bold] kWh  "
            f"->  Uoc tinh/thang: [bold cyan]{est:,.0f}[/bold cyan] VND"
        )
    pause()


# ─────────────────────────────────────────────────────────────
# 4. Toi uu lich su dung - DP vs Greedy
# ─────────────────────────────────────────────────────────────

def menu_optimize() -> None:
    clear(); header()
    devices = storage.load_devices()
    config  = storage.load_config()

    console.print(Panel(
        "[bold]Toi Uu Lich Su Dung Dien[/bold]\n\n"
        "So sanh hai thuat toan:\n"
        "  [cyan](1) DP Group Knapsack[/cyan]  --  Toi uu toan cuc,  O(n x W x H)\n"
        "  [yellow](2) Greedy (pri/watt)[/yellow]   --  Xap xi nhanh,   O(n log n)",
        border_style="blue", padding=(0, 2),
    ))

    budget = FloatPrompt.ask(
        "\nNgan sach dien / ngay (kWh)",
        default=config.daily_budget_kwh,
    )
    console.print()

    dp_res = algorithms.dp_optimize(devices, budget)
    gr_res = algorithms.greedy_optimize(devices, budget)

    _print_opt_result(dp_res, config.electricity_rate, style="cyan")
    _print_opt_result(gr_res, config.electricity_rate, style="yellow")

    diff     = dp_res.total_comfort - gr_res.total_comfort
    diff_pct = diff / max(gr_res.total_comfort, 1e-9) * 100
    dp_vnd   = dp_res.total_cost(config.electricity_rate)
    gr_vnd   = gr_res.total_cost(config.electricity_rate)

    body = (
        f"  [cyan]DP[/cyan]     comfort: [bold]{dp_res.total_comfort:.1f}[/bold]"
        f"  dien: {dp_res.total_kwh:.2f} kWh"
        f"  chi phi: {dp_vnd:,.0f} VND\n"
        f"  [yellow]Greedy[/yellow] comfort: [bold]{gr_res.total_comfort:.1f}[/bold]"
        f"  dien: {gr_res.total_kwh:.2f} kWh"
        f"  chi phi: {gr_vnd:,.0f} VND\n\n"
    )
    if diff > 1e-3:
        body += f"  [green]DP tot hon Greedy +{diff:.1f} diem ({diff_pct:.1f}%)[/green]"
    elif diff < -1e-3:
        body += f"  [yellow]Greedy tot hon DP +{-diff:.1f} diem (hiem gap)[/yellow]"
    else:
        body += "  [dim]Hai thuat toan cho ket qua bang nhau trong truong hop nay.[/dim]"

    console.print(Panel(
        body,
        title="[bold]Ket qua so sanh[/bold]",
        border_style="green", padding=(0, 2),
    ))

    if Confirm.ask("\nXem phan vi du DP tot hon Greedy?", default=False):
        _show_counterexample()
    pause()


def _show_counterexample() -> None:
    demo = algorithms.counterexample_demo()
    dp_r = demo["dp"]
    gr_r = demo["greedy"]

    console.print(Panel(
        f"[bold]Phan vi du: Greedy that bai trong 0/1 Knapsack[/bold]\n\n"
        f"Budget: {demo['budget']} kWh\n\n"
        f"  Loa Bluetooth: 200W, uu tien=3, max=1h  "
        f"→ ratio=3/200=0.0150  [yellow](Greedy chon TRUOC)[/yellow]\n"
        f"  Dieu hoa nho : 300W, uu tien=4, max=1h  "
        f"→ ratio=4/300=0.0133  [dim](Greedy chon sau)[/dim]\n\n"
        f"  [yellow]Greedy[/yellow]: chon Loa (0.20 kWh, +3 diem) "
        f"→ con lai 0.10 kWh → Dieu hoa (can 0.30) khong du → bo qua\n"
        f"           Tong: [bold yellow]{gr_r.total_comfort:.0f} diem[/bold yellow]\n\n"
        f"  [cyan]DP[/cyan]    : bo qua Loa, chon Dieu hoa (0.30 kWh, +4 diem)\n"
        f"           Tong: [bold cyan]{dp_r.total_comfort:.0f} diem[/bold cyan]\n\n"
        f"  [green]=> DP tot hon Greedy "
        f"+{dp_r.total_comfort - gr_r.total_comfort:.0f} diem![/green]\n\n"
        f"  Nguyen nhan: Greedy bi 'tham lam' chon item co ti le cao truoc,\n"
        f"  lam can budget khien khong con cho item gia tri thuc su cao hon.",
        title="[bold red]Counter-example[/bold red]",
        border_style="red", padding=(0, 2),
    ))


def _print_opt_result(res: algorithms.OptResult, rate: float, style: str) -> None:
    t = Table(
        title=f"[{style}]{res.algorithm}[/{style}]",
        box=box.ROUNDED,
        header_style=f"bold {style}",
    )
    t.add_column("Thiet bi", min_width=20)
    t.add_column("Gio",     justify="right")
    t.add_column("kWh",     justify="right")
    t.add_column("Comfort", justify="right")

    for item in res.schedule:
        t.add_row(item.device.name, f"{item.hours}h",
                  f"{item.kwh:.3f}", f"{item.comfort:.1f}")

    t.add_section()
    t.add_row("[bold]Tong[/bold]", "",
              f"[bold]{res.total_kwh:.3f}[/bold]",
              f"[bold]{res.total_comfort:.1f}[/bold]")
    console.print(t)
    console.print(
        f"  Chi phi: [bold]{res.total_cost(rate):,.0f}[/bold] VND/ngay  "
        f"[dim]({res.total_cost(rate) * 30:,.0f} VND/thang)[/dim]\n"
        f"  [dim]Do phuc tap: {res.complexity}[/dim]\n"
    )


# ─────────────────────────────────────────────────────────────
# 5. Lich tranh gio cao diem
# ─────────────────────────────────────────────────────────────

def menu_peak() -> None:
    clear(); header()
    devices = storage.load_devices()
    config  = storage.load_config()

    console.print("[bold]Phan Bo Gio Dung Dien - Tranh Gio Cao Diem[/bold]")
    console.print(
        f"Gio cao diem: [red]{' '.join(str(h) + 'h' for h in config.peak_hours)}[/red]\n"
    )

    budget = FloatPrompt.ask("Ngan sach / ngay (kWh)", default=config.daily_budget_kwh)
    dp_res = algorithms.dp_optimize(devices, budget)
    sched  = algorithms.peak_aware_schedule(dp_res.schedule, config.peak_hours)

    console.print("\n[bold cyan]Timeline 24 gio (moi o = 1 gio):[/bold cyan]\n")
    hour_labels = "".join(f"{h:02d}" for h in range(24))
    console.print(f"  {'Thiet bi':<20} {hour_labels}")
    console.print(f"  {'':<20} {'--' * 24}")

    for item in dp_res.schedule:
        dev   = item.device
        slots = sched.get(dev.id, [])
        bar   = _timeline(slots, config.peak_hours)
        console.print(
            f"  {dev.name:<20} {bar}  "
            f"[dim]{item.hours}h - {item.kwh:.2f} kWh[/dim]"
        )

    console.print(
        "\n  Chu thich: [green]##[/green] dung dien  "
        "[red]!![/red] gio cao diem (tranh)  [dim]..[/dim] khong dung\n"
    )
    pause()


def _timeline(slots: list, peak: list) -> str:
    """Tao thanh timeline 24 gio, moi gio 2 ky tu."""
    peak_set = set(peak)
    row = ["  "] * 24
    for h in peak_set:
        if 0 <= h < 24:
            row[h] = "!!"
    for (start_h, dur) in slots:
        for h in range(start_h, min(start_h + int(dur + 0.5), 24)):
            row[h] = "##"

    out = ""
    for h, c in enumerate(row):
        if c == "##":
            out += f"[green]##[/green]"
        elif c == "!!":
            out += f"[red]!![/red]"
        else:
            out += f"[dim]..[/dim]"
    return out


# ─────────────────────────────────────────────────────────────
# 6. Cai dat
# ─────────────────────────────────────────────────────────────

def menu_settings() -> None:
    clear(); header()
    config = storage.load_config()

    console.print("[bold]Cai Dat Hien Tai:[/bold]\n")
    console.print(f"  Ngan sach / ngay : [cyan]{config.daily_budget_kwh}[/cyan] kWh")
    console.print(f"  Gia dien          : [cyan]{config.electricity_rate:,.0f}[/cyan] VND/kWh")
    console.print(
        f"  Gio cao diem     : [red]{', '.join(str(h) + 'h' for h in config.peak_hours)}[/red]\n"
    )

    if not Confirm.ask("Cap nhat cai dat?"):
        return

    config.daily_budget_kwh = FloatPrompt.ask(
        "Ngan sach / ngay (kWh)", default=config.daily_budget_kwh
    )
    config.electricity_rate = FloatPrompt.ask(
        "Gia dien (VND/kWh)", default=config.electricity_rate
    )
    peak_str = Prompt.ask(
        "Gio cao diem (cach nhau bang dau phay, vi du: 17,18,19,20,21)",
        default=",".join(str(h) for h in config.peak_hours),
    )
    try:
        config.peak_hours = [int(x.strip()) for x in peak_str.split(",")]
    except ValueError:
        console.print("[red]Dinh dang khong hop le, giu nguyen gio cao diem cu.[/red]")

    storage.save_config(config)
    console.print("[green]Da luu cai dat![/green]")
    pause()


# ─────────────────────────────────────────────────────────────
# Main loop
# ─────────────────────────────────────────────────────────────

def main() -> None:
    dispatch = {
        "1": menu_devices,
        "2": menu_usage,
        "3": menu_stats,
        "4": menu_optimize,
        "5": menu_peak,
        "6": menu_settings,
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
