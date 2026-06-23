#!/usr/bin/env python3
"""
Tro Ly Tiet Kiem Dien - Phong Tro Sinh Vien
Mon: Thuat Toan | DP Group Knapsack vs Greedy
"""

import os  # Thư viện thao tác hệ thống tệp và đường dẫn
import sys  # Thư viện tương tác với môi trường hệ thống Python

# Force UTF-8 cho Windows terminal (cmd / PowerShell)
if sys.platform == "win32":  # Kiểm tra nếu đang chạy trên Windows
    os.system("chcp 65001 >nul 2>&1")  # Chuyển code page terminal sang UTF-8 (code page 65001)
    if hasattr(sys.stdout, "reconfigure"):  # Kiểm tra Python >= 3.7 hỗ trợ reconfigure
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # Cấu hình stdout xuất UTF-8
    if hasattr(sys.stderr, "reconfigure"):  # Kiểm tra Python >= 3.7 cho stderr
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")  # Cấu hình stderr xuất UTF-8

from datetime import date  # Lớp xử lý ngày tháng để lấy ngày hôm nay

from rich import box  # Import kiểu khung bảng từ thư viện rich
from rich.console import Console  # Lớp console của rich hỗ trợ màu sắc và định dạng
from rich.panel import Panel  # Widget panel có viền đẹp để hiển thị nội dung nổi bật
from rich.prompt import Confirm, FloatPrompt, IntPrompt, Prompt  # Các loại input có giao diện rich
from rich.table import Table  # Widget bảng của rich để hiển thị dữ liệu dạng lưới

import algorithms  # Module thuật toán DP và Greedy (algorithms.py)
import storage  # Module đọc/ghi JSON (storage.py)
from models import DEFAULT_DEVICES, Device, UsageEntry  # Import lớp dữ liệu từ models.py

console = Console(highlight=False)  # Tạo đối tượng Console của rich, tắt highlight tự động

PRIORITY_LABEL = {  # Dict ánh xạ mức ưu tiên số → nhãn có màu rich
    5: "[green]5/5[/green]",  # Ưu tiên 5: màu xanh lá (không thể thiếu)
    4: "[cyan]4/5[/cyan]",  # Ưu tiên 4: màu cyan (quan trọng)
    3: "[yellow]3/5[/yellow]",  # Ưu tiên 3: màu vàng (bình thường)
    2: "[white]2/5[/white]",  # Ưu tiên 2: màu trắng (thấp)
    1: "[dim]1/5[/dim]",  # Ưu tiên 1: màu mờ (không cần thiết)
}


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────

def clear() -> None:  # Hàm xóa màn hình terminal
    console.clear()  # Gọi phương thức clear của rich Console


def pause() -> None:  # Hàm dừng và chờ người dùng nhấn Enter
    console.print("\n[dim]Nhan Enter de tiep tuc...[/dim]")  # Hiển thị thông báo chờ
    input()  # Chờ người dùng nhấn phím Enter


def header() -> None:  # Hàm hiển thị tiêu đề ứng dụng dạng panel
    console.print(Panel.fit(  # Panel tự co theo nội dung (fit = không có padding thừa)
        "[bold cyan]TRO LY TIET KIEM DIEN[/bold cyan]\n"  # Tiêu đề chính màu cyan đậm
        "[dim]Phong tro sinh vien  |  DP Group Knapsack + Greedy[/dim]",  # Phụ đề mô tả ứng dụng
        border_style="cyan",  # Viền màu cyan
        padding=(0, 4),  # Padding ngang 4 ký tự, không có padding dọc
    ))


# ─────────────────────────────────────────────────────────────
# Menu chinh
# ─────────────────────────────────────────────────────────────

def main_menu() -> str:  # Hàm hiển thị menu chính và nhận lựa chọn
    rows = [  # Danh sách các mục menu với số thứ tự và mô tả
        ("1", "Quan ly thiet bi dien"),  # Mục 1: Quản lý danh sách thiết bị
        ("2", "Ghi nhat ky su dung hom nay"),  # Mục 2: Ghi nhật ký dùng điện hôm nay
        ("3", "Thong ke dien nang"),  # Mục 3: Xem thống kê tiêu thụ điện
        ("4", "Toi uu lich su dung  [bold](DP vs Greedy)[/bold]"),  # Mục 4: So sánh DP và Greedy
        ("5", "Lich dung tranh gio cao diem"),  # Mục 5: Lịch phân bổ tránh giờ cao điểm
        ("6", "Cai dat"),  # Mục 6: Cài đặt ngân sách và giá điện
        ("0", "Thoat"),  # Mục 0: Thoát ứng dụng
    ]
    t = Table(box=box.ROUNDED, border_style="cyan", show_header=False, padding=(0, 1))  # Bảng menu viền tròn cyan
    t.add_column(width=4, style="bold yellow", no_wrap=True)  # Cột số thứ tự, màu vàng đậm
    t.add_column()  # Cột mô tả menu
    for k, v in rows:  # Thêm từng mục menu vào bảng
        t.add_row(f"[{k}]", v)  # Định dạng số trong ngoặc vuông
    console.print(t)  # Hiển thị bảng menu
    return Prompt.ask("[bold]Chon[/bold]", choices=["0", "1", "2", "3", "4", "5", "6"])  # Hỏi và xác nhận lựa chọn 0-6


