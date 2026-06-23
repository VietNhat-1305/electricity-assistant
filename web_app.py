#!/usr/bin/env python3
"""
Trợ Lý Tiết Kiệm Điện — Web App
pip install flask  ->  python web_app.py  ->  http://localhost:5000
"""

# Nhập các thư viện cần thiết
import json, math, os                                          # json: đọc/ghi file JSON | math: làm tròn | os: thao tác file
from dataclasses import dataclass, field                       # dataclass: tạo class dữ liệu gọn hơn | field: giá trị mặc định
from datetime import date, timedelta                           # date: lấy ngày hôm nay | timedelta: tính ngày trước đó
from typing import List, Tuple                                 # khai báo kiểu dữ liệu rõ ràng hơn
from flask import Flask, jsonify, render_template, request     # Flask: web framework | jsonify: trả về JSON | render_template: render HTML | request: đọc dữ liệu từ client

# ══════════════════════════════════════════════════════════════
# MODELS — Định nghĩa cấu trúc dữ liệu
# ══════════════════════════════════════════════════════════════

@dataclass                                      # decorator giúp tự tạo __init__, __repr__ tự động
class Device:
    id: str                                     # mã định danh duy nhất của thiết bị (vd: "ac", "fan")
    name: str                                   # tên hiển thị (vd: "Điều hòa")
    power_w: int                                # công suất tính bằng Watt
    priority: int                               # mức ưu tiên từ 1 (thấp) đến 5 (cao nhất)
    max_daily_hours: float                      # số giờ tối đa có thể dùng mỗi ngày
    category: str                               # danh mục: cooling, lighting, computing, heating...
    def kwh(self, h):                           # phương thức tính điện năng tiêu thụ (kWh) khi dùng h giờ
        return self.power_w * h / 1000          # công thức: W × giờ / 1000 = kWh
    def to_dict(self):                          # chuyển object thành dict để serialize sang JSON
        return self.__dict__.copy()             # sao chép toàn bộ thuộc tính thành dict

@dataclass                                      # định nghĩa class nhật ký sử dụng theo ngày
class UsageEntry:
    device_id: str                              # ID thiết bị đã dùng
    date: str                                   # ngày sử dụng dạng chuỗi "YYYY-MM-DD"
    hours: float                                # số giờ đã sử dụng trong ngày đó
    note: str = ""                              # ghi chú tùy chọn, mặc định rỗng
    def to_dict(self):                          # chuyển sang dict để lưu JSON
        return self.__dict__.copy()

@dataclass                                      # class lưu cài đặt người dùng
class Config:
    daily_budget_kwh: float = 2.0              # ngân sách điện mỗi ngày tính bằng kWh, mặc định 2.0
    electricity_rate: float = 3500.0           # giá điện trung bình (₫/kWh), dùng để ước tính chi phí
    peak_hours: List[int] = field(default_factory=lambda: [17,18,19,20,21])  # danh sách giờ cao điểm EVN
    def to_dict(self):                          # chuyển sang dict để lưu JSON
        return self.__dict__.copy()

# Danh sách thiết bị mặc định khi khởi động lần đầu
DEFAULT_DEVICES: List[Device] = [
    Device("ac",      "Điều hòa",        900,  4,  8.0, "cooling"),       # điều hòa 900W, ưu tiên 4, tối đa 8h/ngày
    Device("fan",     "Quạt điện",        55,  5, 12.0, "cooling"),       # quạt 55W, ưu tiên cao nhất 5, tối đa 12h
    Device("light",   "Đèn LED",          15,  5, 12.0, "lighting"),      # đèn LED 15W tiết kiệm điện, ưu tiên 5
    Device("laptop",  "Laptop",           65,  5, 10.0, "computing"),     # laptop 65W, dùng tối đa 10h/ngày
    Device("phone",   "Sạc điện thoại",   10,  4,  4.0, "computing"),    # sạc phone 10W, tối đa 4h
    Device("heater",  "Bình nước nóng", 2000,  3,  1.0, "heating"),      # bình nóng lạnh 2000W, tốn điện nhất
    Device("tv",      "Tivi",            100,  2,  4.0, "entertainment"), # tivi 100W, ưu tiên thấp 2
    Device("rice",    "Nồi cơm điện",    700,  5,  1.0, "cooking"),      # nồi cơm 700W, ưu tiên cao nhưng chỉ 1h
    Device("fridge",  "Tủ lạnh mini",     80,  3, 24.0, "cooling"),      # tủ lạnh 80W, chạy liên tục 24h
    Device("washing", "Máy giặt",        500,  4,  1.0, "cleaning"),     # máy giặt 500W, 1h/ngày
]

