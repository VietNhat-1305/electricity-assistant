"""
Thuật toán tối ưu hóa lịch sử dụng điện — phòng trọ sinh viên.

╔══════════════════════════════════════════════════════════════╗
║  BÀI TOÁN: GROUP KNAPSACK (Ba lô nhóm)                      ║
╠══════════════════════════════════════════════════════════════╣
║  Input:                                                       ║
║    n thiết bị, mỗi thiết bị i có:                           ║
║      power_w[i]   : công suất (Watt)                        ║
║      priority[i]  : mức ưu tiên (1–5)                       ║
║      max_hours[i] : giờ tối đa / ngày                       ║
║    W : ngân sách điện / ngày (kWh)                           ║
║                                                               ║
║  Với mỗi thiết bị i, chọn h[i] ∈ {0, 0.5, 1, …, max_h[i]} ║
║    Chi phí : cost(i,h) = power_w[i] × h / 1000   (kWh)     ║
║    Lợi ích : val(i,h)  = priority[i] × h          (điểm)   ║
║                                                               ║
║  Mục tiêu  : Tối đa hóa Σ val(i, h[i])                      ║
║              sao cho     Σ cost(i, h[i]) ≤ W                 ║
╠══════════════════════════════════════════════════════════════╣
║  Thuật toán 1 — DP (Group Knapsack)                          ║
║    Optimal  | Time O(n·W/δ·H/Δ) | Space O(n·W/δ)            ║
║    δ = 0.01 kWh (độ mịn ngân sách), Δ = 0.5h (bước giờ)    ║
║                                                               ║
║  Thuật toán 2 — Greedy (tỷ lệ ưu tiên / công suất)          ║
║    Xấp xỉ   | Time O(n log n)   | Space O(n)                ║
╚══════════════════════════════════════════════════════════════╝
"""

from __future__ import annotations  # Cho phép dùng type hint kiểu chuỗi (forward reference)
import math  # Thư viện toán học, dùng math.floor để làm tròn xuống
from dataclasses import dataclass  # Decorator tạo lớp dữ liệu tự động
from typing import List, Tuple  # Import kiểu danh sách và bộ giá trị
from models import Device  # Import lớp Device từ models.py

BUDGET_UNIT = 0.01  # Độ mịn ngân sách trong bảng DP: mỗi đơn vị = 0.01 kWh (1 Wh)
HOUR_STEP   = 0.5   # Bước thời gian: mỗi lựa chọn tăng thêm 0.5 giờ (30 phút)


# ──────────────────────────────────────────────────────────────
# Data classes kết quả
# ──────────────────────────────────────────────────────────────

@dataclass  # Tự động tạo __init__, __repr__ cho lớp
class ScheduleItem:  # Lớp đại diện một mục trong lịch sử dụng điện đã tối ưu
    device: Device  # Thiết bị được lên lịch sử dụng
    hours: float  # Số giờ sử dụng thiết bị trong ngày

    @property  # Thuộc tính tính toán (không lưu, tính mỗi lần gọi)
    def kwh(self) -> float:  # Điện năng tiêu thụ của mục này
        return self.device.kwh(self.hours)  # Ủy quyền tính toán cho phương thức kwh của Device

    @property  # Thuộc tính tính toán điểm thoải mái
    def comfort(self) -> float:  # Điểm thoải mái = mức ưu tiên × số giờ dùng
        return self.device.priority * self.hours  # Công thức tính điểm thoải mái


@dataclass  # Tự động tạo __init__ cho lớp kết quả tối ưu
class OptResult:  # Lớp chứa kết quả đầy đủ của một lần chạy thuật toán tối ưu
    schedule: List[ScheduleItem]  # Danh sách các thiết bị và giờ đã lên lịch
    total_comfort: float  # Tổng điểm thoải mái đạt được
    total_kwh: float  # Tổng điện năng tiêu thụ (kWh)
    algorithm: str  # Tên thuật toán đã sử dụng (để hiển thị)
    complexity: str  # Chuỗi mô tả độ phức tạp thuật toán

    def total_cost(self, rate: float) -> float:  # Tính tổng chi phí điện bằng VND
        return self.total_kwh * rate  # Nhân tổng kWh với giá điện VND/kWh


# ──────────────────────────────────────────────────────────────
# Helper
# ──────────────────────────────────────────────────────────────

