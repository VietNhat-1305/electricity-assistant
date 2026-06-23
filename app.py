#!/usr/bin/env python3
"""
Tro Ly Tiet Kiem Dien - Phong Tro Sinh Vien
Mon: Thuat Toan | DP Group Knapsack vs Greedy
Chay: pip install rich  ->  python app.py
"""

import json  # Thư viện đọc/ghi dữ liệu định dạng JSON
import math  # Thư viện toán học, dùng cho math.floor làm tròn xuống
import os  # Thư viện thao tác hệ thống tệp và đường dẫn
import sys  # Thư viện tương tác với môi trường hệ thống Python
from dataclasses import dataclass, field  # Decorator và hàm tạo lớp dữ liệu tự động
from datetime import date  # Lớp xử lý ngày tháng, dùng để lấy ngày hôm nay
from typing import List, Tuple  # Import kiểu dữ liệu danh sách và bộ giá trị

# Thiết lập encoding UTF-8 cho terminal Windows để hiển thị tiếng Việt đúng cách
if sys.platform == "win32":  # Kiểm tra nếu đang chạy trên hệ điều hành Windows
    os.system("chcp 65001 >nul 2>&1")  # Chuyển code page terminal sang UTF-8 (code page 65001)
    if hasattr(sys.stdout, "reconfigure"):  # Kiểm tra Python >= 3.7 hỗ trợ reconfigure
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # Cấu hình stdout xuất UTF-8
    if hasattr(sys.stderr, "reconfigure"):  # Kiểm tra Python >= 3.7 cho stderr
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")  # Cấu hình stderr xuất UTF-8

from rich import box  # Import kiểu khung bảng từ thư viện rich
from rich.console import Console  # Lớp console của rich hỗ trợ màu sắc và định dạng
from rich.panel import Panel  # Widget panel có viền để hiển thị nội dung nổi bật
from rich.prompt import Confirm, FloatPrompt, IntPrompt, Prompt  # Các loại input có giao diện đẹp
from rich.table import Table  # Widget bảng của rich để hiển thị dữ liệu dạng lưới

# ══════════════════════════════════════════════════════════════
# MODELS
# ══════════════════════════════════════════════════════════════

@dataclass  # Tự động sinh __init__, __repr__, __eq__ cho lớp Device
class Device:  # Lớp đại diện một thiết bị điện trong phòng trọ
    id: str  # Mã định danh duy nhất của thiết bị (vd: "ac", "fan", "light")
    name: str  # Tên hiển thị tiếng Việt (vd: "Dieu hoa", "Quat dien")
    power_w: int            # Cong suat (Watt)  # Công suất tiêu thụ tính bằng Watt
    priority: int           # Muc uu tien 1-5 (5 = khong the thieu)  # Mức ưu tiên 1-5
    max_daily_hours: float  # Gio toi da su dung / ngay  # Số giờ tối đa dùng mỗi ngày
    category: str  # Nhóm thiết bị: cooling / lighting / computing / heating / cooking / cleaning / entertainment

    def kwh(self, hours: float) -> float:  # Hàm tính điện năng tiêu thụ
        return self.power_w * hours / 1000  # Công thức: Watt x giờ / 1000 = kWh


@dataclass  # Tự động sinh __init__ cho lớp UsageEntry
class UsageEntry:  # Lớp ghi nhận một lần sử dụng thiết bị trong ngày
    device_id: str  # ID thiết bị được sử dụng (khóa ngoại)
    date: str   # YYYY-MM-DD  # Ngày sử dụng theo định dạng ISO 8601
    hours: float  # Số giờ đã dùng thiết bị trong ngày đó
    note: str = ""  # Ghi chú tùy chọn, mặc định để trống


@dataclass  # Tự động sinh __init__ cho lớp Config
class Config:  # Lớp lưu cấu hình toàn cục của ứng dụng
    daily_budget_kwh: float = 2.0  # Ngân sách điện mặc định mỗi ngày (kWh)
    electricity_rate: float = 3500.0   # VND/kWh  # Giá điện mặc định tính bằng VND/kWh
    peak_hours: List[int] = field(default_factory=lambda: [17, 18, 19, 20, 21])  # Giờ cao điểm mặc định 17h-21h


DEFAULT_DEVICES: List[Device] = [  # Danh sách 10 thiết bị phổ biến phòng trọ sinh viên
    Device("ac",      "Dieu hoa",         900,  4,  8.0, "cooling"),     # Điều hòa 900W, ưu tiên 4, tối đa 8h/ngày
    Device("fan",     "Quat dien",          55,  5, 12.0, "cooling"),     # Quạt điện 55W, ưu tiên 5, tối đa 12h/ngày
    Device("light",   "Den LED",            15,  5, 12.0, "lighting"),    # Đèn LED 15W, ưu tiên 5, tối đa 12h/ngày
    Device("laptop",  "Laptop",             65,  5, 10.0, "computing"),   # Laptop 65W, ưu tiên 5, tối đa 10h/ngày
    Device("phone",   "Sac dien thoai",     10,  4,  4.0, "computing"),  # Sạc điện thoại 10W, ưu tiên 4, 4h/ngày
    Device("heater",  "Binh nuoc nong",   2000,  3,  1.0, "heating"),    # Bình nóng lạnh 2000W, ưu tiên 3, 1h/ngày
    Device("tv",      "Tivi",              100,  2,  4.0, "entertainment"), # Tivi 100W, ưu tiên 2, tối đa 4h/ngày
    Device("rice",    "Noi com dien",      700,  5,  1.0, "cooking"),    # Nồi cơm điện 700W, ưu tiên 5, 1h/ngày
    Device("fridge",  "Tu lanh mini",       80,  3, 24.0, "cooling"),    # Tủ lạnh mini 80W, ưu tiên 3, hoạt động 24h
    Device("washing", "May giat",          500,  4,  1.0, "cleaning"),   # Máy giặt 500W, ưu tiên 4, 1h/ngày
]

# ══════════════════════════════════════════════════════════════
# STORAGE
# ══════════════════════════════════════════════════════════════

