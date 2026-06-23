/* ════════════════════════════════════════════════════════════════
   API Layer — Tầng gọi API: bọc toàn bộ lệnh fetch đến Flask
   ════════════════════════════════════════════════════════════════ */

const API = {                                  // object chứa tất cả hàm gọi API, dùng chung toàn app

  /* ─── Quản lý Thiết bị ──────────────────────────────────── */
  async getDevices() {                         // hàm bất đồng bộ: lấy danh sách tất cả thiết bị
    const r = await fetch('/api/devices');     // gửi GET request đến /api/devices
    if (!r.ok) throw new Error('Không thể tải danh sách thiết bị');  // ném lỗi nếu server trả về status != 2xx
    return r.json();                           // parse body JSON và trả về (Promise<Array>)
  },

  async addDevice(d) {                         // hàm thêm thiết bị mới, d là object thiết bị
    const r = await fetch('/api/devices', {    // gửi POST request đến /api/devices
      method: 'POST',                          // phương thức HTTP POST
      headers: { 'Content-Type': 'application/json' },  // báo server body là JSON
      body: JSON.stringify(d)                  // chuyển object thành chuỗi JSON để gửi
    });
    const data = await r.json();               // parse phản hồi JSON từ server
    if (!r.ok) throw new Error(data.error || 'Lỗi thêm thiết bị');  // nếu lỗi, ném thông báo từ server
    return data;                               // trả về { ok: true } nếu thành công
  },

  async deleteDevice(id) {                     // hàm xóa thiết bị theo ID
    const r = await fetch(`/api/devices/${id}`, { method: 'DELETE' });  // gửi DELETE request với ID trong URL
    if (!r.ok) throw new Error('Lỗi xóa thiết bị');  // ném lỗi nếu thất bại
    return r.json();                           // trả về { ok: true }
  },

  async resetDevices() {                       // hàm khôi phục danh sách thiết bị về mặc định
    const r = await fetch('/api/devices/reset', { method: 'POST' });  // gọi POST /api/devices/reset
    if (!r.ok) throw new Error('Lỗi reset thiết bị');  // ném lỗi nếu thất bại
    return r.json();                           // trả về { ok: true }
  },

  /* ─── Nhật ký Sử dụng ───────────────────────────────────── */
  async getUsage() {                           // hàm lấy toàn bộ nhật ký sử dụng
    const r = await fetch('/api/usage');       // gửi GET /api/usage
    if (!r.ok) throw new Error('Không thể tải nhật ký');  // ném lỗi nếu thất bại
    return r.json();                           // trả về mảng các nhật ký
  },

  async saveUsage(device_id, date, hours) {   // hàm lưu số giờ sử dụng của 1 thiết bị trong 1 ngày
    const r = await fetch('/api/usage', {     // gửi POST /api/usage
      method: 'POST',                          // phương thức POST
      headers: { 'Content-Type': 'application/json' },  // body là JSON
      body: JSON.stringify({ device_id, date, hours })  // dữ liệu: ID thiết bị, ngày, số giờ
    });
    if (!r.ok) throw new Error('Lỗi lưu nhật ký');  // ném lỗi nếu thất bại
    return r.json();                           // trả về { ok: true }
  },

  async deleteDay(date) {                      // hàm xóa toàn bộ nhật ký của 1 ngày
    const r = await fetch(`/api/usage/${date}`, { method: 'DELETE' });  // DELETE /api/usage/:date
    if (!r.ok) throw new Error('Lỗi xóa ngày');  // ném lỗi nếu thất bại
    return r.json();                           // trả về { ok: true }
  },

  /* ─── Cài đặt ────────────────────────────────────────────── */
  async getConfig() {                          // hàm lấy cài đặt hiện tại (ngân sách, giá điện, giờ cao điểm)
    const r = await fetch('/api/config');      // gửi GET /api/config
    if (!r.ok) throw new Error('Lỗi tải cài đặt');  // ném lỗi nếu thất bại
    return r.json();                           // trả về object config
  },

  async saveConfig(cfg) {                      // hàm lưu cài đặt mới, cfg là object cài đặt
    const r = await fetch('/api/config', {    // gửi POST /api/config
      method: 'POST',                          // phương thức POST
      headers: { 'Content-Type': 'application/json' },  // body là JSON
      body: JSON.stringify(cfg)               // chuyển object cfg thành JSON
    });
    if (!r.ok) throw new Error('Lỗi lưu cài đặt');  // ném lỗi nếu thất bại
    return r.json();                           // trả về { ok: true }
  },

  /* ─── Thống kê ───────────────────────────────────────────── */
  async getStats() {                           // hàm lấy thống kê tổng hợp cho Dashboard
    const r = await fetch('/api/stats');       // gửi GET /api/stats
    if (!r.ok) throw new Error('Lỗi tải thống kê');  // ném lỗi nếu thất bại
    return r.json();                           // trả về object thống kê (daily, by_device, avg_kwh, ...)
  },

  /* ─── Tối ưu hóa ─────────────────────────────────────────── */
  async optimize(budget_kwh) {                 // hàm chạy DP và Greedy, truyền ngân sách kWh
    const r = await fetch('/api/optimize', {  // gửi POST /api/optimize
      method: 'POST',                          // phương thức POST
      headers: { 'Content-Type': 'application/json' },  // body là JSON
      body: JSON.stringify({ budget_kwh })     // gửi ngân sách lên server
    });
    if (!r.ok) throw new Error('Lỗi tối ưu hóa');  // ném lỗi nếu thất bại
    return r.json();                           // trả về { dp, greedy, counterexample }
  },

  /* ─── Lịch cao điểm ──────────────────────────────────────── */
  async getPeak(budget_kwh) {                  // hàm tạo lịch tránh giờ cao điểm
    const r = await fetch('/api/peak', {      // gửi POST /api/peak
      method: 'POST',                          // phương thức POST
      headers: { 'Content-Type': 'application/json' },  // body là JSON
      body: JSON.stringify({ budget_kwh })     // gửi ngân sách
    });
    if (!r.ok) throw new Error('Lỗi lấy lịch cao điểm');  // ném lỗi nếu thất bại
    return r.json();                           // trả về { schedule, peak_hours }
  },

  /* ─── Heatmap ────────────────────────────────────────────── */
  async getHeatmap() {                         // hàm lấy dữ liệu 30 ngày cho heatmap màu sắc
    const r = await fetch('/api/heatmap');     // gửi GET /api/heatmap
    if (!r.ok) throw new Error('Lỗi tải heatmap');  // ném lỗi nếu thất bại
    return r.json();                           // trả về { days: [...], max_kwh }
  },

  /* ─── Dự báo ─────────────────────────────────────────────── */
  async getForecast() {                        // hàm lấy dự báo chi phí 6 tháng tới
    const r = await fetch('/api/forecast');    // gửi GET /api/forecast
    if (!r.ok) throw new Error('Lỗi tải dự báo');  // ném lỗi nếu thất bại
    return r.json();                           // trả về { months, avg_daily_kwh, saving, ... }
  },

  /* ─── Tính tiền điện EVN ──────────────────────────────────── */
  async calcEvn(kwh) {                         // hàm tính tiền điện EVN 6 bậc, truyền vào số kWh
    const r = await fetch('/api/evn', {       // gửi POST /api/evn
      method: 'POST',                          // phương thức POST
      headers: { 'Content-Type': 'application/json' },  // body là JSON
      body: JSON.stringify({ kwh })            // gửi số kWh cần tính
    });
    if (!r.ok) throw new Error('Lỗi tính EVN');  // ném lỗi nếu thất bại
    return r.json();                           // trả về { total, breakdown: [...] }
  }
};