# ─────────────────────────────────────────────────────────────
# 1. Quan ly thiet bi
# ─────────────────────────────────────────────────────────────

def _show_devices(devices: list) -> None:  # Hàm hiển thị bảng danh sách thiết bị
    t = Table(title="Danh Sach Thiet Bi", box=box.SIMPLE_HEAD, header_style="bold cyan")  # Bảng với tiêu đề cyan
    t.add_column("ID",          style="dim", width=10)  # Cột ID, màu mờ, rộng 10 ký tự
    t.add_column("Ten thiet bi", min_width=20)  # Cột tên, tối thiểu 20 ký tự
    t.add_column("Cong suat",   justify="right")  # Cột công suất, căn phải
    t.add_column("Uu tien",     justify="center")  # Cột ưu tiên, căn giữa
    t.add_column("Max gio/ngay", justify="right")  # Cột giờ tối đa, căn phải
    t.add_column("Loai",        style="dim")  # Cột loại thiết bị, màu mờ
    for d in devices:  # Thêm từng thiết bị vào bảng
        t.add_row(
            d.id, d.name, f"{d.power_w}W",  # ID, tên, công suất
            PRIORITY_LABEL.get(d.priority, str(d.priority)),  # Nhãn ưu tiên có màu
            f"{d.max_daily_hours}h", d.category,  # Giờ tối đa và loại
        )
    console.print(t)  # Hiển thị bảng danh sách thiết bị


def menu_devices() -> None:  # Hàm xử lý menu quản lý thiết bị điện
    while True:  # Vòng lặp cho đến khi người dùng chọn quay lại
        clear(); header()  # Xóa màn hình và hiển thị tiêu đề
        devices = storage.load_devices()  # Tải danh sách thiết bị từ file JSON
        _show_devices(devices)  # Hiển thị bảng danh sách thiết bị
        console.print("\n[1] Them  [2] Xoa  [3] Khoi phuc mac dinh  [0] Quay lai")  # Hiển thị các lựa chọn
        ch = Prompt.ask("Chon", choices=["0", "1", "2", "3"])  # Hỏi lựa chọn từ người dùng
        if ch == "0":  # Quay lại menu chính
            break  # Thoát vòng lặp
        elif ch == "1":  # Thêm thiết bị mới
            _add_device(devices)  # Gọi hàm thêm thiết bị
        elif ch == "2":  # Xóa thiết bị
            _del_device(devices)  # Gọi hàm xóa thiết bị
        elif ch == "3":  # Khôi phục danh sách mặc định
            if Confirm.ask("Khoi phuc danh sach thiet bi mac dinh?"):  # Xác nhận trước khi khôi phục
                storage.save_devices(list(DEFAULT_DEVICES))  # Ghi lại danh sách mặc định
                console.print("[green]Da khoi phuc![/green]")  # Xác nhận thành công
                pause()  # Chờ người dùng đọc xong


def _add_device(devices: list) -> None:  # Hàm thêm một thiết bị mới vào danh sách
    console.print("\n[bold]Them thiet bi moi:[/bold]")  # Tiêu đề màn hình thêm thiết bị
    dev_id = Prompt.ask("  ID (viet lien, khong dau, vi du: iron)")  # Hỏi ID thiết bị mới
    if any(d.id == dev_id for d in devices):  # Kiểm tra ID có trùng không
        console.print("[red]  ID da ton tai![/red]"); pause(); return  # Báo lỗi và thoát hàm
    name     = Prompt.ask("  Ten thiet bi")  # Hỏi tên hiển thị thiết bị
    power    = IntPrompt.ask("  Cong suat (Watt)")  # Hỏi công suất tính bằng Watt
    priority = IntPrompt.ask("  Muc uu tien 1-5", default=3)  # Hỏi mức ưu tiên 1-5, mặc định 3
    max_h    = FloatPrompt.ask("  Gio toi da / ngay", default=8.0)  # Hỏi giờ tối đa mỗi ngày, mặc định 8h
    category = Prompt.ask("  Loai", default="other")  # Hỏi nhóm thiết bị, mặc định "other"
    devices.append(Device(dev_id, name, power, max(1, min(5, priority)), max_h, category))  # Tạo Device mới, ưu tiên ép về 1-5
    storage.save_devices(devices)  # Lưu danh sách đã có thêm thiết bị mới
    console.print("[green]  Da them![/green]"); pause()  # Xác nhận thêm thành công