# ══════════════════════════════════════════════════════════════
# STORAGE — Đọc và ghi dữ liệu vào file JSON
# ══════════════════════════════════════════════════════════════

_DIR     = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")  # thư mục data/ cùng cấp với web_app.py
_DEVICES = os.path.join(_DIR, "devices.json")  # đường dẫn file lưu danh sách thiết bị
_USAGE   = os.path.join(_DIR, "usage.json")    # đường dẫn file lưu nhật ký sử dụng
_CONFIG  = os.path.join(_DIR, "config.json")   # đường dẫn file lưu cài đặt người dùng

def _ensure():
    os.makedirs(_DIR, exist_ok=True)            # tạo thư mục data/ nếu chưa tồn tại, bỏ qua nếu đã có

def load_devices():
    _ensure()                                   # đảm bảo thư mục data/ tồn tại
    if not os.path.exists(_DEVICES):            # nếu file devices.json chưa có
        save_devices(list(DEFAULT_DEVICES))     # tạo file mới với danh sách thiết bị mặc định
        return list(DEFAULT_DEVICES)            # trả về danh sách mặc định
    with open(_DEVICES, encoding="utf-8") as f: # mở file với encoding UTF-8 để đọc tiếng Việt
        return [Device(**d) for d in json.load(f)]  # parse JSON thành list Device objects

def save_devices(devs):
    _ensure()                                   # đảm bảo thư mục tồn tại
    with open(_DEVICES,"w",encoding="utf-8") as f:  # mở file để ghi, UTF-8
        json.dump([d.__dict__ for d in devs], f, ensure_ascii=False, indent=2)  # ghi JSON đẹp, giữ tiếng Việt

def load_usage():
    _ensure()                                   # đảm bảo thư mục tồn tại
    if not os.path.exists(_USAGE):              # nếu chưa có file nhật ký
        return []                               # trả về danh sách rỗng
    with open(_USAGE, encoding="utf-8") as f:  # mở file nhật ký
        return [UsageEntry(**e) for e in json.load(f)]  # parse JSON thành list UsageEntry objects

def save_usage(entries):
    _ensure()                                   # đảm bảo thư mục tồn tại
    with open(_USAGE,"w",encoding="utf-8") as f:       # mở file để ghi
        json.dump([e.__dict__ for e in entries], f, ensure_ascii=False, indent=2)  # lưu list entries dưới dạng JSON

def load_config():
    _ensure()                                   # đảm bảo thư mục tồn tại
    if not os.path.exists(_CONFIG):             # nếu chưa có file config
        return Config()                         # trả về Config với giá trị mặc định
    with open(_CONFIG, encoding="utf-8") as f: # mở file config
        return Config(**json.load(f))           # parse JSON thành Config object

def save_config(c):
    _ensure()                                   # đảm bảo thư mục tồn tại
    with open(_CONFIG,"w",encoding="utf-8") as f:      # mở file để ghi
        json.dump(c.__dict__, f, ensure_ascii=False, indent=2)  # lưu config thành JSON

# ══════════════════════════════════════════════════════════════
# ALGORITHMS — Thuật toán tối ưu hóa
# ══════════════════════════════════════════════════════════════

BUDGET_UNIT = 0.01   # đơn vị chia nhỏ ngân sách: mỗi ô = 0.01 kWh (độ mịn cao, tránh sai số lớn)
HOUR_STEP   = 0.5    # bước giờ: 0.5h = 30 phút (lựa chọn h ∈ {0.5, 1.0, 1.5, ...})

