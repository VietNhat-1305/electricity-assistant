from dataclasses import dataclass, field  # Import dataclass để tạo lớp dữ liệu đơn giản
from typing import List  # Import kiểu danh sách


@dataclass  # Decorator tự động sinh __init__, __repr__, __eq__ cho lớp
class Device:  # Lớp đại diện một thiết bị điện
    id: str  # Mã định danh duy nhất của thiết bị (vd: "ac", "fan")
    name: str  # Tên hiển thị thân thiện (vd: "Điều hòa")
    power_w: int  # Công suất tiêu thụ tính bằng Watt
    priority: int  # Mức ưu tiên sử dụng từ 1 (thấp) đến 5 (không thể thiếu)
    max_daily_hours: float  # Số giờ tối đa có thể dùng mỗi ngày
    category: str  # Nhóm thiết bị: cooling / lighting / computing / heating / cooking / cleaning / entertainment

    def kwh(self, hours: float) -> float:  # Hàm tính điện năng tiêu thụ
        """Điện năng tiêu thụ (kWh) khi dùng h giờ."""
        return self.power_w * hours / 1000  # Công thức: W × h / 1000 = kWh


@dataclass  # Decorator tự động sinh các phương thức magic
class UsageEntry:  # Lớp ghi nhận một lần sử dụng thiết bị
    device_id: str  # ID thiết bị được sử dụng (khóa ngoại trỏ tới Device.id)
    date: str  # Ngày sử dụng theo định dạng YYYY-MM-DD
    hours: float  # Số giờ đã sử dụng trong ngày đó
    note: str = ""  # Ghi chú tùy chọn (mặc định để trống)


@dataclass  # Decorator tạo lớp cấu hình ứng dụng
class Config:  # Lớp lưu trữ các cài đặt toàn cục của ứng dụng
    daily_budget_kwh: float = 2.0  # Ngân sách điện mặc định mỗi ngày tính bằng kWh
    electricity_rate: float = 3500.0  # Giá điện mặc định tính bằng VND trên mỗi kWh
    peak_hours: List[int] = field(  # Danh sách các giờ cao điểm (mặc định 17h–21h)
        default_factory=lambda: [17, 18, 19, 20, 21]  # Lambda tránh dùng chung list giữa các instance
    )  # Giờ cao điểm điển hình theo khung giờ EVN Việt Nam


# Danh sách thiết bị điện mặc định phổ biến trong phòng trọ sinh viên
DEFAULT_DEVICES: List[Device] = [  # Khởi tạo 10 thiết bị tiêu biểu
    Device("ac",      "Điều hòa",          900,  4,  8.0, "cooling"),      # Điều hòa 900W, ưu tiên 4, dùng tối đa 8h/ngày
    Device("fan",     "Quạt điện",           55,  5, 12.0, "cooling"),      # Quạt điện 55W, ưu tiên cao nhất, dùng 12h/ngày
    Device("light",   "Đèn LED",             15,  5, 12.0, "lighting"),     # Đèn LED 15W, thiết yếu, dùng 12h/ngày
    Device("laptop",  "Laptop",              65,  5, 10.0, "computing"),    # Laptop 65W, thiết yếu, dùng 10h/ngày
    Device("phone",   "Sạc điện thoại",      10,  4,  4.0, "computing"),   # Sạc điện thoại 10W, ưu tiên 4, sạc 4h/ngày
    Device("heater",  "Bình nước nóng",    2000,  3,  1.0, "heating"),      # Bình nước nóng 2000W, dùng 1h/ngày
    Device("tv",      "Tivi",               100,  2,  4.0, "entertainment"), # Tivi 100W, ưu tiên thấp, xem 4h/ngày
    Device("rice",    "Nồi cơm điện",       700,  5,  1.0, "cooking"),      # Nồi cơm 700W, thiết yếu, nấu 1h/ngày
    Device("fridge",  "Tủ lạnh mini",        80,  3, 24.0, "cooling"),      # Tủ lạnh mini 80W, hoạt động liên tục 24h
    Device("washing", "Máy giặt",           500,  4,  1.0, "cleaning"),     # Máy giặt 500W, ưu tiên 4, giặt 1h/ngày
]
