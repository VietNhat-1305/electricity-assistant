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
║    δ = 0.1 kWh (độ mịn ngân sách), Δ = 0.5h (bước giờ)     ║
║                                                               ║
║  Thuật toán 2 — Greedy (tỷ lệ ưu tiên / công suất)          ║
║    Xấp xỉ   | Time O(n log n)   | Space O(n)                ║
╚══════════════════════════════════════════════════════════════╝
"""

from __future__ import annotations
import math
from dataclasses import dataclass
from typing import List, Tuple
from models import Device

BUDGET_UNIT = 0.01  # kWh / đơn vị ngân sách trong bảng DP (độ mịn cao hơn)
HOUR_STEP   = 0.5   # bước giờ (0.5h = 30 phút)


# ──────────────────────────────────────────────────────────────
# Data classes kết quả
# ──────────────────────────────────────────────────────────────

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


# ──────────────────────────────────────────────────────────────
# Helper
# ──────────────────────────────────────────────────────────────

def _options(dev: Device) -> List[Tuple[int, float, float]]:
    """
    Sinh các lựa chọn (cost_units, comfort_value, hours) cho thiết bị.
    Dùng int(x + 0.5) thay round() để tránh banker's rounding của Python 3.
    Áp dụng max(1, ...) để không thiết bị nào được coi là "miễn phí".
    """
    result = []
    h = HOUR_STEP
    while h <= dev.max_daily_hours + 1e-9:
        cost_u = max(1, int(dev.kwh(h) / BUDGET_UNIT + 0.5))
        val    = dev.priority * h
        result.append((cost_u, val, h))
        h += HOUR_STEP
    return result


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
    n = len(devices)
    W = int(budget_kwh / BUDGET_UNIT) + 1  # số đơn vị ngân sách

    # dp[i][j]: comfort tối đa dùng i thiết bị đầu, budget j đơn vị
    dp     = [[0.0] * W for _ in range(n + 1)]
    choice = [[0.0] * W for _ in range(n)]   # giờ đã chọn để truy vết

    for i, dev in enumerate(devices):
        opts = _options(dev)
        for j in range(W):
            dp[i + 1][j] = dp[i][j]   # mặc định: không dùng thiết bị i
            choice[i][j] = 0.0

            for cost_u, val, h in opts:
                if j >= cost_u:
                    candidate = dp[i][j - cost_u] + val
                    if candidate > dp[i + 1][j]:
                        dp[i + 1][j] = candidate
                        choice[i][j] = h

    # Tìm mức ngân sách cho điểm thoải mái cao nhất
    best_j = max(range(W), key=lambda j: dp[n][j])

    # Truy vết lịch sử dụng từ bảng choice
    schedule: List[ScheduleItem] = []
    j = best_j
    for i in range(n - 1, -1, -1):
        h = choice[i][j]
        if h > 0:
            cost_u = max(1, int(devices[i].kwh(h) / BUDGET_UNIT + 0.5))
            schedule.append(ScheduleItem(devices[i], h))
            j -= cost_u

    total_kwh     = sum(s.kwh for s in schedule)
    total_comfort = dp[n][best_j]

    n_opts = max((len(_options(d)) for d in devices), default=1)
    return OptResult(
        schedule=sorted(schedule, key=lambda x: -x.comfort),
        total_comfort=total_comfort,
        total_kwh=total_kwh,
        algorithm="DP — Group Knapsack",
        complexity=(
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
    Ví dụ phản ví dụ:
      Budget = 0.9 kWh, AC(900W, pri=4) vs Fan(55W, pri=5):
        Greedy chọn Fan trước (ratio 5/55 > 4/900), dùng ~16h Fan = 0.88 kWh → 80 điểm
        DP cũng chọn tương tự trong trường hợp này, nhưng không phải lúc nào cũng vậy.

    Độ phức tạp:
      Time : O(n log n)  — chỉ cần sắp xếp
      Space: O(n)
    """
    sorted_devs = sorted(
        devices,
        key=lambda d: d.priority / d.power_w,
        reverse=True,
    )

    remaining = budget_kwh
    schedule: List[ScheduleItem] = []

    for dev in sorted_devs:
        if remaining < 1e-9:
            break
        max_h_by_budget = remaining / (dev.power_w / 1000)
        hours = min(dev.max_daily_hours, max_h_by_budget)
        hours = math.floor(hours / HOUR_STEP) * HOUR_STEP  # làm tròn XUỐNG để không vượt budget
        if hours >= HOUR_STEP:
            schedule.append(ScheduleItem(dev, hours))
            remaining -= dev.kwh(hours)

    total_kwh     = sum(s.kwh for s in schedule)
    total_comfort = sum(s.comfort for s in schedule)

    return OptResult(
        schedule=sorted(schedule, key=lambda x: -x.comfort),
        total_comfort=total_comfort,
        total_kwh=total_kwh,
        algorithm="Greedy — Tỷ lệ Ưu tiên / Công suất",
        complexity="Time O(n log n)  |  Space O(n)",
    )