def _opts(dev):
    """Sinh tất cả lựa chọn (chi_phí_ô, điểm_thoải_mái, số_giờ) cho thiết bị dev."""
    r = []                                      # danh sách kết quả các lựa chọn
    h = HOUR_STEP                               # bắt đầu từ h = 0.5h (không dùng 0h vì không có ý nghĩa)
    while h <= dev.max_daily_hours + 1e-9:      # duyệt h từ 0.5 đến max_daily_hours (thêm epsilon tránh lỗi float)
        cost_units = max(1, int(dev.kwh(h) / BUDGET_UNIT + 0.5))  # số ô ngân sách cần dùng (làm tròn, tối thiểu 1)
        value      = dev.priority * h           # điểm thoải mái = độ ưu tiên × số giờ
        r.append((cost_units, value, h))        # thêm tuple (chi_phí_ô, điểm, giờ) vào danh sách
        h += HOUR_STEP                          # tăng h lên 0.5h cho lần lặp tiếp theo
    return r                                    # trả về tất cả lựa chọn của thiết bị này

def dp_optimize(devices, budget_kwh):
    """
    Thuật toán QHĐ Group Knapsack — Tìm lịch sử dụng tối ưu toàn cục.
    Độ phức tạp: O(n × W/δ × H/Δ) — đảm bảo kết quả tối ưu.
    """
    n = len(devices)                            # số lượng thiết bị
    W = int(budget_kwh / BUDGET_UNIT) + 1      # số ô ngân sách (vd: 2kWh / 0.01 = 200 ô)
    dp = [[0.0] * W for _ in range(n + 1)]     # bảng DP kích thước (n+1)×W, khởi tạo 0
    ch = [[0.0] * W for _ in range(n)]         # bảng CHOICE lưu số giờ đã chọn tại mỗi (i, j), dùng để truy vết

    for i, dev in enumerate(devices):          # duyệt từng thiết bị i (từ 0 đến n-1)
        opts = _opts(dev)                       # lấy tất cả lựa chọn giờ của thiết bị i
        for j in range(W):                     # duyệt từng mức ngân sách j (từ 0 đến W-1 ô)
            dp[i+1][j] = dp[i][j]             # mặc định: không dùng thiết bị i → kế thừa điểm từ hàng trên
            for cu, val, h in opts:            # thử từng lựa chọn h giờ của thiết bị i
                if j >= cu and dp[i][j-cu] + val > dp[i+1][j]:  # nếu đủ ngân sách VÀ điểm tốt hơn hiện tại
                    dp[i+1][j] = dp[i][j-cu] + val  # cập nhật điểm tốt nhất cho (i+1, j)
                    ch[i][j]   = h             # ghi nhớ: tại (i, j) chọn h giờ cho thiết bị i

    # Truy vết ngược để tìm lịch tối ưu
    bj = max(range(W), key=lambda j: dp[n][j]) # tìm vị trí j cho điểm cao nhất ở hàng cuối
    sc = []                                    # danh sách kết quả lịch sử dụng
    j  = bj                                    # bắt đầu truy vết từ j tốt nhất

    for i in range(n-1, -1, -1):              # truy vết ngược từ thiết bị n-1 về 0
        h = ch[i][j]                           # lấy số giờ đã chọn cho thiết bị i tại cột j
        if h > 0:                              # nếu thiết bị i được chọn (h > 0)
            cu = max(1, int(devices[i].kwh(h) / BUDGET_UNIT + 0.5))  # tính lại chi phí ô
            sc.append({                        # thêm vào lịch kết quả
                "device":  devices[i].to_dict(),    # thông tin thiết bị
                "hours":   h,                       # số giờ sử dụng được chọn
                "kwh":     round(devices[i].kwh(h), 3),  # kWh tiêu thụ
                "comfort": round(devices[i].priority * h, 1)  # điểm thoải mái
            })
            j -= cu                            # trừ đi chi phí của thiết bị i, lùi về cột trước đó

    no = max((len(_opts(d)) for d in devices), default=1)  # số lựa chọn tối đa của 1 thiết bị (dùng tính độ phức tạp)
    return {
        "schedule":       sorted(sc, key=lambda x: -x["comfort"]),  # sắp xếp theo điểm thoải mái giảm dần
        "total_comfort":  round(dp[n][bj], 1),          # tổng điểm thoải mái tối đa đạt được
        "total_kwh":      round(sum(s["kwh"] for s in sc), 3),  # tổng kWh đã dùng
        "algorithm":      "DP — Group Knapsack",         # tên thuật toán
        "complexity":     f"O(n×W×H) = O({n}×{W}×{no}) ≈ {n*W*no:,} ops"  # thông tin độ phức tạp thực tế
    }