def _del_device(devices: list) -> None:  # Hàm xóa một thiết bị khỏi danh sách
    dev_id = Prompt.ask("Nhap ID thiet bi can xoa")  # Hỏi ID thiết bị cần xóa
    idx = next((i for i, d in enumerate(devices) if d.id == dev_id), None)  # Tìm vị trí thiết bị trong danh sách
    if idx is None:  # Không tìm thấy thiết bị với ID đó
        console.print("[red]Khong tim thay ID nay.[/red]")  # Báo lỗi không tìm thấy
    else:  # Tìm thấy thiết bị
        console.print(f"[yellow]Da xoa: {devices.pop(idx).name}[/yellow]")  # Xóa thiết bị và thông báo tên đã xóa
        storage.save_devices(devices)  # Lưu danh sách sau khi đã xóa
    pause()  # Chờ người dùng xác nhận đọc xong


# ─────────────────────────────────────────────────────────────
# 2. Nhat ky su dung
# ─────────────────────────────────────────────────────────────

def menu_usage() -> None:  # Hàm xử lý ghi nhật ký sử dụng điện hôm nay
    clear(); header()  # Xóa màn hình và hiển thị tiêu đề
    devices = storage.load_devices()  # Tải danh sách thiết bị từ JSON
    usage   = storage.load_usage()  # Tải nhật ký sử dụng hiện có
    config  = storage.load_config()  # Tải cấu hình (ngân sách, giá điện)
    today   = date.today().isoformat()  # Lấy ngày hôm nay theo định dạng YYYY-MM-DD

    console.print(f"[bold]Ghi nhat ky su dung - [cyan]{today}[/cyan][/bold]\n")  # Hiển thị tiêu đề và ngày hôm nay

    today_log = [e for e in usage if e.date == today]  # Lọc các bản ghi nhật ký của hôm nay
    if today_log:  # Nếu đã có dữ liệu hôm nay thì hiển thị tóm tắt
        dev_map = {d.id: d for d in devices}  # Dict tra cứu nhanh thiết bị theo ID
        t = Table(box=box.SIMPLE, header_style="bold", title="Da ghi hom nay")  # Bảng tóm tắt hôm nay
        t.add_column("Thiet bi")  # Cột tên thiết bị
        t.add_column("Gio",          justify="right")  # Cột số giờ, căn phải
        t.add_column("kWh",          justify="right")  # Cột điện tiêu thụ, căn phải
        t.add_column("Chi phi (VND)", justify="right")  # Cột chi phí, căn phải
        total_kwh = 0.0  # Biến tích lũy tổng điện tiêu thụ hôm nay
        for e in today_log:  # Duyệt qua từng bản ghi hôm nay
            dev = dev_map.get(e.device_id)  # Tra cứu thông tin thiết bị từ dict
            name = dev.name if dev else e.device_id  # Dùng tên thiết bị hoặc ID nếu không tìm thấy
            kwh  = dev.kwh(e.hours) if dev else 0.0  # Tính điện tiêu thụ (0 nếu không tìm thấy)
            total_kwh += kwh  # Cộng vào tổng
            t.add_row(name, f"{e.hours}h", f"{kwh:.3f}",  # Thêm hàng dữ liệu vào bảng
                      f"{kwh * config.electricity_rate:,.0f}")  # Chi phí điện bằng VND
        t.add_section()  # Đường kẻ ngang phân cách trước hàng tổng
        t.add_row("[bold]Tong[/bold]", "",  # Hàng tổng cộng
                  f"[bold]{total_kwh:.3f}[/bold]",
                  f"[bold]{total_kwh * config.electricity_rate:,.0f}[/bold]")
        console.print(t)  # Hiển thị bảng tóm tắt
        if total_kwh <= config.daily_budget_kwh:  # So sánh tổng điện với ngân sách ngày
            console.print("  Trang thai: [green]Trong ngan sach[/green]\n")  # Xanh: trong ngân sách
        else:  # Vượt ngân sách
            over = total_kwh - config.daily_budget_kwh  # Tính mức vượt ngân sách
            console.print(f"  Trang thai: [red]Vuot {over:.2f} kWh![/red]\n")  # Đỏ: báo vượt bao nhiêu kWh

    console.print("[dim]Nhap so gio da dung (de trong = bo qua):[/dim]")  # Hướng dẫn nhập liệu
    changed = False  # Cờ theo dõi có thay đổi dữ liệu không
    for dev in devices:  # Duyệt qua từng thiết bị để nhập giờ sử dụng hôm nay
        h_str = Prompt.ask(  # Hỏi số giờ đã dùng thiết bị này hôm nay
            f"  {dev.name} [dim]({dev.power_w}W, toi da {dev.max_daily_hours}h)[/dim]",
            default="",  # Mặc định để trống (bỏ qua thiết bị này)
        ).strip()  # Loại bỏ khoảng trắng đầu cuối
        if not h_str:  # Người dùng để trống
            continue  # Bỏ qua, sang thiết bị tiếp theo
        try:  # Thử chuyển chuỗi nhập thành số float
            hours = float(h_str)  # Chuyển chuỗi sang số thực
            if hours < 0 or hours > dev.max_daily_hours:  # Kiểm tra giờ hợp lệ
                console.print(f"[red]    Gio khong hop le (0 - {dev.max_daily_hours}h)[/red]")  # Báo giờ không hợp lệ
                continue  # Bỏ qua, sang thiết bị tiếp theo
            usage = [e for e in usage if not (e.date == today and e.device_id == dev.id)]  # Xóa bản ghi cũ hôm nay của thiết bị này
            if hours > 0:  # Chỉ thêm bản ghi nếu giờ > 0
                usage.append(UsageEntry(dev.id, today, hours))  # Thêm bản ghi mới vào nhật ký
            changed = True  # Đánh dấu có thay đổi dữ liệu
        except ValueError:  # Người dùng nhập không phải số
            console.print("[red]    Bo qua (khong phai so)[/red]")  # Báo lỗi định dạng

    if changed:  # Nếu có thay đổi dữ liệu nhật ký
        storage.save_usage(usage)  # Lưu nhật ký đã cập nhật ra file JSON
        console.print("\n[green]Da luu nhat ky![/green]")  # Xác nhận lưu thành công
    pause()  # Chờ người dùng nhấn Enter