# ──────────────────────────────────────────────────────────────
# Counterexample: chứng minh Greedy không tối ưu toàn cục
# ──────────────────────────────────────────────────────────────

def counterexample_demo() -> dict:
    """
    Phản ví dụ kinh điển — Greedy thua DP.

    Budget = 0.30 kWh (30 units, delta=0.01)

    Thiet bi:
      Loa Bluetooth:  200W, priority=3, max=1h
        ratio = 3/200 = 0.0150  (cao hon, Greedy chon truoc)
        cost  = 0.20 kWh
        value = 3

      Dieu hoa (nho):  300W, priority=4, max=1h
        ratio = 4/300 = 0.0133  (thap hon, Greedy chon sau)
        cost  = 0.30 kWh
        value = 4

    Greedy: chon Loa truoc (ratio cao hon) → dung 0.20 kWh, con lai 0.10 kWh
            Dieu hoa can 0.30 kWh → khong du → bo qua
            Tong: 3 diem

    DP:     bo qua Loa, chon Dieu hoa (0.30 kWh, value=4)
            Tong: 4 diem  →  DP THANG GREEDY!

    Day chinh la failure case cua Greedy trong 0/1 Knapsack:
    chon item "hieu qua theo ti le" truoc nhung lai can mat budget
    de roi khong con cho item gia tri cao hon.
    """
    loa   = Device("loa_demo", "Loa Bluetooth (demo)", 200, 3, 1.0, "entertainment")
    dh    = Device("dh_demo",  "Dieu hoa nho (demo)",  300, 4, 1.0, "cooling")
    devs  = [loa, dh]
    budget = 0.30

    dp_r  = dp_optimize(devs, budget)
    gr_r  = greedy_optimize(devs, budget)

    return {
        "devices":  devs,
        "budget":   budget,
        "dp":       dp_r,
        "greedy":   gr_r,
        "dp_wins":  dp_r.total_comfort > gr_r.total_comfort + 1e-6,
    }


# ──────────────────────────────────────────────────────────────
# Phân bổ giờ tránh giờ cao điểm (heuristic)
# ──────────────────────────────────────────────────────────────

def peak_aware_schedule(
    schedule: List[ScheduleItem],
    peak_hours: List[int],
) -> dict[str, list[tuple[int, float]]]:
    """
    Phân bổ giờ sử dụng thiết bị sao cho tránh giờ cao điểm.

    Heuristic:
      - Thiết bị công suất cao (≥ 500W) → đẩy sang giờ thấp điểm trước.
      - Thiết bị công suất thấp   → linh hoạt hơn.

    Trả về: {device_id: [(start_hour, duration_h), ...]}
    """
    peak_set = set(peak_hours)
    off_peak = [h for h in range(24) if h not in peak_set]
    peak_asc = sorted(peak_hours)

    result: dict[str, list[tuple[int, float]]] = {}

    for item in schedule:
        dev   = item.device
        slots: list[tuple[int, float]] = []
        left  = item.hours

        # Thiết bị tốn điện → ưu tiên giờ thấp điểm
        pool = off_peak if dev.power_w >= 500 else (off_peak + peak_asc)

        for h in pool:
            if left < 1e-9:
                break
            used = min(1.0, left)
            slots.append((h, used))
            left -= used

        result[dev.id] = slots

    return result