def greedy_optimize(devices, budget_kwh):
    """
    Thuật toán Greedy — Sắp xếp theo tỉ lệ ưu_tiên/công_suất giảm dần.
    Độ phức tạp: O(n log n) — nhanh hơn DP nhưng không đảm bảo tối ưu toàn cục.
    """
    sc  = []                                    # danh sách kết quả lịch sử dụng
    rem = budget_kwh                            # ngân sách còn lại ban đầu = toàn bộ ngân sách

    for dev in sorted(devices, key=lambda d: d.priority / d.power_w, reverse=True):  # sắp xếp thiết bị theo ratio = ưu_tiên/công_suất giảm dần
        if rem < 1e-9:                          # nếu ngân sách đã hết (kiểm tra epsilon tránh lỗi float)
            break                               # dừng vòng lặp, không xét thêm thiết bị
        h = math.floor(                         # tính số giờ tối đa có thể dùng, làm tròn XUỐNG
            min(dev.max_daily_hours, rem / (dev.power_w / 1000))  # min(giới hạn thiết bị, giờ tối đa theo ngân sách)
            / HOUR_STEP                         # chia cho bước 0.5h
        ) * HOUR_STEP                           # nhân lại để có bội số của 0.5h
        if h >= HOUR_STEP:                      # chỉ thêm thiết bị nếu dùng được ít nhất 0.5h
            sc.append({                         # thêm vào lịch kết quả
                "device":  dev.to_dict(),       # thông tin thiết bị
                "hours":   h,                   # số giờ được phân bổ
                "kwh":     round(dev.kwh(h), 3),  # kWh tiêu thụ
                "comfort": round(dev.priority * h, 1)  # điểm thoải mái
            })
            rem -= dev.kwh(h)                   # trừ kWh đã dùng khỏi ngân sách còn lại

    return {
        "schedule":      sorted(sc, key=lambda x: -x["comfort"]),  # sắp xếp theo điểm thoải mái
        "total_comfort": round(sum(s["comfort"] for s in sc), 1),  # tổng điểm
        "total_kwh":     round(sum(s["kwh"] for s in sc), 3),      # tổng kWh
        "algorithm":     "Greedy — Ưu tiên/Công suất",             # tên thuật toán
        "complexity":    "O(n log n)"                               # độ phức tạp chỉ do bước sắp xếp
    }

def calc_evn(kwh):
    """Tính tiền điện theo biểu giá EVN 6 bậc lũy tiến (2024)."""
    tiers = [(50,1806),(50,1866),(100,2167),(100,2729),(100,3050),(9999,3151)]  # (giới hạn kWh mỗi bậc, đơn giá ₫/kWh)
    cost  = 0                                   # tổng tiền điện khởi tạo = 0
    rem   = kwh                                 # số kWh còn lại chưa tính tiền
    for lim, rate in tiers:                     # duyệt từng bậc từ thấp đến cao
        used   = min(rem, lim)                  # số kWh thuộc bậc này = min(còn lại, giới hạn bậc)
        cost  += used * rate                    # cộng tiền bậc này: kWh × đơn giá
        rem   -= used                           # trừ số kWh đã tính
        if rem <= 0:                            # nếu đã tính hết toàn bộ kWh
            break                               # thoát vòng lặp sớm
    return cost                                 # trả về tổng tiền điện (₫)

def smart_tips(devices, usage, config):
    """Phân tích nhật ký và đề xuất gợi ý tiết kiệm điện tự động."""
    dev_map   = {d.id: d for d in devices}     # dict tra cứu nhanh thiết bị theo ID
    tips      = []                              # danh sách gợi ý kết quả
    dates_used = set(e.date for e in usage)    # tập hợp các ngày đã có dữ liệu
    n_days    = max(len(dates_used), 1)        # số ngày đã ghi nhật ký (tối thiểu 1 để tránh chia 0)

    for dev in sorted(devices, key=lambda d: -d.power_w):  # duyệt thiết bị theo công suất giảm dần (ưu tiên thiết bị tốn điện)
        total_h = sum(e.hours for e in usage if e.device_id == dev.id)  # tổng số giờ đã dùng thiết bị này
        if not total_h:                        # bỏ qua thiết bị chưa có dữ liệu sử dụng
            continue
        avg_h = total_h / n_days              # trung bình số giờ dùng mỗi ngày
        if avg_h > dev.max_daily_hours * 0.75 and dev.power_w >= 200:  # nếu dùng >75% giới hạn VÀ công suất ≥200W
            save = dev.kwh(avg_h * 0.2)       # tính kWh tiết kiệm được nếu giảm 20% số giờ
            tips.append({
                "device":    dev.name,          # tên thiết bị cần chú ý
                "power":     dev.power_w,       # công suất (W)
                "msg": f"Giảm 20% → tiết kiệm ~{save:.2f} kWh/ngày (~{save*30*config.electricity_rate:,.0f} VND/tháng)",  # nội dung gợi ý
                "save_kwh":  round(save, 3),    # lượng kWh tiết kiệm mỗi ngày
                "level":     "danger" if dev.power_w >= 500 else "warning"  # mức độ cảnh báo: nguy hiểm nếu ≥500W
            })
        if len(tips) >= 4:                     # giới hạn tối đa 4 gợi ý để không làm loãng UI
            break
    return tips                                # trả về danh sách gợi ý