_DIR     = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")  # Thư mục data/ cùng cấp file app.py
_DEVICES = os.path.join(_DIR, "devices.json")  # Đường dẫn file lưu danh sách thiết bị
_USAGE   = os.path.join(_DIR, "usage.json")  # Đường dẫn file lưu nhật ký sử dụng
_CONFIG  = os.path.join(_DIR, "config.json")  # Đường dẫn file lưu cấu hình


def _ensure() -> None:  # Hàm nội bộ đảm bảo thư mục data tồn tại
    os.makedirs(_DIR, exist_ok=True)  # Tạo thư mục data/ nếu chưa có, không lỗi nếu đã tồn tại


def load_devices() -> List[Device]:  # Đọc danh sách thiết bị từ JSON
    _ensure()  # Đảm bảo thư mục data tồn tại
    if not os.path.exists(_DEVICES):  # Nếu file devices.json chưa có
        save_devices(list(DEFAULT_DEVICES))  # Tạo file với danh sách mặc định
        return list(DEFAULT_DEVICES)  # Trả về bản sao danh sách mặc định
    with open(_DEVICES, encoding="utf-8") as f:  # Mở file JSON để đọc
        return [Device(**d) for d in json.load(f)]  # Chuyển từng dict JSON thành đối tượng Device


def save_devices(devices: List[Device]) -> None:  # Ghi danh sách thiết bị ra JSON
    _ensure()  # Đảm bảo thư mục data tồn tại
    with open(_DEVICES, "w", encoding="utf-8") as f:  # Mở file để ghi
        json.dump([d.__dict__ for d in devices], f, ensure_ascii=False, indent=2)  # Ghi JSON có định dạng, giữ tiếng Việt


def load_usage() -> List[UsageEntry]:  # Đọc nhật ký sử dụng từ JSON
    _ensure()  # Đảm bảo thư mục data tồn tại
    if not os.path.exists(_USAGE):  # Nếu file usage.json chưa có
        return []  # Trả về danh sách rỗng
    with open(_USAGE, encoding="utf-8") as f:  # Mở file JSON nhật ký
        return [UsageEntry(**e) for e in json.load(f)]  # Chuyển dict thành UsageEntry


def save_usage(entries: List[UsageEntry]) -> None:  # Ghi nhật ký sử dụng ra JSON
    _ensure()  # Đảm bảo thư mục data tồn tại
    with open(_USAGE, "w", encoding="utf-8") as f:  # Mở file để ghi
        json.dump([e.__dict__ for e in entries], f, ensure_ascii=False, indent=2)  # Ghi JSON nhật ký


def load_config() -> Config:  # Đọc cấu hình từ JSON
    _ensure()  # Đảm bảo thư mục data tồn tại
    if not os.path.exists(_CONFIG):  # Nếu file config.json chưa có
        return Config()  # Trả về cấu hình mặc định
    with open(_CONFIG, encoding="utf-8") as f:  # Mở file cấu hình
        return Config(**json.load(f))  # Tạo Config từ dữ liệu JSON đã lưu


def save_config(cfg: Config) -> None:  # Ghi cấu hình ra JSON
    _ensure()  # Đảm bảo thư mục data tồn tại
    with open(_CONFIG, "w", encoding="utf-8") as f:  # Mở file để ghi
        json.dump(cfg.__dict__, f, ensure_ascii=False, indent=2)  # Ghi toàn bộ thuộc tính Config


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

BUDGET_UNIT = 0.01  # kWh / don vi ngan sach trong bang DP  # Độ mịn ngân sách: 0.01 kWh mỗi đơn vị
HOUR_STEP   = 0.5   # buoc gio (0.5h = 30 phut)  # Bước thời gian: mỗi lựa chọn tăng 30 phút


@dataclass  # Tự động sinh __init__ cho ScheduleItem
class ScheduleItem:  # Lớp đại diện một mục trong lịch sử dụng điện tối ưu
    device: Device  # Thiết bị được lên lịch sử dụng
    hours: float  # Số giờ dùng thiết bị trong ngày

    @property  # Thuộc tính tính toán (tính khi truy cập, không lưu)
    def kwh(self) -> float:  # Điện năng tiêu thụ của mục này (kWh)
        return self.device.kwh(self.hours)  # Ủy quyền tính cho phương thức kwh của Device

    @property  # Thuộc tính tính toán điểm thoải mái
    def comfort(self) -> float:  # Điểm thoải mái = ưu tiên x số giờ
        return self.device.priority * self.hours  # Tích của mức ưu tiên và thời gian sử dụng


@dataclass  # Tự động sinh __init__ cho OptResult
class OptResult:  # Lớp chứa kết quả đầy đủ của một lần tối ưu hóa
    schedule: List[ScheduleItem]  # Danh sách thiết bị và giờ trong lịch tối ưu
    total_comfort: float  # Tổng điểm thoải mái đạt được
    total_kwh: float  # Tổng điện năng tiêu thụ (kWh)
    algorithm: str  # Tên thuật toán đã dùng để hiển thị
    complexity: str  # Chuỗi mô tả độ phức tạp thuật toán

    def total_cost(self, rate: float) -> float:  # Tính tổng chi phí điện bằng VND
        return self.total_kwh * rate  # Nhân tổng kWh với giá điện VND/kWh


