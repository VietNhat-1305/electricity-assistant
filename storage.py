import json  # Thư viện đọc/ghi dữ liệu định dạng JSON
import os  # Thư viện xử lý đường dẫn và thao tác hệ thống tệp
from typing import List  # Import kiểu danh sách cho type hint

from models import Config, DEFAULT_DEVICES, Device, UsageEntry  # Import các lớp dữ liệu từ models.py

# Đường dẫn thư mục chứa các file JSON dữ liệu (thư mục "data" cùng cấp với file này)
_DIR     = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")  # Thư mục lưu trữ data/
_DEVICES = os.path.join(_DIR, "devices.json")  # Đường dẫn file lưu danh sách thiết bị
_USAGE   = os.path.join(_DIR, "usage.json")  # Đường dẫn file lưu nhật ký sử dụng
_CONFIG  = os.path.join(_DIR, "config.json")  # Đường dẫn file lưu cấu hình ứng dụng


def _ensure() -> None:  # Hàm nội bộ đảm bảo thư mục data tồn tại
    os.makedirs(_DIR, exist_ok=True)  # Tạo thư mục data nếu chưa có, bỏ qua nếu đã tồn tại


# ── Devices ───────────────────────────────────────────────────

def load_devices() -> List[Device]:  # Hàm đọc danh sách thiết bị từ file JSON
    _ensure()  # Đảm bảo thư mục data tồn tại trước khi đọc
    if not os.path.exists(_DEVICES):  # Nếu file devices.json chưa tồn tại
        save_devices(list(DEFAULT_DEVICES))  # Tạo file mới với danh sách thiết bị mặc định
        return list(DEFAULT_DEVICES)  # Trả về bản sao danh sách mặc định
    with open(_DEVICES, encoding="utf-8") as f:  # Mở file JSON với encoding UTF-8
        return [Device(**d) for d in json.load(f)]  # Đọc JSON và chuyển mỗi dict thành đối tượng Device


def save_devices(devices: List[Device]) -> None:  # Hàm ghi danh sách thiết bị ra file JSON
    _ensure()  # Đảm bảo thư mục data tồn tại trước khi ghi
    with open(_DEVICES, "w", encoding="utf-8") as f:  # Mở file để ghi với encoding UTF-8
        json.dump([d.__dict__ for d in devices], f, ensure_ascii=False, indent=2)  # Chuyển từng Device thành dict rồi ghi JSON có định dạng


# ── Usage log ─────────────────────────────────────────────────

def load_usage() -> List[UsageEntry]:  # Hàm đọc nhật ký sử dụng điện từ file JSON
    _ensure()  # Đảm bảo thư mục data tồn tại
    if not os.path.exists(_USAGE):  # Nếu file usage.json chưa tồn tại
        return []  # Trả về danh sách rỗng (chưa có dữ liệu)
    with open(_USAGE, encoding="utf-8") as f:  # Mở file JSON nhật ký
        return [UsageEntry(**e) for e in json.load(f)]  # Chuyển mỗi dict thành đối tượng UsageEntry


def save_usage(entries: List[UsageEntry]) -> None:  # Hàm ghi nhật ký sử dụng ra file JSON
    _ensure()  # Đảm bảo thư mục data tồn tại
    with open(_USAGE, "w", encoding="utf-8") as f:  # Mở file để ghi
        json.dump([e.__dict__ for e in entries], f, ensure_ascii=False, indent=2)  # Chuyển từng UsageEntry thành dict và ghi JSON


# ── Config ────────────────────────────────────────────────────

def load_config() -> Config:  # Hàm đọc cấu hình ứng dụng từ file JSON
    _ensure()  # Đảm bảo thư mục data tồn tại
    if not os.path.exists(_CONFIG):  # Nếu file config.json chưa tồn tại
        return Config()  # Trả về cấu hình mặc định (2 kWh/ngày, 3500 VND/kWh)
    with open(_CONFIG, encoding="utf-8") as f:  # Mở file cấu hình
        return Config(**json.load(f))  # Đọc JSON và khởi tạo đối tượng Config từ các giá trị đã lưu


def save_config(cfg: Config) -> None:  # Hàm ghi cấu hình ra file JSON
    _ensure()  # Đảm bảo thư mục data tồn tại
    with open(_CONFIG, "w", encoding="utf-8") as f:  # Mở file để ghi
        json.dump(cfg.__dict__, f, ensure_ascii=False, indent=2)  # Ghi toàn bộ thuộc tính Config ra JSON có định dạng