/* ─── Metadata danh mục thiết bị ──────────────────────────────── */
const CATEGORY_META = {                        // object tra cứu icon và màu theo danh mục thiết bị
  cooling:       { icon: '❄️',  color: '#38bdf8', label: 'Làm mát' },       // điều hòa, quạt, tủ lạnh
  lighting:      { icon: '💡',  color: '#fbbf24', label: 'Chiếu sáng' },    // đèn LED
  computing:     { icon: '💻',  color: '#a78bfa', label: 'Máy tính' },      // laptop, điện thoại
  heating:       { icon: '🔥',  color: '#f87171', label: 'Nhiệt' },         // bình nước nóng
  entertainment: { icon: '📺',  color: '#fb923c', label: 'Giải trí' },      // tivi, loa
  cooking:       { icon: '🍚',  color: '#4ade80', label: 'Nấu ăn' },        // nồi cơm, lò vi sóng
  cleaning:      { icon: '🌊',  color: '#67e8f9', label: 'Vệ sinh' },       // máy giặt
  other:         { icon: '🔌',  color: '#94a3b8', label: 'Khác' },          // thiết bị không thuộc nhóm trên
};

const DEVICE_ICONS = {                         // object tra cứu icon theo ID thiết bị mặc định
  ac: '❄️', fan: '🌬️', light: '💡', laptop: '💻', phone: '📱',
  heater: '🚿', tv: '📺', rice: '🍚', fridge: '🧊', washing: '🌊'
};

function deviceIcon(dev) {                     // hàm lấy icon phù hợp nhất cho thiết bị
  return DEVICE_ICONS[dev.id]                  // ưu tiên 1: icon theo ID (chính xác nhất)
    || CATEGORY_META[dev.category]?.icon       // ưu tiên 2: icon theo danh mục
    || '🔌';                                   // ưu tiên 3: icon mặc định
}

function catColor(cat) {                       // hàm lấy màu hex của danh mục
  return CATEGORY_META[cat]?.color || '#94a3b8';  // trả về màu danh mục hoặc màu xám mặc định
}