# ─────────────────────────────────────────────────────────────
# 3. Thong ke
# ─────────────────────────────────────────────────────────────

def menu_stats() -> None:  # Hàm hiển thị thống kê tiêu thụ điện
    clear(); header()  # Xóa màn hình và hiển thị tiêu đề
    devices = storage.load_devices()  # Tải danh sách thiết bị
    usage   = storage.load_usage()  # Tải toàn bộ nhật ký sử dụng
    config  = storage.load_config()  # Tải cấu hình ngân sách và giá điện
    dev_map = {d.id: d for d in devices}  # Dict tra cứu thiết bị theo ID

    if not usage:  # Nếu chưa có nhật ký nào
        console.print("[yellow]Chua co du lieu. Hay ghi nhat ky su dung truoc.[/yellow]")  # Thông báo chưa có dữ liệu
        pause(); return  # Dừng và quay về menu chính

    console.print("[bold cyan]Thong ke theo ngay (14 ngay gan nhat):[/bold cyan]")  # Tiêu đề thống kê theo ngày
    t = Table(box=box.SIMPLE_HEAD, header_style="bold")  # Bảng thống kê theo ngày
    t.add_column("Ngay")  # Cột ngày tháng
    t.add_column("kWh",          justify="right")  # Cột điện tiêu thụ, căn phải
    t.add_column("Chi phi (VND)", justify="right")  # Cột chi phí VND, căn phải
    t.add_column("Trang thai",   justify="center")  # Cột trạng thái (trong/vượt ngân sách)

    dates = sorted(set(e.date for e in usage))[-14:]  # Lấy 14 ngày gần nhất từ nhật ký
    for d in dates:  # Duyệt từng ngày
        kwh = sum(  # Tính tổng điện trong ngày d
            dev_map[e.device_id].kwh(e.hours)
            for e in usage if e.date == d and e.device_id in dev_map  # Chỉ tính thiết bị còn trong danh sách
        )
        ok = kwh <= config.daily_budget_kwh  # True nếu trong ngân sách
        t.add_row(
            d, f"{kwh:.2f}", f"{kwh * config.electricity_rate:,.0f}",  # Ngày, kWh, chi phí
            "[green]Tot[/green]" if ok else "[red]Vuot![/red]",  # Trạng thái có màu
        )
    console.print(t)  # Hiển thị bảng thống kê theo ngày

    console.print("\n[bold cyan]Tong dien theo thiet bi:[/bold cyan]")  # Tiêu đề thống kê theo thiết bị
    t2 = Table(box=box.SIMPLE, header_style="bold")  # Bảng tổng điện theo từng thiết bị
    t2.add_column("Thiet bi")  # Cột tên thiết bị
    t2.add_column("Tong gio",    justify="right")  # Cột tổng giờ sử dụng, căn phải
    t2.add_column("Tong kWh",    justify="right")  # Cột tổng điện tiêu thụ, căn phải
    t2.add_column("Chi phi (VND)", justify="right")  # Cột tổng chi phí, căn phải

    for dev in sorted(devices, key=lambda d: -sum(  # Sắp xếp thiết bị theo tổng giờ giảm dần
            e.hours for e in usage if e.device_id == d.id)):
        total_h = sum(e.hours for e in usage if e.device_id == dev.id)  # Tổng giờ dùng thiết bị này
        if total_h == 0:  # Bỏ qua thiết bị chưa từng được sử dụng
            continue
        kwh  = dev.kwh(total_h)  # Tổng điện tiêu thụ của thiết bị
        cost = kwh * config.electricity_rate  # Tổng chi phí tính bằng VND
        t2.add_row(dev.name, f"{total_h:.1f}h", f"{kwh:.2f}", f"{cost:,.0f}")  # Thêm hàng dữ liệu
    console.print(t2)  # Hiển thị bảng tổng theo thiết bị

    if dates:  # Nếu có dữ liệu ngày để tính trung bình
        n_days  = len(dates)  # Số ngày có dữ liệu
        avg_kwh = sum(  # Tính tổng điện tất cả ngày
            dev_map[e.device_id].kwh(e.hours)
            for e in usage if e.device_id in dev_map
        ) / n_days  # Chia cho số ngày để lấy trung bình
        est = avg_kwh * 30 * config.electricity_rate  # Ước tính chi phí tháng (30 ngày)
        console.print(
            f"\n  Trung binh/ngay: [bold]{avg_kwh:.2f}[/bold] kWh  "  # Hiển thị trung bình ngày
            f"->  Uoc tinh/thang: [bold cyan]{est:,.0f}[/bold cyan] VND"  # Ước tính chi phí tháng
        )
    pause()  # Chờ người dùng nhấn Enter