# ══════════════════════════════════════════════════════════════
# FLASK ROUTES — Định nghĩa các API endpoint
# ══════════════════════════════════════════════════════════════

app = Flask(__name__)                          # tạo ứng dụng Flask, __name__ giúp Flask tìm đúng thư mục templates/static

@app.route("/")                               # route trang chính
def index():
    return render_template("index.html")       # render file templates/index.html và trả về HTML

@app.route("/flowchart")                      # route trang flowchart
def flowchart():
    return render_template("flowchart.html")  # render file templates/flowchart.html

# ── Devices API ───────────────────────────────────────────────
@app.route("/api/devices")                    # GET /api/devices — lấy danh sách thiết bị
def r_devices():
    return jsonify([d.to_dict() for d in load_devices()])  # đọc file JSON, chuyển thành list dict, trả về JSON

@app.route("/api/devices", methods=["POST"]) # POST /api/devices — thêm thiết bị mới
def r_add_device():
    d    = request.json                        # đọc body JSON từ request
    devs = load_devices()                      # tải danh sách thiết bị hiện tại
    if any(x.id == d["id"] for x in devs):   # kiểm tra ID đã tồn tại chưa
        return jsonify({"error": "ID đã tồn tại"}), 400  # trả về lỗi 400 nếu trùng ID
    devs.append(Device(**d))                   # thêm thiết bị mới vào danh sách
    save_devices(devs)                         # lưu danh sách mới vào file
    return jsonify({"ok": True})              # trả về thành công

@app.route("/api/devices/<dev_id>", methods=["DELETE"])  # DELETE /api/devices/:id — xóa thiết bị
def r_del_device(dev_id):
    save_devices([d for d in load_devices() if d.id != dev_id])  # lọc bỏ thiết bị có ID trùng, lưu lại
    return jsonify({"ok": True})

@app.route("/api/devices/reset", methods=["POST"])  # POST /api/devices/reset — khôi phục mặc định
def r_reset_devices():
    save_devices(list(DEFAULT_DEVICES))        # ghi đè bằng danh sách thiết bị mặc định
    return jsonify({"ok": True})

# ── Usage API ─────────────────────────────────────────────────
@app.route("/api/usage")                      # GET /api/usage — lấy toàn bộ nhật ký
def r_usage():
    return jsonify([e.to_dict() for e in load_usage()])  # trả về tất cả nhật ký dạng JSON

@app.route("/api/usage", methods=["POST"])    # POST /api/usage — lưu/cập nhật nhật ký 1 thiết bị 1 ngày
def r_save_usage():
    d = request.json                           # đọc body JSON
    u = [e for e in load_usage()              # lọc bỏ entry cũ của thiết bị này trong ngày này (nếu có)
         if not (e.date == d["date"] and e.device_id == d["device_id"])]
    if float(d.get("hours", 0)) > 0:         # chỉ thêm nếu số giờ > 0 (không lưu 0h)
        u.append(UsageEntry(d["device_id"], d["date"], float(d["hours"])))  # thêm entry mới
    save_usage(u)                              # lưu danh sách đã cập nhật
    return jsonify({"ok": True})

@app.route("/api/usage/<log_date>", methods=["DELETE"])  # DELETE /api/usage/:date — xóa toàn bộ ngày
def r_del_day(log_date):
    save_usage([e for e in load_usage() if e.date != log_date])  # lọc bỏ mọi entry của ngày đó
    return jsonify({"ok": True})