def _options(dev: Device) -> List[Tuple[int, float, float]]:
    """Sinh cac lua chon (cost_units, comfort_value, hours) cho thiet bi."""
    result = []  # Danh sách các lựa chọn giờ cho thiết bị này
    h = HOUR_STEP  # Bắt đầu từ 0.5h (không xét 0h vì không dùng)
    while h <= dev.max_daily_hours + 1e-9:  # Lặp đến giới hạn giờ tối đa (epsilon tránh lỗi float)
        # int(x + 0.5) thay round() de tranh banker's rounding cua Python 3
        cost_u = max(1, int(dev.kwh(h) / BUDGET_UNIT + 0.5))  # Số đơn vị ngân sách cần, ít nhất 1
        result.append((cost_u, dev.priority * h, h))  # Thêm bộ (chi phí, giá trị, giờ) vào danh sách
        h += HOUR_STEP  # Tăng lên mức giờ tiếp theo
    return result  # Trả về tất cả lựa chọn có thể của thiết bị


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
    n = len(devices)  # Số lượng thiết bị
    W = int(budget_kwh / BUDGET_UNIT) + 1  # Tổng số đơn vị ngân sách (số cột bảng DP)

    dp     = [[0.0] * W for _ in range(n + 1)]  # Bảng DP: (n+1) hàng x W cột, khởi tạo 0
    choice = [[0.0] * W for _ in range(n)]  # Bảng truy vết: n hàng x W cột lưu số giờ đã chọn

    for i, dev in enumerate(devices):  # Duyệt qua từng thiết bị (mỗi vòng điền hàng i+1)
        opts = _options(dev)  # Lấy tất cả lựa chọn giờ của thiết bị i
        for j in range(W):  # Duyệt qua từng mức ngân sách j
            dp[i + 1][j] = dp[i][j]   # mac dinh: khong dung thiet bi i  # Không chọn thiết bị i
            choice[i][j] = 0.0  # Mặc định: giờ = 0 (không dùng thiết bị i)
            for cost_u, val, h in opts:  # Thử từng mức giờ h cho thiết bị i
                if j >= cost_u:  # Chỉ xét nếu còn đủ ngân sách để dùng h giờ
                    candidate = dp[i][j - cost_u] + val  # Điểm nếu chọn thiết bị i với h giờ
                    if candidate > dp[i + 1][j]:  # Nếu tốt hơn kết quả đang có
                        dp[i + 1][j] = candidate  # Cập nhật giá trị tối ưu
                        choice[i][j] = h  # Ghi nhận giờ h dẫn đến kết quả tối ưu

    best_j = max(range(W), key=lambda j: dp[n][j])  # Tìm cột j cho điểm thoải mái cao nhất

    # Truy vet lich su dung tu bang choice
    schedule: List[ScheduleItem] = []  # Danh sách thiết bị được chọn (kết quả truy vết)
    j = best_j  # Bắt đầu truy vết từ ngân sách tối ưu
    for i in range(n - 1, -1, -1):  # Đi ngược từ thiết bị thứ n-1 về 0
        h = choice[i][j]  # Lấy số giờ đã chọn tại ô (i, j)
        if h > 0:  # Nếu thiết bị i được chọn dùng
            cost_u = max(1, int(devices[i].kwh(h) / BUDGET_UNIT + 0.5))  # Tính chi phí đơn vị
            schedule.append(ScheduleItem(devices[i], h))  # Thêm vào danh sách kết quả
            j -= cost_u  # Khôi phục ngân sách trước khi chọn thiết bị i

    n_opts = max((len(_options(d)) for d in devices), default=1)  # Số lựa chọn tối đa của một thiết bị
    return OptResult(  # Trả về kết quả DP đầy đủ
        schedule=sorted(schedule, key=lambda x: -x.comfort),  # Sắp xếp theo điểm thoải mái giảm dần
        total_comfort=dp[n][best_j],  # Điểm thoải mái tối ưu từ bảng DP
        total_kwh=sum(s.kwh for s in schedule),  # Tổng điện tiêu thụ
        algorithm="DP - Group Knapsack",  # Nhãn thuật toán
        complexity=(  # Chuỗi mô tả độ phức tạp với số liệu cụ thể
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
    schedule: List[ScheduleItem] = []  # Danh sách thiết bị được chọn
    remaining = budget_kwh  # Ngân sách còn lại để cấp phát

    for dev in sorted(devices, key=lambda d: d.priority / d.power_w, reverse=True):  # Sắp xếp giảm theo tỷ lệ ưu tiên/công suất
        if remaining < 1e-9:  # Ngân sách cạn thì dừng (epsilon tránh lỗi float)
            break
        hours = min(dev.max_daily_hours, remaining / (dev.power_w / 1000))  # Số giờ tối đa có thể dùng với ngân sách còn lại
        hours = math.floor(hours / HOUR_STEP) * HOUR_STEP  # lam tron XUONG, khong vuot budget
        if hours >= HOUR_STEP:  # Chỉ chọn thiết bị nếu dùng được ít nhất 0.5 giờ
            schedule.append(ScheduleItem(dev, hours))  # Thêm vào lịch
            remaining -= dev.kwh(hours)  # Trừ điện năng khỏi ngân sách còn lại

    return OptResult(  # Trả về kết quả Greedy
        schedule=sorted(schedule, key=lambda x: -x.comfort),  # Sắp xếp theo điểm thoải mái giảm dần
        total_comfort=sum(s.comfort for s in schedule),  # Tổng điểm thoải mái
        total_kwh=sum(s.kwh for s in schedule),  # Tổng điện tiêu thụ
        algorithm="Greedy - Ti le Uu tien / Cong suat",  # Nhãn thuật toán
        complexity="Time O(n log n) | Space O(n)",  # Độ phức tạp Greedy
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
    loa  = Device("loa_demo", "Loa Bluetooth (demo)", 200, 3, 1.0, "entertainment")  # Thiết bị A: Loa 200W ưu tiên 3
    dh   = Device("dh_demo",  "Dieu hoa nho (demo)",  300, 4, 1.0, "cooling")  # Thiết bị B: Điều hòa 300W ưu tiên 4
    devs = [loa, dh]  # Chỉ 2 thiết bị để tạo tình huống xung đột
    dp_r = dp_optimize(devs, 0.30)  # Chạy DP với ngân sách 0.30 kWh
    gr_r = greedy_optimize(devs, 0.30)  # Chạy Greedy với cùng ngân sách
    return {"dp": dp_r, "greedy": gr_r, "dp_wins": dp_r.total_comfort > gr_r.total_comfort + 1e-6}  # Trả về kết quả cả hai


def peak_aware_schedule(schedule: List[ScheduleItem], peak_hours: List[int]) -> dict:
    """
    Phan bo gio su dung thiet bi tranh gio cao diem.
    Thiet bi cong suat cao (>=500W) -> day sang gio thap diem truoc.
    """
    peak_set = set(peak_hours)  # Chuyển danh sách giờ cao điểm thành set để tra cứu O(1)
    off_peak = [h for h in range(24) if h not in peak_set]  # Danh sách các giờ thấp điểm
    peak_asc = sorted(peak_hours)  # Sắp xếp giờ cao điểm tăng dần
    result   = {}  # Dict kết quả: {device_id: [(giờ, thời lượng), ...]}
    for item in schedule:  # Duyệt qua từng thiết bị trong lịch tối ưu
        slots = []  # Danh sách khung giờ phân bổ cho thiết bị này
        left  = item.hours  # Số giờ còn cần phân bổ
        pool  = off_peak if item.device.power_w >= 500 else (off_peak + peak_asc)  # Thiết bị tốn điện ưu tiên giờ thấp điểm
        for h in pool:  # Duyệt qua danh sách giờ ưu tiên
            if left < 1e-9:  # Đã đủ giờ thì dừng
                break
            used = min(1.0, left)  # Tối đa 1 giờ mỗi khung giờ
            slots.append((h, used))  # Ghi nhận phân bổ giờ h với thời lượng used
            left -= used  # Giảm số giờ còn lại
        result[item.device.id] = slots  # Lưu kết quả phân bổ cho thiết bị
    return result  # Trả về toàn bộ lịch phân bổ theo giờ


# ══════════════════════════════════════════════════════════════
# UI
# ══════════════════════════════════════════════════════════════

console = Console(highlight=False)  # Tạo đối tượng Console của rich, tắt highlight tự động

PRIORITY_LABEL = {  # Dict ánh xạ mức ưu tiên số → nhãn màu sắc rich
    5: "[green]5/5[/green]", 4: "[cyan]4/5[/cyan]",  # Ưu tiên 5 màu xanh lá, 4 màu cyan
    3: "[yellow]3/5[/yellow]", 2: "[white]2/5[/white]", 1: "[dim]1/5[/dim]",  # 3 vàng, 2 trắng, 1 mờ
}


def clear() -> None:  # Hàm xóa màn hình terminal
    console.clear()  # Gọi phương thức clear của rich Console


def pause() -> None:  # Hàm dừng và chờ người dùng nhấn Enter
    console.print("\n[dim]Nhan Enter de tiep tuc...[/dim]")  # Hiển thị thông báo chờ
    input()  # Chờ người dùng nhấn Enter


def header() -> None:  # Hàm hiển thị tiêu đề ứng dụng dạng panel
    console.print(Panel.fit(  # Panel tự co theo nội dung
        "[bold cyan]TRO LY TIET KIEM DIEN[/bold cyan]\n"  # Tiêu đề chính màu cyan đậm
        "[dim]Phong tro sinh vien  |  DP Group Knapsack + Greedy[/dim]",  # Phụ đề mô tả ứng dụng
        border_style="cyan", padding=(0, 4),  # Viền màu cyan, padding ngang 4 ký tự
    ))


def main_menu() -> str:  # Hàm hiển thị menu chính và nhận lựa chọn của người dùng
    rows = [  # Danh sách các mục menu với số thứ tự và mô tả
        ("1", "Quan ly thiet bi dien"),  # Mục 1: Quản lý thiết bị điện
        ("2", "Ghi nhat ky su dung hom nay"),  # Mục 2: Ghi nhật ký sử dụng
        ("3", "Thong ke dien nang"),  # Mục 3: Xem thống kê tiêu thụ điện
        ("4", "Toi uu lich su dung  [bold](DP vs Greedy)[/bold]"),  # Mục 4: Tối ưu hóa DP vs Greedy
        ("5", "Lich dung tranh gio cao diem"),  # Mục 5: Lịch tránh giờ cao điểm
        ("6", "Cai dat"),  # Mục 6: Cài đặt ứng dụng
        ("0", "Thoat"),  # Mục 0: Thoát ứng dụng
    ]
    t = Table(box=box.ROUNDED, border_style="cyan", show_header=False, padding=(0, 1))  # Bảng menu viền tròn không có tiêu đề
    t.add_column(width=4, style="bold yellow", no_wrap=True)  # Cột số thứ tự, màu vàng đậm
    t.add_column()  # Cột mô tả menu
    for k, v in rows:  # Thêm từng mục menu vào bảng
        t.add_row(f"[{k}]", v)  # Định dạng số trong ngoặc vuông
    console.print(t)  # Hiển thị bảng menu
    return Prompt.ask("[bold]Chon[/bold]", choices=["0","1","2","3","4","5","6"])  # Hỏi lựa chọn, chỉ chấp nhận 0-6


# ── 1. Quan ly thiet bi ───────────────────────────────────────

def menu_devices() -> None:  # Hàm xử lý menu quản lý thiết bị điện
    while True:  # Vòng lặp cho đến khi người dùng chọn quay lại
        clear(); header()  # Xóa màn hình và hiển thị tiêu đề
        devices = load_devices()  # Tải danh sách thiết bị từ file JSON
        t = Table(title="Danh Sach Thiet Bi", box=box.SIMPLE_HEAD, header_style="bold cyan")  # Bảng danh sách thiết bị
        t.add_column("ID", style="dim", width=10)  # Cột ID mờ, rộng 10 ký tự
        t.add_column("Ten thiet bi", min_width=20)  # Cột tên thiết bị, tối thiểu 20 ký tự
        t.add_column("Cong suat", justify="right")  # Cột công suất, căn phải
        t.add_column("Uu tien", justify="center")  # Cột ưu tiên, căn giữa
        t.add_column("Max gio/ngay", justify="right")  # Cột giờ tối đa, căn phải
        t.add_column("Loai", style="dim")  # Cột loại thiết bị, màu mờ
        for d in devices:  # Thêm từng thiết bị vào bảng
            t.add_row(d.id, d.name, f"{d.power_w}W",  # ID, tên, công suất
                      PRIORITY_LABEL.get(d.priority, str(d.priority)),  # Nhãn ưu tiên có màu
                      f"{d.max_daily_hours}h", d.category)  # Giờ tối đa và loại
        console.print(t)  # Hiển thị bảng danh sách thiết bị
        console.print("\n[1] Them  [2] Xoa  [3] Khoi phuc mac dinh  [0] Quay lai")  # Hiển thị các lựa chọn con
        ch = Prompt.ask("Chon", choices=["0","1","2","3"])  # Hỏi lựa chọn từ người dùng
        if ch == "0":  # Người dùng chọn quay lại menu chính
            break  # Thoát vòng lặp
        elif ch == "1":  # Người dùng chọn thêm thiết bị mới
            dev_id = Prompt.ask("  ID (viet lien, khong dau)")  # Hỏi ID thiết bị mới
            if any(d.id == dev_id for d in devices):  # Kiểm tra ID đã tồn tại chưa
                console.print("[red]  ID da ton tai![/red]"); pause(); continue  # Báo lỗi và tiếp tục vòng lặp
            name     = Prompt.ask("  Ten thiet bi")  # Hỏi tên thiết bị
            power    = IntPrompt.ask("  Cong suat (Watt)")  # Hỏi công suất (số nguyên)
            priority = IntPrompt.ask("  Muc uu tien 1-5", default=3)  # Hỏi mức ưu tiên, mặc định 3
            max_h    = FloatPrompt.ask("  Gio toi da / ngay", default=8.0)  # Hỏi giờ tối đa, mặc định 8h
            category = Prompt.ask("  Loai", default="other")  # Hỏi loại thiết bị
            devices.append(Device(dev_id, name, power, max(1, min(5, priority)), max_h, category))  # Tạo và thêm thiết bị
            save_devices(devices)  # Lưu danh sách đã cập nhật
            console.print("[green]  Da them![/green]"); pause()  # Xác nhận thành công
        elif ch == "2":  # Người dùng chọn xóa thiết bị
            dev_id = Prompt.ask("Nhap ID thiet bi can xoa")  # Hỏi ID thiết bị cần xóa
            idx = next((i for i, d in enumerate(devices) if d.id == dev_id), None)  # Tìm vị trí thiết bị
            if idx is None:  # Không tìm thấy
                console.print("[red]Khong tim thay.[/red]")  # Báo lỗi
            else:  # Tìm thấy
                console.print(f"[yellow]Da xoa: {devices.pop(idx).name}[/yellow]")  # Xóa và thông báo
                save_devices(devices)  # Lưu danh sách sau khi xóa
            pause()  # Chờ người dùng xác nhận
        elif ch == "3":  # Người dùng chọn khôi phục mặc định
            if Confirm.ask("Khoi phuc danh sach mac dinh?"):  # Hỏi xác nhận
                save_devices(list(DEFAULT_DEVICES))  # Ghi lại danh sách mặc định
                console.print("[green]Da khoi phuc![/green]"); pause()  # Xác nhận thành công


# ── 2. Nhat ky su dung ───────────────────────────────────────

def menu_usage() -> None:  # Hàm xử lý ghi nhật ký sử dụng điện hôm nay
    clear(); header()  # Xóa màn hình và hiển thị tiêu đề
    devices = load_devices()  # Tải danh sách thiết bị
    usage   = load_usage()  # Tải nhật ký sử dụng hiện có
    config  = load_config()  # Tải cấu hình (ngân sách, giá điện)
    today   = date.today().isoformat()  # Lấy ngày hôm nay theo định dạng YYYY-MM-DD

    console.print(f"[bold]Ghi nhat ky - [cyan]{today}[/cyan][/bold]\n")  # Hiển thị tiêu đề và ngày hôm nay

    today_log = [e for e in usage if e.date == today]  # Lọc bản ghi nhật ký của hôm nay
    if today_log:  # Nếu đã có dữ liệu hôm nay thì hiển thị tóm tắt
        dev_map = {d.id: d for d in devices}  # Dict tra cứu nhanh thiết bị theo ID
        t = Table(box=box.SIMPLE, header_style="bold", title="Da ghi hom nay")  # Bảng tóm tắt sử dụng hôm nay
        t.add_column("Thiet bi")  # Cột tên thiết bị
        t.add_column("Gio", justify="right")  # Cột số giờ, căn phải
        t.add_column("kWh", justify="right")  # Cột điện tiêu thụ, căn phải
        t.add_column("Chi phi (VND)", justify="right")  # Cột chi phí, căn phải
        total_kwh = 0.0  # Biến tích lũy tổng điện tiêu thụ hôm nay
        for e in today_log:  # Duyệt qua từng bản ghi hôm nay
            dev = dev_map.get(e.device_id)  # Tra cứu thông tin thiết bị
            kwh = dev.kwh(e.hours) if dev else 0.0  # Tính điện tiêu thụ (0 nếu không tìm thấy)
            total_kwh += kwh  # Cộng vào tổng điện hôm nay
            t.add_row(dev.name if dev else e.device_id, f"{e.hours}h",  # Thêm hàng vào bảng
                      f"{kwh:.3f}", f"{kwh * config.electricity_rate:,.0f}")  # Điện và chi phí
        t.add_section()  # Đường kẻ ngang phân cách trước hàng tổng
        t.add_row("[bold]Tong[/bold]", "",  # Hàng tổng cộng
                  f"[bold]{total_kwh:.3f}[/bold]",
                  f"[bold]{total_kwh * config.electricity_rate:,.0f}[/bold]")
        console.print(t)  # Hiển thị bảng tóm tắt hôm nay
        if total_kwh <= config.daily_budget_kwh:  # So sánh với ngân sách ngày
            console.print("  Trang thai: [green]Trong ngan sach[/green]\n")  # Trong ngân sách: màu xanh
        else:  # Vượt ngân sách
            console.print(f"  Trang thai: [red]Vuot {total_kwh - config.daily_budget_kwh:.2f} kWh![/red]\n")  # Báo vượt bao nhiêu kWh

    console.print("[dim]Nhap so gio da dung (de trong = bo qua):[/dim]")  # Hướng dẫn nhập liệu
    changed = False  # Cờ theo dõi có thay đổi dữ liệu không
    for dev in devices:  # Duyệt qua từng thiết bị để nhập giờ sử dụng
        h_str = Prompt.ask(  # Hỏi số giờ đã dùng thiết bị này hôm nay
            f"  {dev.name} [dim]({dev.power_w}W, toi da {dev.max_daily_hours}h)[/dim]",
            default="").strip()  # Mặc định để trống (bỏ qua thiết bị này)
        if not h_str:  # Nếu người dùng để trống
            continue  # Bỏ qua thiết bị này, sang thiết bị tiếp theo
        try:  # Thử chuyển đổi chuỗi sang số thực
            hours = float(h_str)  # Chuyển chuỗi nhập thành số float
            if not (0 <= hours <= dev.max_daily_hours):  # Kiểm tra giờ hợp lệ trong khoảng
                console.print(f"[red]    Gio khong hop le (0-{dev.max_daily_hours}h)[/red]"); continue  # Báo lỗi
            usage = [e for e in usage if not (e.date == today and e.device_id == dev.id)]  # Xóa bản ghi cũ hôm nay
            if hours > 0:  # Chỉ thêm bản ghi mới nếu giờ > 0
                usage.append(UsageEntry(dev.id, today, hours))  # Thêm bản ghi mới
            changed = True  # Đánh dấu có thay đổi
        except ValueError:  # Người dùng nhập không phải số
            console.print("[red]    Bo qua (khong phai so)[/red]")  # Báo lỗi định dạng

    if changed:  # Nếu có thay đổi dữ liệu
        save_usage(usage)  # Lưu nhật ký đã cập nhật
        console.print("\n[green]Da luu nhat ky![/green]")  # Xác nhận lưu thành công
    pause()  # Chờ người dùng nhấn Enter trước khi quay về menu


# ── 3. Thong ke ──────────────────────────────────────────────

def menu_stats() -> None:  # Hàm hiển thị thống kê tiêu thụ điện
    clear(); header()  # Xóa màn hình và hiển thị tiêu đề
    devices = load_devices()  # Tải danh sách thiết bị
    usage   = load_usage()  # Tải nhật ký sử dụng
    config  = load_config()  # Tải cấu hình
    dev_map = {d.id: d for d in devices}  # Dict tra cứu thiết bị theo ID

    if not usage:  # Nếu chưa có dữ liệu nhật ký
        console.print("[yellow]Chua co du lieu. Hay ghi nhat ky truoc.[/yellow]")  # Thông báo chưa có dữ liệu
        pause(); return  # Dừng và quay về menu chính

    console.print("[bold cyan]Thong ke theo ngay (14 ngay gan nhat):[/bold cyan]")  # Tiêu đề thống kê theo ngày
    t = Table(box=box.SIMPLE_HEAD, header_style="bold")  # Bảng thống kê theo ngày
    t.add_column("Ngay"); t.add_column("kWh", justify="right")  # Cột ngày và kWh
    t.add_column("Chi phi (VND)", justify="right"); t.add_column("Trang thai", justify="center")  # Cột chi phí và trạng thái
    dates = sorted(set(e.date for e in usage))[-14:]  # Lấy 14 ngày gần nhất từ nhật ký
    for d in dates:  # Duyệt từng ngày
        kwh = sum(dev_map[e.device_id].kwh(e.hours)  # Tính tổng điện ngày đó
                  for e in usage if e.date == d and e.device_id in dev_map)
        t.add_row(d, f"{kwh:.2f}", f"{kwh * config.electricity_rate:,.0f}",  # Thêm hàng dữ liệu
                  "[green]Tot[/green]" if kwh <= config.daily_budget_kwh else "[red]Vuot![/red]")  # Trạng thái có màu
    console.print(t)  # Hiển thị bảng thống kê theo ngày

    console.print("\n[bold cyan]Tong dien theo thiet bi:[/bold cyan]")  # Tiêu đề thống kê theo thiết bị
    t2 = Table(box=box.SIMPLE, header_style="bold")  # Bảng tổng theo thiết bị
    t2.add_column("Thiet bi"); t2.add_column("Tong gio", justify="right")  # Cột tên và tổng giờ
    t2.add_column("Tong kWh", justify="right"); t2.add_column("Chi phi (VND)", justify="right")  # Cột kWh và chi phí
    for dev in sorted(devices, key=lambda d: -sum(e.hours for e in usage if e.device_id == d.id)):  # Sắp xếp theo tổng giờ giảm dần
        total_h = sum(e.hours for e in usage if e.device_id == dev.id)  # Tổng giờ dùng thiết bị này
        if total_h == 0:  # Bỏ qua thiết bị chưa dùng
            continue
        kwh = dev.kwh(total_h)  # Tổng điện tiêu thụ của thiết bị
        t2.add_row(dev.name, f"{total_h:.1f}h", f"{kwh:.2f}", f"{kwh * config.electricity_rate:,.0f}")  # Thêm hàng
    console.print(t2)  # Hiển thị bảng tổng theo thiết bị

    if dates:  # Nếu có dữ liệu ngày
        avg = sum(dev_map[e.device_id].kwh(e.hours)  # Tính tổng điện tất cả ngày
                  for e in usage if e.device_id in dev_map) / len(dates)  # Chia cho số ngày để lấy trung bình
        console.print(f"\n  Trung binh/ngay: [bold]{avg:.2f}[/bold] kWh  "  # Hiển thị trung bình ngày
                      f"->  Uoc tinh/thang: [bold cyan]{avg * 30 * config.electricity_rate:,.0f}[/bold cyan] VND")  # Ước tính tháng
    pause()  # Chờ người dùng nhấn Enter


# ── 4. Toi uu DP vs Greedy ────────────────────────────────────

def menu_optimize() -> None:  # Hàm xử lý tối ưu hóa lịch sử dụng điện DP vs Greedy
    clear(); header()  # Xóa màn hình và hiển thị tiêu đề
    devices = load_devices()  # Tải danh sách thiết bị
    config  = load_config()  # Tải cấu hình

    console.print(Panel(  # Hiển thị panel giới thiệu hai thuật toán
        "[bold]Toi Uu Lich Su Dung Dien[/bold]\n\n"  # Tiêu đề panel
        "So sanh hai thuat toan:\n"  # Mô tả nội dung so sánh
        "  [cyan](1) DP Group Knapsack[/cyan]  --  Toi uu toan cuc,  O(n x W x H)\n"  # Thuật toán DP: tối ưu nhưng chậm hơn
        "  [yellow](2) Greedy (pri/watt)[/yellow]   --  Xap xi nhanh,   O(n log n)",  # Thuật toán Greedy: nhanh nhưng xấp xỉ
        border_style="blue", padding=(0, 2),  # Viền xanh dương
    ))

    budget = FloatPrompt.ask("\nNgan sach dien / ngay (kWh)", default=config.daily_budget_kwh)  # Hỏi ngân sách điện ngày
    console.print()  # In dòng trống

    dp_res = dp_optimize(devices, budget)  # Chạy thuật toán DP Group Knapsack
    gr_res = greedy_optimize(devices, budget)  # Chạy thuật toán Greedy

    _print_result(dp_res, config.electricity_rate, "cyan")  # In kết quả DP màu cyan
    _print_result(gr_res, config.electricity_rate, "yellow")  # In kết quả Greedy màu vàng

    diff = dp_res.total_comfort - gr_res.total_comfort  # Hiệu điểm thoải mái giữa DP và Greedy
    body = (  # Xây dựng nội dung so sánh hai thuật toán
        f"  [cyan]DP[/cyan]     comfort: [bold]{dp_res.total_comfort:.1f}[/bold]"
        f"  dien: {dp_res.total_kwh:.2f} kWh"
        f"  chi phi: {dp_res.total_cost(config.electricity_rate):,.0f} VND\n"
        f"  [yellow]Greedy[/yellow] comfort: [bold]{gr_res.total_comfort:.1f}[/bold]"
        f"  dien: {gr_res.total_kwh:.2f} kWh"
        f"  chi phi: {gr_res.total_cost(config.electricity_rate):,.0f} VND\n\n"
    )
    if diff > 1e-3:  # DP tốt hơn Greedy đáng kể
        body += f"  [green]DP tot hon Greedy +{diff:.1f} diem ({diff / max(gr_res.total_comfort, 1e-9) * 100:.1f}%)[/green]"
    elif diff < -1e-3:  # Greedy tốt hơn DP (hiếm gặp)
        body += f"  [yellow]Greedy tot hon DP +{-diff:.1f} diem (hiem gap)[/yellow]"
    else:  # Hai thuật toán cho kết quả tương đương
        body += "  [dim]Hai thuat toan cho ket qua bang nhau trong truong hop nay.[/dim]"

    console.print(Panel(body, title="[bold]Ket qua so sanh[/bold]", border_style="green", padding=(0, 2)))  # Hiển thị panel so sánh

    if Confirm.ask("\nXem phan vi du DP tot hon Greedy?", default=False):  # Hỏi có muốn xem phản ví dụ không
        demo = counterexample_demo()  # Chạy phản ví dụ Loa Bluetooth vs Điều hòa nhỏ
        console.print(Panel(  # Hiển thị panel phân tích phản ví dụ
            f"[bold]Phan vi du: Greedy that bai trong 0/1 Knapsack[/bold]\n\n"
            f"Budget: 0.30 kWh\n\n"  # Ngân sách của phản ví dụ
            f"  Loa Bluetooth: 200W, pri=3  -> ratio=3/200=0.0150  [yellow](Greedy chon TRUOC)[/yellow]\n"
            f"  Dieu hoa nho : 300W, pri=4  -> ratio=4/300=0.0133  [dim](Greedy bo qua)[/dim]\n\n"
            f"  [yellow]Greedy[/yellow]: chon Loa (0.20kWh,+3diem) -> con 0.10kWh -> Dieu hoa can 0.30 -> khong du\n"
            f"           Tong: [bold yellow]{demo['greedy'].total_comfort:.0f} diem[/bold yellow]\n\n"
            f"  [cyan]DP[/cyan]    : bo qua Loa, chon Dieu hoa (0.30kWh,+4diem)\n"
            f"           Tong: [bold cyan]{demo['dp'].total_comfort:.0f} diem[/bold cyan]\n\n"
            f"  [green]=> DP tot hon Greedy +{demo['dp'].total_comfort - demo['greedy'].total_comfort:.0f} diem![/green]\n\n"
            f"  Nguyen nhan: Greedy 'tham lam' chon item ti le cao truoc, can mat budget\n"
            f"  khien khong con cho item co gia tri thuc su cao hon.",  # Kết luận giải thích lý thuyết
            title="[bold red]Counter-example[/bold red]", border_style="red", padding=(0, 2),
        ))
    pause()  # Chờ người dùng nhấn Enter


def _print_result(res: OptResult, rate: float, style: str) -> None:  # Hàm in kết quả tối ưu dạng bảng
    t = Table(title=f"[{style}]{res.algorithm}[/{style}]",  # Tiêu đề bảng là tên thuật toán có màu
              box=box.ROUNDED, header_style=f"bold {style}")  # Viền tròn, tiêu đề cột có màu
    t.add_column("Thiet bi", min_width=20)  # Cột tên thiết bị
    t.add_column("Gio",     justify="right")  # Cột số giờ, căn phải
    t.add_column("kWh",     justify="right")  # Cột điện tiêu thụ, căn phải
    t.add_column("Comfort", justify="right")  # Cột điểm thoải mái, căn phải
    for item in res.schedule:  # Thêm từng thiết bị trong lịch vào bảng
        t.add_row(item.device.name, f"{item.hours}h", f"{item.kwh:.3f}", f"{item.comfort:.1f}")
    t.add_section()  # Đường kẻ ngang trước hàng tổng
    t.add_row("[bold]Tong[/bold]", "",  # Hàng tổng cộng
              f"[bold]{res.total_kwh:.3f}[/bold]", f"[bold]{res.total_comfort:.1f}[/bold]")
    console.print(t)  # Hiển thị bảng kết quả
    console.print(  # In thêm chi phí và độ phức tạp bên dưới bảng
        f"  Chi phi: [bold]{res.total_cost(rate):,.0f}[/bold] VND/ngay  "
        f"[dim]({res.total_cost(rate) * 30:,.0f} VND/thang)[/dim]\n"  # Chi phí ước tính theo tháng
        f"  [dim]Do phuc tap: {res.complexity}[/dim]\n"  # Thông tin độ phức tạp thuật toán
    )


# ── 5. Lich tranh gio cao diem ────────────────────────────────

def menu_peak() -> None:  # Hàm hiển thị lịch sử dụng tránh giờ cao điểm
    clear(); header()  # Xóa màn hình và hiển thị tiêu đề
    devices = load_devices()  # Tải danh sách thiết bị
    config  = load_config()  # Tải cấu hình (bao gồm danh sách giờ cao điểm)

    console.print("[bold]Phan Bo Gio Dung Dien - Tranh Gio Cao Diem[/bold]")  # Tiêu đề màn hình
    console.print(f"Gio cao diem: [red]{' '.join(str(h)+'h' for h in config.peak_hours)}[/red]\n")  # Danh sách giờ cao điểm màu đỏ

    budget = FloatPrompt.ask("Ngan sach / ngay (kWh)", default=config.daily_budget_kwh)  # Hỏi ngân sách điện ngày
    dp_res = dp_optimize(devices, budget)  # Chạy DP để lấy lịch sử dụng tối ưu
    sched  = peak_aware_schedule(dp_res.schedule, config.peak_hours)  # Phân bổ giờ tránh cao điểm

    console.print("\n[bold cyan]Timeline 24 gio (moi o = 1 gio):[/bold cyan]\n")  # Tiêu đề bản đồ timeline
    console.print(f"  {'Thiet bi':<20} {''.join(f'{h:02d}' for h in range(24))}")  # Hàng nhãn giờ 00-23
    console.print(f"  {'':<20} {'--' * 24}")  # Đường kẻ phân cách tiêu đề và dữ liệu
    for item in dp_res.schedule:  # Duyệt qua từng thiết bị trong lịch tối ưu
        peak_set = set(config.peak_hours)  # Set giờ cao điểm để kiểm tra nhanh
        row = ["  "] * 24  # Khởi tạo 24 ô trống (2 ký tự mỗi ô)
        for h in peak_set:  # Đánh dấu giờ cao điểm bằng "!!"
            if 0 <= h < 24:
                row[h] = "!!"
        for (sh, dur) in sched.get(item.device.id, []):  # Đánh dấu giờ dùng điện bằng "##"
            for h in range(sh, min(sh + int(dur + 0.5), 24)):
                row[h] = "##"
        bar = "".join(  # Tạo chuỗi timeline với màu sắc cho từng ô
            f"[green]##[/green]" if c == "##" else  # Giờ dùng điện: màu xanh lá
            f"[red]!![/red]"    if c == "!!" else  # Giờ cao điểm không dùng: màu đỏ
            f"[dim]..[/dim]"    for c in row  # Giờ không dùng điện: màu mờ
        )
        console.print(f"  {item.device.name:<20} {bar}  [dim]{item.hours}h - {item.kwh:.2f}kWh[/dim]")  # In hàng thiết bị

    console.print("\n  Chu thich: [green]##[/green] dung dien  [red]!![/red] gio cao diem  [dim]..[/dim] khong dung\n")  # Chú thích màu sắc
    pause()  # Chờ người dùng nhấn Enter


# ── 6. Cai dat ───────────────────────────────────────────────

def menu_settings() -> None:  # Hàm xử lý màn hình cài đặt ứng dụng
    clear(); header()  # Xóa màn hình và hiển thị tiêu đề
    config = load_config()  # Tải cấu hình hiện tại
    console.print("[bold]Cai Dat Hien Tai:[/bold]\n")  # Tiêu đề phần hiển thị cài đặt
    console.print(f"  Ngan sach / ngay : [cyan]{config.daily_budget_kwh}[/cyan] kWh")  # Hiển thị ngân sách hiện tại
    console.print(f"  Gia dien          : [cyan]{config.electricity_rate:,.0f}[/cyan] VND/kWh")  # Hiển thị giá điện hiện tại
    console.print(f"  Gio cao diem      : [red]{', '.join(str(h)+'h' for h in config.peak_hours)}[/red]\n")  # Hiển thị giờ cao điểm
    if not Confirm.ask("Cap nhat cai dat?"):  # Hỏi có muốn thay đổi không
        return  # Không thay đổi, quay về menu chính
    config.daily_budget_kwh = FloatPrompt.ask("Ngan sach / ngay (kWh)", default=config.daily_budget_kwh)  # Nhập ngân sách mới
    config.electricity_rate = FloatPrompt.ask("Gia dien (VND/kWh)", default=config.electricity_rate)  # Nhập giá điện mới
    peak_str = Prompt.ask("Gio cao diem (cach nhau bang dau phay)",  # Hỏi giờ cao điểm mới
                          default=",".join(str(h) for h in config.peak_hours))  # Hiển thị giờ cao điểm hiện tại làm mặc định
    try:  # Thử phân tích chuỗi giờ nhập vào
        config.peak_hours = [int(x.strip()) for x in peak_str.split(",")]  # Tách chuỗi và chuyển thành list số nguyên
    except ValueError:  # Nếu định dạng không hợp lệ
        console.print("[red]Dinh dang khong hop le, giu nguyen.[/red]")  # Báo lỗi, giữ nguyên giờ cũ
    save_config(config)  # Lưu cấu hình đã cập nhật
    console.print("[green]Da luu cai dat![/green]")  # Xác nhận lưu thành công
    pause()  # Chờ người dùng nhấn Enter


# ══════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════

def main() -> None:  # Hàm chính điều phối toàn bộ ứng dụng CLI
    dispatch = {  # Dict ánh xạ lựa chọn menu → hàm xử lý tương ứng
        "1": menu_devices, "2": menu_usage, "3": menu_stats,  # Quản lý, nhật ký, thống kê
        "4": menu_optimize, "5": menu_peak, "6": menu_settings,  # Tối ưu, lịch cao điểm, cài đặt
    }
    while True:  # Vòng lặp chính: chạy mãi cho đến khi người dùng thoát
        clear(); header()  # Xóa màn hình và hiển thị tiêu đề
        ch = main_menu()  # Hiển thị menu chính và nhận lựa chọn
        if ch == "0":  # Người dùng chọn thoát
            console.print("\n[cyan]Tam biet! Tiet kiem dien nhe![/cyan]\n")  # Lời tạm biệt thân thiện
            break  # Thoát vòng lặp, kết thúc chương trình
        dispatch[ch]()  # Gọi hàm xử lý tương ứng với lựa chọn của người dùng


if __name__ == "__main__":  # Chỉ chạy khi gọi trực tiếp file này (không phải khi import)
    main()  # Khởi động ứng dụng CLI