# ─────────────────────────────────────────────────────────────
# 4. Toi uu lich su dung - DP vs Greedy
# ─────────────────────────────────────────────────────────────

def menu_optimize() -> None:  # Hàm xử lý so sánh tối ưu hóa DP vs Greedy
    clear(); header()  # Xóa màn hình và hiển thị tiêu đề
    devices = storage.load_devices()  # Tải danh sách thiết bị
    config  = storage.load_config()  # Tải cấu hình

    console.print(Panel(  # Panel giới thiệu hai thuật toán
        "[bold]Toi Uu Lich Su Dung Dien[/bold]\n\n"  # Tiêu đề panel
        "So sanh hai thuat toan:\n"  # Mô tả nội dung so sánh
        "  [cyan](1) DP Group Knapsack[/cyan]  --  Toi uu toan cuc,  O(n x W x H)\n"  # DP: chính xác nhưng chậm hơn
        "  [yellow](2) Greedy (pri/watt)[/yellow]   --  Xap xi nhanh,   O(n log n)",  # Greedy: nhanh nhưng có thể không tối ưu
        border_style="blue", padding=(0, 2),  # Viền xanh dương
    ))

    budget = FloatPrompt.ask(  # Hỏi ngân sách điện ngày
        "\nNgan sach dien / ngay (kWh)",
        default=config.daily_budget_kwh,  # Hiển thị giá trị hiện tại làm mặc định
    )
    console.print()  # Dòng trống để tạo khoảng cách

    dp_res = algorithms.dp_optimize(devices, budget)  # Chạy thuật toán DP Group Knapsack
    gr_res = algorithms.greedy_optimize(devices, budget)  # Chạy thuật toán Greedy

    _print_opt_result(dp_res, config.electricity_rate, style="cyan")  # In kết quả DP màu cyan
    _print_opt_result(gr_res, config.electricity_rate, style="yellow")  # In kết quả Greedy màu vàng

    diff     = dp_res.total_comfort - gr_res.total_comfort  # Hiệu điểm thoải mái DP - Greedy
    diff_pct = diff / max(gr_res.total_comfort, 1e-9) * 100  # Phần trăm chênh lệch
    dp_vnd   = dp_res.total_cost(config.electricity_rate)  # Chi phí DP bằng VND
    gr_vnd   = gr_res.total_cost(config.electricity_rate)  # Chi phí Greedy bằng VND

    body = (  # Xây dựng nội dung panel so sánh
        f"  [cyan]DP[/cyan]     comfort: [bold]{dp_res.total_comfort:.1f}[/bold]"
        f"  dien: {dp_res.total_kwh:.2f} kWh"
        f"  chi phi: {dp_vnd:,.0f} VND\n"
        f"  [yellow]Greedy[/yellow] comfort: [bold]{gr_res.total_comfort:.1f}[/bold]"
        f"  dien: {gr_res.total_kwh:.2f} kWh"
        f"  chi phi: {gr_vnd:,.0f} VND\n\n"
    )
    if diff > 1e-3:  # DP tốt hơn Greedy đáng kể
        body += f"  [green]DP tot hon Greedy +{diff:.1f} diem ({diff_pct:.1f}%)[/green]"
    elif diff < -1e-3:  # Greedy tốt hơn DP (hiếm)
        body += f"  [yellow]Greedy tot hon DP +{-diff:.1f} diem (hiem gap)[/yellow]"
    else:  # Hai thuật toán cho kết quả tương đương
        body += "  [dim]Hai thuat toan cho ket qua bang nhau trong truong hop nay.[/dim]"

    console.print(Panel(  # Hiển thị panel kết quả so sánh
        body,
        title="[bold]Ket qua so sanh[/bold]",
        border_style="green", padding=(0, 2),
    ))

    if Confirm.ask("\nXem phan vi du DP tot hon Greedy?", default=False):  # Hỏi có muốn xem phản ví dụ không
        _show_counterexample()  # Hiển thị phản ví dụ Loa Bluetooth vs Điều hòa nhỏ
    pause()  # Chờ người dùng nhấn Enter