# ── Config API ────────────────────────────────────────────────
@app.route("/api/config")                     # GET /api/config — lấy cài đặt hiện tại
def r_config():
    return jsonify(load_config().to_dict())   # đọc config và trả về JSON

@app.route("/api/config", methods=["POST"])   # POST /api/config — lưu cài đặt mới
def r_save_config():
    d = request.json                           # đọc body JSON
    save_config(Config(float(d["daily_budget_kwh"]), float(d["electricity_rate"]), d["peak_hours"]))  # tạo Config mới và lưu
    return jsonify({"ok": True})

# ── Stats API ─────────────────────────────────────────────────
@app.route("/api/stats")                      # GET /api/stats — thống kê tổng hợp cho Dashboard
def r_stats():
    devs    = load_devices()                   # tải danh sách thiết bị
    usage   = load_usage()                     # tải nhật ký sử dụng
    cfg     = load_config()                    # tải cài đặt
    dev_map = {d.id: d for d in devs}         # dict tra cứu nhanh theo ID
    today   = date.today()                     # ngày hôm nay

    daily = []                                 # dữ liệu 14 ngày gần nhất
    for i in range(13, -1, -1):               # lặp từ 13 ngày trước đến hôm nay
        dd  = (today - timedelta(days=i)).isoformat()  # chuỗi ngày "YYYY-MM-DD"
        kwh = sum(dev_map[e.device_id].kwh(e.hours)   # tổng kWh của ngày dd
                  for e in usage if e.date == dd and e.device_id in dev_map)
        daily.append({"date": dd, "kwh": round(kwh,3), "cost": round(kwh*cfg.electricity_rate)})  # thêm vào kết quả

    by_dev = []                                # thống kê theo từng thiết bị
    for d in devs:
        h = sum(e.hours for e in usage if e.device_id == d.id)  # tổng giờ đã dùng thiết bị d
        if h:                                  # chỉ thêm thiết bị đã có sử dụng
            kwh = round(d.kwh(h), 2)          # tổng kWh của thiết bị này
            by_dev.append({"name": d.name, "kwh": kwh, "hours": h,
                           "cost": round(kwh*cfg.electricity_rate), "category": d.category})
    by_dev.sort(key=lambda x: -x["kwh"])      # sắp xếp theo kWh giảm dần (thiết bị tốn điện nhất lên đầu)

    dates_used = sorted(set(e.date for e in usage))  # tập hợp các ngày đã có dữ liệu
    total_kwh  = sum(dev_map[e.device_id].kwh(e.hours)  # tổng kWh toàn bộ lịch sử
                     for e in usage if e.device_id in dev_map)
    avg        = round(total_kwh / len(dates_used), 3) if dates_used else 0  # trung bình kWh/ngày
    today_kwh  = sum(dev_map[e.device_id].kwh(e.hours)  # tổng kWh hôm nay
                     for e in usage if e.date == today.isoformat() and e.device_id in dev_map)

    return jsonify({
        "daily":       daily,                  # dữ liệu 14 ngày cho biểu đồ đường
        "by_device":   by_dev,                 # dữ liệu theo thiết bị cho biểu đồ donut
        "avg_kwh":     avg,                    # trung bình kWh/ngày
        "monthly_kwh": round(avg*30, 1),       # ước tính kWh/tháng = avg × 30
        "est_evn":     round(calc_evn(avg*30)),# ước tính tiền điện EVN/tháng
        "today_kwh":   round(today_kwh, 3),    # kWh đã dùng hôm nay
        "budget":      cfg.daily_budget_kwh,   # ngân sách/ngày từ cài đặt
        "budget_rem":  round(max(0, cfg.daily_budget_kwh - today_kwh), 3),  # ngân sách còn lại hôm nay
        "tips":        smart_tips(devs, usage, cfg),  # gợi ý tiết kiệm điện
        "n_days":      len(dates_used)          # số ngày đã có dữ liệu
    })