def _options(dev: Device) -> List[Tuple[int, float, float]]:
    """
    Sinh các lựa chọn (cost_units, comfort_value, hours) cho thiết bị.
    Dùng int(x + 0.5) thay round() để tránh banker's rounding của Python 3.
    Áp dụng max(1, ...) để không thiết bị nào được coi là "miễn phí".
    """
    result = []  # Danh sách các lựa chọn giờ sử dụng cho thiết bị này
    h = HOUR_STEP  # Bắt đầu từ 0.5h (không xét 0h vì không dùng = không đưa vào lịch)
    while h <= dev.max_daily_hours + 1e-9:  # Lặp qua tất cả mức giờ đến giới hạn tối đa
        cost_u = max(1, int(dev.kwh(h) / BUDGET_UNIT + 0.5))  # Số đơn vị ngân sách cần (làm tròn, ít nhất 1)
        val    = dev.priority * h  # Điểm thoải mái khi dùng h giờ
        result.append((cost_u, val, h))  # Thêm bộ (chi phí đơn vị, giá trị, giờ) vào danh sách
        h += HOUR_STEP  # Tăng bước giờ lên 0.5h tiếp theo
    return result  # Trả về danh sách tất cả lựa chọn có thể của thiết bị


# ──────────────────────────────────────────────────────────────
# Thuật toán 1: DP — Group Knapsack
# ──────────────────────────────────────────────────────────────

def dp_optimize(devices: List[Device], budget_kwh: float) -> OptResult:
    """
    Quy hoạch động — Group Knapsack.

    Trạng thái:
      dp[i][j] = điểm thoải mái tối đa khi xét i thiết bị đầu tiên,
                 với ngân sách j × BUDGET_UNIT kWh.

    Chuyển trạng thái (với mỗi thiết bị i và mọi ngân sách j):
      dp[i+1][j] = max(
          dp[i][j],                                # không dùng thiết bị i
          max_{h} dp[i][j - cost(i,h)] + val(i,h) # dùng h giờ
      )

    Truy vết:
      choice[i][j] = số giờ đã chọn cho thiết bị i khi dp[i+1][j] tối ưu.

    Độ phức tạp:
      Time : O(n × (W/δ) × (max_h/Δ))
      Space: O(n × W/δ)
      Với n=10, W=2 kWh, δ=0.01, max_h=12h, Δ=0.5 → ~96 000 phép tính
    """
    n = len(devices)  # Số lượng thiết bị cần tối ưu
    W = int(budget_kwh / BUDGET_UNIT) + 1  # Tổng số đơn vị ngân sách (cột bảng DP)

    # Bảng DP: dp[i][j] = điểm thoải mái tối đa với i thiết bị đầu, budget j đơn vị
    dp     = [[0.0] * W for _ in range(n + 1)]  # Khởi tạo bảng DP với (n+1) hàng và W cột
    choice = [[0.0] * W for _ in range(n)]  # Bảng truy vết: lưu số giờ đã chọn tại mỗi ô

    for i, dev in enumerate(devices):  # Duyệt qua từng thiết bị (hàng của bảng DP)
        opts = _options(dev)  # Lấy danh sách tất cả lựa chọn giờ của thiết bị i
        for j in range(W):  # Duyệt qua từng mức ngân sách (cột của bảng DP)
            dp[i + 1][j] = dp[i][j]  # Mặc định: không chọn thiết bị i, giữ nguyên giá trị
            choice[i][j] = 0.0  # Ghi nhận chưa chọn giờ nào cho thiết bị i

            for cost_u, val, h in opts:  # Thử từng mức giờ có thể cho thiết bị i
                if j >= cost_u:  # Chỉ xét nếu ngân sách j đủ để dùng h giờ
                    candidate = dp[i][j - cost_u] + val  # Điểm nếu chọn thiết bị i với h giờ
                    if candidate > dp[i + 1][j]:  # Nếu tốt hơn kết quả hiện tại
                        dp[i + 1][j] = candidate  # Cập nhật giá trị tối ưu
                        choice[i][j] = h  # Ghi nhận số giờ dẫn đến kết quả tối ưu

    # Tìm mức ngân sách j* cho điểm thoải mái tối đa sau khi xét toàn bộ n thiết bị
    best_j = max(range(W), key=lambda j: dp[n][j])  # Tìm cột j có dp[n][j] lớn nhất

    # Truy vết ngược từ bảng choice để tìm lịch sử dụng tối ưu
    schedule: List[ScheduleItem] = []  # Danh sách thiết bị được chọn (kết quả truy vết)
    j = best_j  # Bắt đầu truy vết từ cột ngân sách tối ưu
    for i in range(n - 1, -1, -1):  # Đi ngược từ thiết bị cuối về đầu
        h = choice[i][j]  # Lấy số giờ đã chọn cho thiết bị i tại ngân sách j
        if h > 0:  # Nếu thiết bị i được chọn (giờ > 0)
            cost_u = max(1, int(devices[i].kwh(h) / BUDGET_UNIT + 0.5))  # Tính lại chi phí đơn vị
            schedule.append(ScheduleItem(devices[i], h))  # Thêm thiết bị vào lịch kết quả
            j -= cost_u  # Giảm ngân sách để tiếp tục truy vết

    total_kwh     = sum(s.kwh for s in schedule)  # Tổng điện năng tiêu thụ của lịch được chọn
    total_comfort = dp[n][best_j]  # Tổng điểm thoải mái tối ưu từ bảng DP

    n_opts = max((len(_options(d)) for d in devices), default=1)  # Số lựa chọn tối đa của một thiết bị
    return OptResult(  # Trả về kết quả tối ưu đầy đủ
        schedule=sorted(schedule, key=lambda x: -x.comfort),  # Sắp xếp lịch theo điểm thoải mái giảm dần
        total_comfort=total_comfort,  # Tổng điểm thoải mái
        total_kwh=total_kwh,  # Tổng điện tiêu thụ
        algorithm="DP — Group Knapsack",  # Nhãn tên thuật toán để hiển thị
        complexity=(  # Chuỗi mô tả độ phức tạp với số liệu cụ thể
            f"Time O(n·W/δ·H/Δ) = O({n}·{W}·{n_opts}) ≈ {n*W*n_opts:,} phép tính  |  "
            f"Space O(n·W/δ) = O({n}·{W}) = {n*W:,} ô nhớ"
        ),
    )


