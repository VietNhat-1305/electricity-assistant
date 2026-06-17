from dataclasses import dataclass, field
from typing import List


@dataclass
class Device:
    id: str
    name: str
    power_w: int            # Công suất (Watt)
    priority: int           # Mức ưu tiên 1-5 (5 = không thể thiếu)
    max_daily_hours: float  # Giờ tối đa sử dụng / ngày
    category: str           # Loại thiết bị

    def kwh(self, hours: float) -> float:
        """Điện năng tiêu thụ (kWh) khi dùng h giờ."""
        return self.power_w * hours / 1000


@dataclass
class UsageEntry:
    device_id: str
    date: str    # YYYY-MM-DD
    hours: float
    note: str = ""


@dataclass
class Config:
    daily_budget_kwh: float = 2.0         # Ngân sách điện / ngày (kWh)
    electricity_rate: float = 3500.0       # Giá điện (VND / kWh)
    peak_hours: List[int] = field(
        default_factory=lambda: [17, 18, 19, 20, 21]
    )  # Giờ cao điểm điển hình (17h–21h)


# Thiết bị mặc định phổ biến trong phòng trọ sinh viên
DEFAULT_DEVICES: List[Device] = [
    Device("ac",      "Điều hòa",          900,  4,  8.0, "cooling"),
    Device("fan",     "Quạt điện",           55,  5, 12.0, "cooling"),
    Device("light",   "Đèn LED",             15,  5, 12.0, "lighting"),
    Device("laptop",  "Laptop",              65,  5, 10.0, "computing"),
    Device("phone",   "Sạc điện thoại",      10,  4,  4.0, "computing"),
    Device("heater",  "Bình nước nóng",    2000,  3,  1.0, "heating"),
    Device("tv",      "Tivi",               100,  2,  4.0, "entertainment"),
    Device("rice",    "Nồi cơm điện",       700,  5,  1.0, "cooking"),
    Device("fridge",  "Tủ lạnh mini",        80,  3, 24.0, "cooling"),
    Device("washing", "Máy giặt",           500,  4,  1.0, "cleaning"),
]