def _show_counterexample() -> None:  # Hàm hiển thị phản ví dụ DP thắng Greedy
    demo = algorithms.counterexample_demo()  # Chạy hàm tạo phản ví dụ
    dp_r = demo["dp"]  # Kết quả thuật toán DP trong phản ví dụ
    gr_r = demo["greedy"]  # Kết quả thuật toán Greedy trong phản ví dụ

    console.print(Panel(  # Hiển thị panel phân tích phản ví dụ
        f"[bold]Phan vi du: Greedy that bai trong 0/1 Knapsack[/bold]\n\n"
        f"Budget: {demo['budget']} kWh\n\n"  # Ngân sách của phản ví dụ: 0.30 kWh
        f"  Loa Bluetooth: 200W, uu tien=3, max=1h  "
        f"-> ratio=3/200=0.0150  [yellow](Greedy chon TRUOC)[/yellow]\n"  # Greedy ưu tiên Loa vì ratio cao hơn
        f"  Dieu hoa nho : 300W, uu tien=4, max=1h  "
        f"-> ratio=4/300=0.0133  [dim](Greedy chon sau)[/dim]\n\n"  # Greedy xếp Điều hòa sau Loa
        f"  [yellow]Greedy[/yellow]: chon Loa (0.20 kWh, +3 diem) "
        f"-> con lai 0.10 kWh -> Dieu hoa (can 0.30) khong du -> bo qua\n"  # Greedy tham lam chọn Loa, không còn đủ cho Điều hòa
        f"           Tong: [bold yellow]{gr_r.total_comfort:.0f} diem[/bold yellow]\n\n"  # Kết quả Greedy: 3 điểm
        f"  [cyan]DP[/cyan]    : bo qua Loa, chon Dieu hoa (0.30 kWh, +4 diem)\n"  # DP bỏ qua Loa, chọn Điều hòa
        f"           Tong: [bold cyan]{dp_r.total_comfort:.0f} diem[/bold cyan]\n\n"  # Kết quả DP: 4 điểm
        f"  [green]=> DP tot hon Greedy "
        f"+{dp_r.total_comfort - gr_r.total_comfort:.0f} diem![/green]\n\n"  # Kết luận DP thắng
        f"  Nguyen nhan: Greedy bi 'tham lam' chon item co ti le cao truoc,\n"  # Giải thích: Greedy tham lam
        f"  lam can budget khien khong con cho item gia tri thuc su cao hon.",  # Hậu quả: không còn ngân sách cho item tốt hơn
        title="[bold red]Counter-example[/bold red]",  # Tiêu đề panel màu đỏ
        border_style="red", padding=(0, 2),  # Viền đỏ
    ))