# ──────────────────────────────────────────────────────────────
# Thuật toán 2: Greedy — tỷ lệ ưu tiên / công suất
# ──────────────────────────────────────────────────────────────

def greedy_optimize(devices: List[Device], budget_kwh: float) -> OptResult:
    """
    Greedy: xếp hạng thiết bị theo tỷ lệ priority / power_w.

    Ý tưởng: thiết bị có ưu tiên cao nhưng tốn ít điện → "hiệu quả" hơn.
    Lần lượt cấp phát ngân sách cho từng thiết bị theo thứ tự đó.

    ⚠️  Greedy KHÔNG đảm bảo tối ưu toàn cục.

    Độ phức tạp:
      Time : O(n log n)  — chỉ cần sắp xếp
      Space: O(n)
    """
    sorted_devs = sorted(  # Sắp xếp thiết bị theo tỷ lệ ưu tiên/công suất từ cao xuống thấp
        devices,
        key=lambda d: d.priority / d.power_w,  # Tiêu chí sắp xếp: priority chia power_w
        reverse=True,  # Sắp xếp giảm dần (thiết bị "hiệu quả" nhất lên đầu)
    )

    remaining = budget_kwh  # Ngân sách điện còn lại để phân bổ (kWh)
    schedule: List[ScheduleItem] = []  # Danh sách thiết bị được chọn

    for dev in sorted_devs:  # Duyệt qua từng thiết bị theo thứ tự ưu tiên
        if remaining < 1e-9:  # Nếu ngân sách đã cạn (nhỏ hơn ngưỡng epsilon) thì dừng
            break
        max_h_by_budget = remaining / (dev.power_w / 1000)  # Số giờ tối đa thiết bị có thể dùng với ngân sách còn lại
        hours = min(dev.max_daily_hours, max_h_by_budget)  # Giới hạn bởi cả ngân sách lẫn giới hạn giờ tối đa
        hours = math.floor(hours / HOUR_STEP) * HOUR_STEP  # Làm tròn XUỐNG theo bước giờ để không vượt ngân sách
        if hours >= HOUR_STEP:  # Chỉ chọn thiết bị nếu dùng được ít nhất 0.5 giờ
            schedule.append(ScheduleItem(dev, hours))  # Thêm vào lịch
            remaining -= dev.kwh(hours)  # Trừ điện năng thiết bị này khỏi ngân sách còn lại

    total_kwh     = sum(s.kwh for s in schedule)  # Tổng điện tiêu thụ của lịch Greedy
    total_comfort = sum(s.comfort for s in schedule)  # Tổng điểm thoải mái của lịch Greedy

    return OptResult(  # Trả về kết quả thuật toán Greedy
        schedule=sorted(schedule, key=lambda x: -x.comfort),  # Sắp xếp theo điểm thoải mái giảm dần
        total_comfort=total_comfort,  # Tổng điểm thoải mái
        total_kwh=total_kwh,  # Tổng điện tiêu thụ
        algorithm="Greedy — Tỷ lệ Ưu tiên / Công suất",  # Nhãn tên thuật toán
        complexity="Time O(n log n)  |  Space O(n)",  # Độ phức tạp đơn giản hơn DP
    )


# ──────────────────────────────────────────────────────────────
# Counterexample: chứng minh Greedy không tối ưu toàn cục
# ──────────────────────────────────────────────────────────────