function catLabel(cat) {                       // hàm lấy nhãn tiếng Việt của danh mục
  return CATEGORY_META[cat]?.label || 'Khác'; // trả về nhãn hoặc 'Khác' nếu không tìm thấy
}

/* ─── Hàm định dạng hiển thị ──────────────────────────────────── */
const fmt = {                                  // object chứa các hàm format số liệu ra chuỗi
  vnd:   n => n >= 1000                        // hàm format tiền VND: nếu ≥1000 thì hiện dạng "Xk ₫"
              ? `${(n/1000).toFixed(0)}k ₫`    // ví dụ: 35000 → "35k ₫"
              : `${Math.round(n)} ₫`,          // ví dụ: 500 → "500 ₫"

  vndFull: n => new Intl.NumberFormat('vi-VN').format(Math.round(n)) + ' ₫',  // format đầy đủ: 35.000 ₫

  kwh:   n => `${(+n).toFixed(3)} kWh`,       // format kWh 3 chữ số thập phân: "2.350 kWh"

  kwhS:  n => `${(+n).toFixed(2)} kWh`,       // format kWh ngắn 2 chữ số: "2.35 kWh"

  hours: n => n >= 1                           // format giờ: nếu ≥1h thì hiện "Xh", dưới 1h hiện phút
              ? `${n}h`
              : `${(n*60).toFixed(0)}p`,

  pct:   n => `${(+n).toFixed(1)}%`,          // format phần trăm 1 chữ số thập phân

  date:  d => {                                // format ngày từ "YYYY-MM-DD" thành "DD/MM"
    const dt = new Date(d + 'T00:00:00');      // thêm T00:00:00 để tránh lỗi múi giờ
    return dt.toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit' });  // "23/06"
  },

  dateShort: d => {                            // format ngày kèm thứ: "T2 23/06"
    const dt   = new Date(d + 'T00:00:00');
    const days = ['CN','T2','T3','T4','T5','T6','T7'];  // tên thứ tiếng Việt
    return days[dt.getDay()] + ' ' + dt.toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit' });
  },

  comfortColor: (c, max) => {                  // hàm trả về màu dựa theo tỉ lệ điểm thoải mái
    const pct = c / max;                       // tỉ lệ so với điểm cao nhất
    if (pct >= 0.8) return '#10b981';          // ≥80%: màu xanh lá (tốt)
    if (pct >= 0.5) return '#f59e0b';          // ≥50%: màu vàng (trung bình)
    return '#ef4444';                          // <50%: màu đỏ (thấp)
  }
};

/* ─── Hệ thống Toast thông báo ────────────────────────────────── */
function toast(msg, type = 'info') {           // hiện thông báo popup góc dưới phải màn hình
  const icons = {                              // map loại thông báo → class icon Bootstrap
    success: 'bi-check-circle-fill',           // thành công: dấu tích xanh
    error:   'bi-x-circle-fill',              // lỗi: dấu x đỏ
    info:    'bi-info-circle-fill',           // thông tin: chữ i xanh
    warning: 'bi-exclamation-triangle-fill'   // cảnh báo: tam giác vàng
  };
  const wrap = document.getElementById('toastContainer');  // lấy container chứa các toast
  const el   = document.createElement('div'); // tạo phần tử div mới cho toast này
  el.className = `toast ${type}`;             // gán class css: "toast success" hoặc "toast error"...
  el.innerHTML = `
    <i class="bi ${icons[type] || icons.info} toast-icon"></i>
    <span class="toast-text">${msg}</span>
    <i class="bi bi-x toast-close" onclick="removeToast(this.parentElement)"></i>`;  // nội dung HTML của toast
  wrap.appendChild(el);                       // thêm toast vào container trong DOM
  setTimeout(() => removeToast(el), 4000);    // tự động xóa toast sau 4 giây
}

function removeToast(el) {                     // hàm xóa toast có hiệu ứng trượt ra
  if (!el || !el.parentElement) return;       // bỏ qua nếu toast đã bị xóa trước đó
  el.classList.add('removing');               // thêm class "removing" để chạy animation trượt ra
  setTimeout(() => el.remove(), 300);         // sau 300ms (thời gian animation) thì xóa hẳn khỏi DOM
}

/* ─── Hàm tiện ích ngày tháng ─────────────────────────────────── */
function todayStr() {                          // lấy ngày hôm nay dạng chuỗi "YYYY-MM-DD"
  return new Date().toISOString().slice(0, 10);  // cắt 10 ký tự đầu của ISO string
}

function formatDateVN(str) {                   // chuyển "YYYY-MM-DD" thành "DD/MM/YYYY" kiểu Việt Nam
  const [y, m, d] = str.split('-');           // tách chuỗi theo dấu "-"
  return `${d}/${m}/${y}`;                    // ghép lại theo thứ tự ngày/tháng/năm
}