def _print_opt_result(res: algorithms.OptResult, rate: float, style: str) -> None:  # Hàm in kết quả tối ưu dạng bảng
    t = Table(  # Tạo bảng kết quả
        title=f"[{style}]{res.algorithm}[/{style}]",  # Tiêu đề bảng là tên thuật toán có màu
        box=box.ROUNDED,  # Kiểu viền tròn
        header_style=f"bold {style}",  # Tiêu đề cột có màu theo style
    )
    t.add_column("Thiet bi", min_width=20)  # Cột tên thiết bị
    t.add_column("Gio",     justify="right")  # Cột số giờ, căn phải
    t.add_column("kWh",     justify="right")  # Cột điện tiêu thụ, căn phải
    t.add_column("Comfort", justify="right")  # Cột điểm thoải mái, căn phải

    for item in res.schedule:  # Thêm từng thiết bị trong lịch vào bảng
        t.add_row(item.device.name, f"{item.hours}h",  # Tên và số giờ
                  f"{item.kwh:.3f}", f"{item.comfort:.1f}")  # Điện và điểm thoải mái

    t.add_section()  # Đường kẻ ngang phân cách trước hàng tổng
    t.add_row("[bold]Tong[/bold]", "",  # Hàng tổng cộng
              f"[bold]{res.total_kwh:.3f}[/bold]",
              f"[bold]{res.total_comfort:.1f}[/bold]")
    console.print(t)  # Hiển thị bảng kết quả
    console.print(
        f"  Chi phi: [bold]{res.total_cost(rate):,.0f}[/bold] VND/ngay  "  # Chi phí điện ngày
        f"[dim]({res.total_cost(rate) * 30:,.0f} VND/thang)[/dim]\n"  # Ước tính chi phí tháng
        f"  [dim]Do phuc tap: {res.complexity}[/dim]\n"  # Thông tin độ phức tạp thuật toán
    )


# ─────────────────────────────────────────────────────────────
# 5. Lich tranh gio cao diem
# ─────────────────────────────────────────────────────────────

def menu_peak() -> None:  # Hàm hiển thị lịch phân bổ giờ tránh cao điểm
    clear(); header()  # Xóa màn hình và hiển thị tiêu đề
    devices = storage.load_devices()  # Tải danh sách thiết bị
    config  = storage.load_config()  # Tải cấu hình (bao gồm danh sách giờ cao điểm)

    console.print("[bold]Phan Bo Gio Dung Dien - Tranh Gio Cao Diem[/bold]")  # Tiêu đề màn hình
    console.print(  # Hiển thị danh sách giờ cao điểm màu đỏ
        f"Gio cao diem: [red]{' '.join(str(h) + 'h' for h in config.peak_hours)}[/red]\n"
    )

    budget = FloatPrompt.ask("Ngan sach / ngay (kWh)", default=config.daily_budget_kwh)  # Hỏi ngân sách điện
    dp_res = algorithms.dp_optimize(devices, budget)  # Chạy DP để lấy lịch tối ưu
    sched  = algorithms.peak_aware_schedule(dp_res.schedule, config.peak_hours)  # Phân bổ giờ tránh cao điểm

    console.print("\n[bold cyan]Timeline 24 gio (moi o = 1 gio):[/bold cyan]\n")  # Tiêu đề timeline 24 giờ
    hour_labels = "".join(f"{h:02d}" for h in range(24))  # Tạo nhãn giờ "000102...23"
    console.print(f"  {'Thiet bi':<20} {hour_labels}")  # Hàng tiêu đề cột giờ
    console.print(f"  {'':<20} {'--' * 24}")  # Đường kẻ phân cách tiêu đề và dữ liệu

    for item in dp_res.schedule:  # Duyệt qua từng thiết bị trong lịch tối ưu
        dev   = item.device  # Lấy thông tin thiết bị
        slots = sched.get(dev.id, [])  # Lấy danh sách khung giờ phân bổ cho thiết bị này
        bar   = _timeline(slots, config.peak_hours)  # Tạo chuỗi timeline màu sắc
        console.print(  # In hàng timeline cho thiết bị này
            f"  {dev.name:<20} {bar}  "
            f"[dim]{item.hours}h - {item.kwh:.2f} kWh[/dim]"  # Thông tin tổng giờ và điện
        )

    console.print(  # In chú thích màu sắc bên dưới timeline
        "\n  Chu thich: [green]##[/green] dung dien  "
        "[red]!![/red] gio cao diem (tranh)  [dim]..[/dim] khong dung\n"
    )
    pause()  # Chờ người dùng nhấn Enter


def _timeline(slots: list, peak: list) -> str:  # Hàm tạo chuỗi timeline 24 giờ có màu
    """Tao thanh timeline 24 gio, moi gio 2 ky tu."""
    peak_set = set(peak)  # Chuyển danh sách giờ cao điểm thành set để tra cứu O(1)
    row = ["  "] * 24  # Khởi tạo 24 ô trống (2 ký tự mỗi ô)
    for h in peak_set:  # Đánh dấu các giờ cao điểm bằng "!!"
        if 0 <= h < 24:  # Kiểm tra giờ hợp lệ trong khoảng 0-23
            row[h] = "!!"  # Ký hiệu giờ cao điểm
    for (start_h, dur) in slots:  # Đánh dấu các giờ dùng điện bằng "##"
        for h in range(start_h, min(start_h + int(dur + 0.5), 24)):  # Mỗi slot kéo dài dur giờ
            row[h] = "##"  # Ký hiệu giờ đang dùng điện

    out = ""  # Chuỗi kết quả
    for h, c in enumerate(row):  # Duyệt qua từng ô trong timeline
        if c == "##":  # Giờ đang dùng điện
            out += f"[green]##[/green]"  # Màu xanh lá
        elif c == "!!":  # Giờ cao điểm không được dùng
            out += f"[red]!![/red]"  # Màu đỏ
        else:  # Giờ không dùng điện
            out += f"[dim]..[/dim]"  # Màu mờ
    return out  # Trả về chuỗi timeline có màu sắc