# ── Optimize API ──────────────────────────────────────────────
@app.route("/api/optimize", methods=["POST"]) # POST /api/optimize — chạy so sánh DP vs Greedy
def r_optimize():
    budget = float(request.json.get("budget_kwh", 2.0))  # đọc ngân sách từ body, mặc định 2.0 kWh
    devs   = load_devices()                    # tải danh sách thiết bị
    cfg    = load_config()                     # tải cài đặt

    dp = dp_optimize(devs, budget)             # chạy thuật toán DP Group Knapsack
    gr = greedy_optimize(devs, budget)         # chạy thuật toán Greedy

    for r in (dp, gr):                         # với mỗi kết quả (DP và Greedy)
        r["daily_cost"]   = round(r["total_kwh"] * cfg.electricity_rate)      # chi phí/ngày (₫)
        r["monthly_cost"] = round(r["total_kwh"] * 30 * cfg.electricity_rate) # chi phí/tháng (₫)

    # Tạo phản ví dụ minh họa Greedy không tối ưu với 2 thiết bị cụ thể
    loa = Device("loa_d", "Loa Bluetooth", 200, 3, 1.0, "entertainment")  # Loa 200W ưu tiên 3, ratio=3/200=0.015
    dh  = Device("dh_d",  "Điều hòa nhỏ", 300, 4, 1.0, "cooling")        # Điều hòa 300W ưu tiên 4, ratio=4/300=0.013
    ce_dp = dp_optimize([loa, dh], 0.30)      # DP với ngân sách 0.30 kWh → chọn điều hòa (4 điểm)
    ce_gr = greedy_optimize([loa, dh], 0.30)  # Greedy → chọn loa trước (ratio cao hơn) → chỉ 3 điểm

    return jsonify({
        "dp":             dp,                  # kết quả DP
        "greedy":         gr,                  # kết quả Greedy
        "budget":         budget,              # ngân sách đã dùng
        "counterexample": {                    # phản ví dụ DP thắng Greedy
            "dp":      ce_dp,
            "greedy":  ce_gr,
            "dp_wins": ce_dp["total_comfort"] > ce_gr["total_comfort"] + 1e-6  # True nếu DP thắng
        }
    })

# ── Peak Schedule API ─────────────────────────────────────────
@app.route("/api/peak", methods=["POST"])     # POST /api/peak — tạo lịch tránh giờ cao điểm
def r_peak():
    budget   = float(request.json.get("budget_kwh", 2.0))  # ngân sách từ body
    devs     = load_devices()                  # tải thiết bị
    cfg      = load_config()                   # tải cài đặt (để biết giờ cao điểm)
    dp       = dp_optimize(devs, budget)       # chạy DP để có lịch tối ưu trước
    peak_set = set(cfg.peak_hours)             # tập hợp các giờ cao điểm để tra cứu nhanh O(1)
    off      = [h for h in range(24) if h not in peak_set]  # danh sách giờ thấp điểm
    pa       = sorted(cfg.peak_hours)         # danh sách giờ cao điểm đã sắp xếp

    result = {}                                # kết quả lịch cho từng thiết bị
    for item in dp["schedule"]:               # duyệt từng thiết bị trong lịch DP
        did  = item["device"]["id"]            # ID thiết bị
        left = item["hours"]                   # số giờ cần phân bổ
        slots = []                             # danh sách slot giờ cụ thể
        pool = off if item["device"]["power_w"] >= 500 else (off + pa)  # thiết bị ≥500W chỉ dùng giờ thấp điểm
        for h in pool:                         # duyệt từng giờ trong pool
            if left < 1e-9: break              # đã phân bổ đủ giờ, dừng lại
            used = min(1.0, left)              # phân bổ tối đa 1h mỗi slot
            slots.append({"start": h, "dur": used})  # thêm slot
            left -= used                       # trừ đi giờ đã phân bổ
        result[did] = {**item, "slots": slots} # gộp thông tin thiết bị với danh sách slots

    return jsonify({"schedule": result, "peak_hours": cfg.peak_hours})  # trả về lịch và giờ cao điểm

# ── Heatmap API ───────────────────────────────────────────────
@app.route("/api/heatmap")                    # GET /api/heatmap — dữ liệu 30 ngày cho heatmap
def r_heatmap():
    devs    = load_devices()                   # tải thiết bị
    usage   = load_usage()                     # tải nhật ký
    dev_map = {d.id: d for d in devs}         # dict tra cứu nhanh
    today   = date.today()                     # ngày hôm nay
    days    = []                               # dữ liệu 30 ngày
    for i in range(29, -1, -1):              # từ 29 ngày trước đến hôm nay
        dd  = (today - timedelta(days=i)).isoformat()  # chuỗi ngày
        kwh = sum(dev_map[e.device_id].kwh(e.hours)   # tổng kWh ngày đó
                  for e in usage if e.date == dd and e.device_id in dev_map)
        days.append({"date": dd, "kwh": round(kwh, 3)})  # thêm vào kết quả
    mx = max((d["kwh"] for d in days), default=1)   # giá trị kWh cao nhất để chuẩn hóa màu heatmap
    return jsonify({"days": days, "max_kwh": round(mx, 3)})  # trả về dữ liệu và max để frontend tô màu

