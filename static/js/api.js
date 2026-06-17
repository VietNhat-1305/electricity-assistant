/* ════════════════════════════════════════════════════════════════
   API Layer — wraps all fetch calls to Flask backend
   ════════════════════════════════════════════════════════════════ */

const API = {
  /* ─── Devices ────────────────────────────────────────────── */
  async getDevices() {
    const r = await fetch('/api/devices');
    if (!r.ok) throw new Error('Không thể tải danh sách thiết bị');
    return r.json();
  },
  async addDevice(d) {
    const r = await fetch('/api/devices', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(d)
    });
    const data = await r.json();
    if (!r.ok) throw new Error(data.error || 'Lỗi thêm thiết bị');
    return data;
  },
  async deleteDevice(id) {
    const r = await fetch(`/api/devices/${id}`, { method: 'DELETE' });
    if (!r.ok) throw new Error('Lỗi xóa thiết bị');
    return r.json();
  },
  async resetDevices() {
    const r = await fetch('/api/devices/reset', { method: 'POST' });
    if (!r.ok) throw new Error('Lỗi reset thiết bị');
    return r.json();
  },

  /* ─── Usage ──────────────────────────────────────────────── */
  async getUsage() {
    const r = await fetch('/api/usage');
    if (!r.ok) throw new Error('Không thể tải nhật ký');
    return r.json();
  },
  async saveUsage(device_id, date, hours) {
    const r = await fetch('/api/usage', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ device_id, date, hours })
    });
    if (!r.ok) throw new Error('Lỗi lưu nhật ký');
    return r.json();
  },
  async deleteDay(date) {
    const r = await fetch(`/api/usage/${date}`, { method: 'DELETE' });
    if (!r.ok) throw new Error('Lỗi xóa ngày');
    return r.json();
  },

  /* ─── Config ─────────────────────────────────────────────── */
  async getConfig() {
    const r = await fetch('/api/config');
    if (!r.ok) throw new Error('Lỗi tải cài đặt');
    return r.json();
  },
  async saveConfig(cfg) {
    const r = await fetch('/api/config', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(cfg)
    });
    if (!r.ok) throw new Error('Lỗi lưu cài đặt');
    return r.json();
  },

  /* ─── Stats ──────────────────────────────────────────────── */
  async getStats() {
    const r = await fetch('/api/stats');
    if (!r.ok) throw new Error('Lỗi tải thống kê');
    return r.json();
  },

  /* ─── Optimize ───────────────────────────────────────────── */
  async optimize(budget_kwh) {
    const r = await fetch('/api/optimize', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ budget_kwh })
    });
    if (!r.ok) throw new Error('Lỗi tối ưu hóa');
    return r.json();
  },

  /* ─── Peak ───────────────────────────────────────────────── */
  async getPeak(budget_kwh) {
    const r = await fetch('/api/peak', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ budget_kwh })
    });
    if (!r.ok) throw new Error('Lỗi lấy lịch cao điểm');
    return r.json();
  },

  /* ─── Heatmap ────────────────────────────────────────────── */
  async getHeatmap() {
    const r = await fetch('/api/heatmap');
    if (!r.ok) throw new Error('Lỗi tải heatmap');
    return r.json();
  },

  /* ─── Forecast ───────────────────────────────────────────── */
  async getForecast() {
    const r = await fetch('/api/forecast');
    if (!r.ok) throw new Error('Lỗi tải dự báo');
    return r.json();
  },

  /* ─── EVN ────────────────────────────────────────────────── */
  async calcEvn(kwh) {
    const r = await fetch('/api/evn', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ kwh })
    });
    if (!r.ok) throw new Error('Lỗi tính EVN');
    return r.json();
  }
};

/* ─── Meta lookup for categories ─────────────────────────────── */
const CATEGORY_META = {
  cooling:       { icon: '❄️',  color: '#38bdf8', label: 'Làm mát' },
  lighting:      { icon: '💡',  color: '#fbbf24', label: 'Chiếu sáng' },
  computing:     { icon: '💻',  color: '#a78bfa', label: 'Máy tính' },
  heating:       { icon: '🔥',  color: '#f87171', label: 'Nhiệt' },
  entertainment: { icon: '📺',  color: '#fb923c', label: 'Giải trí' },
  cooking:       { icon: '🍚',  color: '#4ade80', label: 'Nấu ăn' },
  cleaning:      { icon: '🌊',  color: '#67e8f9', label: 'Vệ sinh' },
  other:         { icon: '🔌',  color: '#94a3b8', label: 'Khác' },
};

const DEVICE_ICONS = {
  ac: '❄️', fan: '🌬️', light: '💡', laptop: '💻', phone: '📱',
  heater: '🚿', tv: '📺', rice: '🍚', fridge: '🧊', washing: '🌊'
};

function deviceIcon(dev) {
  return DEVICE_ICONS[dev.id] || CATEGORY_META[dev.category]?.icon || '🔌';
}

function catColor(cat) { return CATEGORY_META[cat]?.color || '#94a3b8'; }
function catLabel(cat) { return CATEGORY_META[cat]?.label || 'Khác'; }

/* ─── Formatting helpers ──────────────────────────────────────── */
const fmt = {
  vnd:   n => n >= 1000 ? `${(n/1000).toFixed(0)}k ₫` : `${Math.round(n)} ₫`,
  vndFull: n => new Intl.NumberFormat('vi-VN').format(Math.round(n)) + ' ₫',
  kwh:   n => `${(+n).toFixed(3)} kWh`,
  kwhS:  n => `${(+n).toFixed(2)} kWh`,
  hours: n => n >= 1 ? `${n}h` : `${(n*60).toFixed(0)}p`,
  pct:   n => `${(+n).toFixed(1)}%`,
  date:  d => {
    const dt = new Date(d + 'T00:00:00');
    return dt.toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit' });
  },
  dateShort: d => {
    const dt = new Date(d + 'T00:00:00');
    const days = ['CN','T2','T3','T4','T5','T6','T7'];
    return days[dt.getDay()] + ' ' + dt.toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit' });
  },
  comfortColor: (c, max) => {
    const pct = c / max;
    if (pct >= 0.8) return '#10b981';
    if (pct >= 0.5) return '#f59e0b';
    return '#ef4444';
  }
};

/* ─── Toast system ────────────────────────────────────────────── */
function toast(msg, type = 'info') {
  const icons = { success: 'bi-check-circle-fill', error: 'bi-x-circle-fill', info: 'bi-info-circle-fill', warning: 'bi-exclamation-triangle-fill' };
  const wrap = document.getElementById('toastContainer');
  const el = document.createElement('div');
  el.className = `toast ${type}`;
  el.innerHTML = `
    <i class="bi ${icons[type] || icons.info} toast-icon"></i>
    <span class="toast-text">${msg}</span>
    <i class="bi bi-x toast-close" onclick="removeToast(this.parentElement)"></i>`;
  wrap.appendChild(el);
  setTimeout(() => removeToast(el), 4000);
}

function removeToast(el) {
  if (!el || !el.parentElement) return;
  el.classList.add('removing');
  setTimeout(() => el.remove(), 300);
}

/* ─── Today's date helper ─────────────────────────────────────── */
function todayStr() {
  return new Date().toISOString().slice(0, 10);
}

function formatDateVN(str) {
  const [y,m,d] = str.split('-');
  return `${d}/${m}/${y}`;
}