# ─────────────────────────────────────────────────────────────
# 6. Cai dat
# ─────────────────────────────────────────────────────────────

def menu_settings() -> None:  # Hàm xử lý màn hình cài đặt ứng dụng
    clear(); header()  # Xóa màn hình và hiển thị tiêu đề
    config = storage.load_config()  # Tải cấu hình hiện tại

    console.print("[bold]Cai Dat Hien Tai:[/bold]\n")  # Tiêu đề phần hiển thị cài đặt
    console.print(f"  Ngan sach / ngay : [cyan]{config.daily_budget_kwh}[/cyan] kWh")  # Hiển thị ngân sách hiện tại
    console.print(f"  Gia dien          : [cyan]{config.electricity_rate:,.0f}[/cyan] VND/kWh")  # Hiển thị giá điện hiện tại
    console.print(  # Hiển thị giờ cao điểm hiện tại màu đỏ
        f"  Gio cao diem     : [red]{', '.join(str(h) + 'h' for h in config.peak_hours)}[/red]\n"
    )

    if not Confirm.ask("Cap nhat cai dat?"):  # Hỏi có muốn thay đổi cài đặt không
        return  # Người dùng không muốn thay đổi, quay về menu chính

    config.daily_budget_kwh = FloatPrompt.ask(  # Nhập ngân sách điện mới
        "Ngan sach / ngay (kWh)", default=config.daily_budget_kwh
    )
    config.electricity_rate = FloatPrompt.ask(  # Nhập giá điện mới
        "Gia dien (VND/kWh)", default=config.electricity_rate
    )
    peak_str = Prompt.ask(  # Nhập danh sách giờ cao điểm mới
        "Gio cao diem (cach nhau bang dau phay, vi du: 17,18,19,20,21)",
        default=",".join(str(h) for h in config.peak_hours),  # Hiển thị giá trị hiện tại làm mặc định
    )
    try:  # Thử phân tích chuỗi giờ cao điểm nhập vào
        config.peak_hours = [int(x.strip()) for x in peak_str.split(",")]  # Tách bằng dấu phẩy và chuyển sang int
    except ValueError:  # Nếu định dạng không hợp lệ (không phải số)
        console.print("[red]Dinh dang khong hop le, giu nguyen gio cao diem cu.[/red]")  # Báo lỗi, giữ nguyên

    storage.save_config(config)  # Lưu cấu hình đã cập nhật ra file JSON
    console.print("[green]Da luu cai dat![/green]")  # Xác nhận lưu thành công
    pause()  # Chờ người dùng nhấn Enter


# ─────────────────────────────────────────────────────────────
# Main loop
# ─────────────────────────────────────────────────────────────

def main() -> None:  # Hàm chính điều phối toàn bộ ứng dụng CLI
    dispatch = {  # Dict ánh xạ lựa chọn menu → hàm xử lý tương ứng
        "1": menu_devices,  # Mục 1 → quản lý thiết bị
        "2": menu_usage,  # Mục 2 → ghi nhật ký sử dụng
        "3": menu_stats,  # Mục 3 → xem thống kê
        "4": menu_optimize,  # Mục 4 → tối ưu hóa DP vs Greedy
        "5": menu_peak,  # Mục 5 → lịch tránh giờ cao điểm
        "6": menu_settings,  # Mục 6 → cài đặt ứng dụng
    }
    while True:  # Vòng lặp chính: chạy mãi cho đến khi người dùng chọn thoát
        clear(); header()  # Xóa màn hình và hiển thị tiêu đề ứng dụng
        ch = main_menu()  # Hiển thị menu chính và nhận lựa chọn từ người dùng
        if ch == "0":  # Người dùng chọn thoát
            console.print("\n[cyan]Tam biet! Tiet kiem dien nhe![/cyan]\n")  # Lời tạm biệt thân thiện
            break  # Thoát vòng lặp, kết thúc chương trình
        dispatch[ch]()  # Gọi hàm xử lý tương ứng với lựa chọn của người dùng


if __name__ == "__main__":  # Chỉ chạy khi gọi trực tiếp file này (không phải khi import)
    main()  # Khởi động vòng lặp chính của ứng dụng CLI