# ── Forecast API ──────────────────────────────────────────────
@app.route("/api/forecast")                   # GET /api/forecast — dự báo 6 tháng tới
def r_forecast():
    devs       = load_devices()               # tải thiết bị
    usage      = load_usage()                 # tải nhật ký
    cfg        = load_config()                # tải cài đặt
    dev_map    = {d.id: d for d in devs}     # dict tra cứu
    dates_used = sorted(set(e.date for e in usage))  # các ngày đã có dữ liệu
    if not dates_used:                        # nếu chưa có dữ liệu nào
        return jsonify({"months": [], "avg_daily_kwh": 0, "saving": 0})  # trả về rỗng

    total     = sum(dev_map[e.device_id].kwh(e.hours)  # tổng kWh toàn lịch sử
                    for e in usage if e.device_id in dev_map)
    avg       = total / len(dates_used)       # trung bình kWh/ngày từ dữ liệu thực tế
    monthly   = avg * 30                      # ước tính kWh/tháng

    months    = [{"label": f"Tháng +{i+1}", "kwh": round(monthly, 1),  # dự báo 6 tháng tới
                  "evn": round(calc_evn(monthly))} for i in range(6)]

    dp        = dp_optimize(devs, cfg.daily_budget_kwh)   # chạy DP để tính kịch bản tối ưu
    opt_monthly = dp["total_kwh"] * 30        # kWh/tháng nếu dùng theo lịch DP tối ưu

    return jsonify({
        "months":          months,             # dữ liệu dự báo 6 tháng
        "avg_daily_kwh":   round(avg, 3),     # trung bình kWh/ngày hiện tại
        "monthly_kwh":     round(monthly, 1), # kWh/tháng hiện tại
        "evn":             round(calc_evn(monthly)),      # tiền điện EVN hiện tại
        "opt_monthly_kwh": round(opt_monthly, 1),         # kWh/tháng nếu dùng lịch DP
        "opt_evn":         round(calc_evn(opt_monthly)),  # tiền điện EVN nếu dùng lịch DP
        "saving":          round(calc_evn(monthly) - calc_evn(opt_monthly))  # số tiền tiết kiệm được
    })

# ── EVN Calculator API ────────────────────────────────────────
@app.route("/api/evn", methods=["POST"])      # POST /api/evn — tính chi tiết tiền điện EVN
def r_evn():
    kwh   = float(request.json.get("kwh", 0))  # số kWh từ body, mặc định 0
    tiers = [(50,1806),(50,1866),(100,2167),(100,2729),(100,3050),(9999,3151)]  # biểu giá 6 bậc EVN
    bk    = []                                  # breakdown: chi tiết từng bậc
    rem   = kwh                                 # kWh còn lại chưa tính
    for i, (lim, rate) in enumerate(tiers):    # duyệt từng bậc
        used = min(rem, lim)                    # kWh thuộc bậc này
        if used > 0:                            # chỉ thêm bậc nếu có sử dụng
            bk.append({"bac": i+1, "kwh": round(used,2),  # thứ tự bậc và số kWh
                        "rate": rate, "cost": round(used*rate)})  # đơn giá và thành tiền
        rem -= used                             # trừ đi kWh đã tính
        if rem <= 0: break                      # thoát nếu đã tính hết
    return jsonify({"kwh": kwh, "total": round(calc_evn(kwh)), "breakdown": bk})  # trả về tổng và chi tiết

# ══════════════════════════════════════════════════════════════
# ENTRY POINT — Khởi động server
# ══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    os.makedirs("templates", exist_ok=True)    # đảm bảo thư mục templates tồn tại
    print("\n  http://localhost:5000\n")        # in địa chỉ truy cập ra terminal
    app.run(debug=False, host="0.0.0.0", port=5000)  # chạy server: debug=False (production), host=0.0.0.0 (cho phép truy cập từ mạng LAN), port=5000