def counterexample_demo() -> dict:
    """
    Phản ví dụ kinh điển — Greedy thua DP.

    Budget = 0.30 kWh

    Loa Bluetooth:  200W, priority=3, max=1h
      ratio = 3/200 = 0.0150  (Greedy chọn TRƯỚC vì ratio cao hơn)
      cost  = 0.20 kWh | value = 3

    Điều hòa nhỏ:  300W, priority=4, max=1h
      ratio = 4/300 = 0.0133  (Greedy chọn sau)
      cost  = 0.30 kWh | value = 4

    Greedy: chọn Loa trước → dùng 0.20 kWh, còn lại 0.10 kWh
            Điều hòa cần 0.30 kWh → không đủ → bỏ qua
            Tổng: 3 điểm

    DP:     bỏ qua Loa, chọn Điều hòa (0.30 kWh, value=4)
            Tổng: 4 điểm  →  DP THẮNG GREEDY!
    """
    loa   = Device("loa_demo", "Loa Bluetooth (demo)", 200, 3, 1.0, "entertainment")  # Thiết bị A: Loa 200W ưu tiên 3
    dh    = Device("dh_demo",  "Dieu hoa nho (demo)",  300, 4, 1.0, "cooling")  # Thiết bị B: Điều hòa 300W ưu tiên 4
    devs  = [loa, dh]  # Danh sách 2 thiết bị trong phản ví dụ
    budget = 0.30  # Ngân sách giới hạn 0.30 kWh để tạo xung đột giữa hai thiết bị

    dp_r  = dp_optimize(devs, budget)  # Chạy DP trên 2 thiết bị và ngân sách 0.30 kWh
    gr_r  = greedy_optimize(devs, budget)  # Chạy Greedy trên cùng bài toán

    return {  # Trả về dict kết quả để UI hiển thị phân tích
        "devices":  devs,  # Danh sách 2 thiết bị trong phản ví dụ
        "budget":   budget,  # Ngân sách sử dụng trong phản ví dụ
        "dp":       dp_r,  # Kết quả thuật toán DP
        "greedy":   gr_r,  # Kết quả thuật toán Greedy
        "dp_wins":  dp_r.total_comfort > gr_r.total_comfort + 1e-6,  # True nếu DP tốt hơn Greedy
    }


# ──────────────────────────────────────────────────────────────
# Phân bổ giờ tránh giờ cao điểm (heuristic)
# ──────────────────────────────────────────────────────────────

def peak_aware_schedule(
    schedule: List[ScheduleItem],  # Lịch sử dụng đã tối ưu (từ DP hoặc Greedy)
    peak_hours: List[int],  # Danh sách các giờ cao điểm cần tránh (vd: [17,18,19,20,21])
) -> dict[str, list[tuple[int, float]]]:
    """
    Phân bổ giờ sử dụng thiết bị sao cho tránh giờ cao điểm.

    Heuristic:
      - Thiết bị công suất cao (≥ 500W) → đẩy sang giờ thấp điểm trước.
      - Thiết bị công suất thấp   → linh hoạt hơn.

    Trả về: {device_id: [(start_hour, duration_h), ...]}
    """
    peak_set = set(peak_hours)  # Chuyển danh sách giờ cao điểm thành set để tra cứu O(1)
    off_peak = [h for h in range(24) if h not in peak_set]  # Danh sách 24 giờ trừ đi các giờ cao điểm
    peak_asc = sorted(peak_hours)  # Sắp xếp giờ cao điểm tăng dần để dùng sau khi hết giờ thấp điểm

    result: dict[str, list[tuple[int, float]]] = {}  # Kết quả: ánh xạ device_id → danh sách (giờ, thời lượng)

    for item in schedule:  # Duyệt qua từng thiết bị trong lịch tối ưu
        dev   = item.device  # Lấy thông tin thiết bị
        slots: list[tuple[int, float]] = []  # Danh sách khung giờ phân bổ cho thiết bị này
        left  = item.hours  # Số giờ còn cần phân bổ

        # Thiết bị ≥500W (tốn điện) → chỉ dùng giờ thấp điểm; còn lại → linh hoạt cả hai loại giờ
        pool = off_peak if dev.power_w >= 500 else (off_peak + peak_asc)  # Chọn danh sách giờ ưu tiên

        for h in pool:  # Duyệt qua từng giờ trong danh sách ưu tiên
            if left < 1e-9:  # Đã phân bổ đủ số giờ cần thiết thì dừng
                break
            used = min(1.0, left)  # Mỗi khung giờ tối đa 1 giờ, hoặc ít hơn nếu còn ít
            slots.append((h, used))  # Ghi nhận phân bổ giờ h với thời lượng used
            left -= used  # Giảm số giờ còn cần phân bổ

        result[dev.id] = slots  # Lưu kết quả phân bổ cho thiết bị này

    return result  # Trả về toàn bộ lịch phân bổ theo giờ cho tất cả thiết bị
