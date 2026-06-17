/* ════════════════════════════════════════════════════════════════
   Extras — Export, Algorithm Table, Device Stats, Tips Engine
   ════════════════════════════════════════════════════════════════ */

/* ─── CSV Export ─────────────────────────────────────────────── */
async function exportUsageCSV() {
  const [devs, usage] = await Promise.all([API.getDevices(), API.getUsage()]).catch(() => [[], []]);
  const devMap = Object.fromEntries(devs.map(d => [d.id, d]));
  const rows   = [['Ngày', 'Thiết bị', 'ID', 'Công suất (W)', 'Số giờ', 'kWh', 'Chi phí (₫)']];
  const cfg    = await API.getConfig().catch(() => ({ electricity_rate: 3500 }));

  usage.forEach(u => {
    const dev = devMap[u.device_id];
    if (!dev) return;
    const kwh  = dev.power_w * u.hours / 1000;
    const cost = Math.round(kwh * cfg.electricity_rate);
    rows.push([u.date, dev.name, dev.id, dev.power_w, u.hours, kwh.toFixed(3), cost]);
  });

  const csv  = rows.map(r => r.map(v => `"${v}"`).join(',')).join('\n');
  const blob = new Blob(['﻿' + csv], { type: 'text/csv;charset=utf-8;' });
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement('a');
  a.href     = url;
  a.download = `nhat-ky-dien-${todayStr()}.csv`;
  a.click();
  URL.revokeObjectURL(url);
  toast('Đã xuất file CSV!', 'success');
}

async function exportOptimizeCSV(result) {
  if (!result) { toast('Hãy chạy tối ưu trước', 'warning'); return; }
  const { dp, greedy } = result;
  const rows = [['Thuật toán', 'Thiết bị', 'Số giờ', 'kWh', 'Điểm thoải mái']];
  dp.schedule.forEach(s => rows.push(['DP', s.device.name, s.hours, s.kwh, s.comfort]));
  greedy.schedule.forEach(s => rows.push(['Greedy', s.device.name, s.hours, s.kwh, s.comfort]));
  const csv  = rows.map(r => r.map(v => `"${v}"`).join(',')).join('\n');
  const blob = new Blob(['﻿' + csv], { type: 'text/csv;charset=utf-8;' });
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement('a');
  a.href = url; a.download = `toi-uu-dp-greedy-${todayStr()}.csv`; a.click();
  URL.revokeObjectURL(url);
  toast('Đã xuất kết quả tối ưu!', 'success');
}

/* ─── Algorithm Complexity Table ─────────────────────────────── */
function renderComplexityTable(containerId) {
  const el = document.getElementById(containerId);
  if (!el) return;
  el.innerHTML = `
    <table class="data-table">
      <thead>
        <tr>
          <th>Thuật toán</th>
          <th>Thời gian</th>
          <th>Không gian</th>
          <th>Kết quả</th>
          <th>Trường hợp sử dụng</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><span class="badge badge-blue">DP Group Knapsack</span></td>
          <td class="mono" style="color:#00d4ff">O(n·W/δ·H/Δ)</td>
          <td class="mono" style="color:#a78bfa">O(n·W/δ)</td>
          <td><span class="badge badge-green">Tối ưu toàn cục</span></td>
          <td style="font-size:12px;color:var(--text-muted)">Khi cần đảm bảo lịch tốt nhất, chấp nhận thời gian tính lâu hơn</td>
        </tr>
        <tr>
          <td><span class="badge badge-purple">Greedy Ratio</span></td>
          <td class="mono" style="color:#10b981">O(n log n)</td>
          <td class="mono" style="color:#10b981">O(n)</td>
          <td><span class="badge badge-amber">Xấp xỉ</span></td>
          <td style="font-size:12px;color:var(--text-muted)">Khi cần kết quả nhanh, chấp nhận có thể không tối ưu</td>
        </tr>
        <tr>
          <td><span class="badge badge-gray">Brute Force</span></td>
          <td class="mono" style="color:#ef4444">O((H/Δ + 1)ⁿ)</td>
          <td class="mono" style="color:#ef4444">O(n)</td>
          <td><span class="badge badge-green">Tối ưu toàn cục</span></td>
          <td style="font-size:12px;color:var(--text-muted)">Không thực tế: n=10 thiết bị × 25 lựa chọn = 25¹⁰ ≈ 10¹⁴ phép tính</td>
        </tr>
      </tbody>
    </table>
    <div style="margin-top:14px;padding:12px 16px;background:rgba(0,212,255,0.04);border:1px solid rgba(0,212,255,0.12);border-radius:10px;font-size:12px;color:var(--text-muted)">
      <strong style="color:#00d4ff">Ký hiệu:</strong>
      n = số thiết bị · W = ngân sách (kWh) · δ = độ mịn ngân sách (0.01 kWh) · H = giờ tối đa/thiết bị · Δ = bước giờ (0.5h)
      <br>Ví dụ thực tế: n=10, W=2kWh, δ=0.01 → W/δ=200, H=12h, Δ=0.5 → H/Δ=24 → DP ≈ 10×200×24 = <strong style="color:#00d4ff">48.000 phép tính</strong>
    </div>`;
}

/* ─── Device Stats Detail ─────────────────────────────────────── */
async function renderDeviceStatsDetail(containerId) {
  const el = document.getElementById(containerId);
  if (!el) return;
  const [devs, usage, cfg] = await Promise.all([
    API.getDevices(), API.getUsage(), API.getConfig()
  ]).catch(() => [[], [], { electricity_rate: 3500 }]);

  const devMap    = Object.fromEntries(devs.map(d => [d.id, d]));
  const dateSet   = new Set(usage.map(u => u.date));
  const nDays     = Math.max(dateSet.size, 1);

  const stats = devs.map(dev => {
    const entries = usage.filter(u => u.device_id === dev.id);
    const totalH  = entries.reduce((s, u) => s + u.hours, 0);
    const totalKwh = dev.power_w * totalH / 1000;
    const cost    = totalKwh * cfg.electricity_rate;
    const avgH    = totalH / nDays;
    const usedDays = new Set(entries.map(u => u.date)).size;
    return {
      dev, totalH, totalKwh, cost, avgH, usedDays,
      usagePct: usedDays / nDays,
      monthlyKwh: dev.power_w * avgH * 30 / 1000,
      monthlyCost: dev.power_w * avgH * 30 / 1000 * cfg.electricity_rate
    };
  }).filter(s => s.totalH > 0).sort((a, b) => b.totalKwh - a.totalKwh);

  if (!stats.length) {
    el.innerHTML = '<div class="empty-state"><i class="bi bi-bar-chart"></i><p>Chưa có dữ liệu. Hãy ghi nhật ký trước.</p></div>';
    return;
  }

  const maxKwh = stats[0].totalKwh;
  el.innerHTML = `
    <table class="data-table">
      <thead>
        <tr>
          <th>Thiết bị</th>
          <th>Tổng giờ</th>
          <th>Tổng kWh</th>
          <th>Chi phí</th>
          <th>TB/ngày</th>
          <th>Ngày dùng</th>
          <th>kWh/tháng*</th>
          <th>Tỷ trọng</th>
        </tr>
      </thead>
      <tbody>
        ${stats.map(s => `
          <tr>
            <td>
              <div style="display:flex;align-items:center;gap:8px">
                <span>${deviceIcon(s.dev)}</span>
                <div>
                  <div style="font-weight:600;color:var(--text-bright)">${s.dev.name}</div>
                  <div style="font-size:11px;color:var(--text-muted)">${s.dev.power_w}W</div>
                </div>
              </div>
            </td>
            <td style="font-weight:600">${s.totalH.toFixed(1)}h</td>
            <td style="color:#00d4ff;font-weight:700">${s.totalKwh.toFixed(3)}</td>
            <td style="color:#f59e0b">${fmt.vnd(s.cost)}</td>
            <td style="color:var(--text-muted)">${s.avgH.toFixed(2)}h</td>
            <td>
              <div style="display:flex;align-items:center;gap:6px">
                <span style="font-weight:600">${s.usedDays}</span>
                <span style="font-size:11px;color:var(--text-muted)">/ ${nDays} ngày</span>
              </div>
            </td>
            <td style="color:#a78bfa">${s.monthlyKwh.toFixed(1)}</td>
            <td style="min-width:100px">
              <div class="progress-bar-wrap">
                <div class="progress-bar-fill" style="width:${(s.totalKwh/maxKwh*100).toFixed(1)}%;background:${catColor(s.dev.category)}"></div>
              </div>
            </td>
          </tr>`).join('')}
      </tbody>
    </table>
    <div style="font-size:11px;color:var(--text-muted);margin-top:8px;padding-left:4px">
      * Ước tính tháng dựa trên trung bình ${nDays} ngày đã ghi
    </div>`;
}

/* ─── Seasonal Tips Engine ────────────────────────────────────── */
const SEASONAL_TIPS = [
  {
    icon: '❄️',
    title: 'Điều hòa tiết kiệm điện',
    tips: [
      'Đặt nhiệt độ 26–28°C thay vì 18–20°C — tiết kiệm tới 30% điện năng',
      'Bật chế độ "Economy" hoặc "Eco" trên điều hòa',
      'Vệ sinh lọc điều hòa mỗi 1–2 tháng để tăng hiệu suất',
      'Kết hợp quạt điện + điều hòa để tối ưu làm mát',
    ]
  },
  {
    icon: '💡',
    title: 'Chiếu sáng thông minh',
    tips: [
      'Dùng đèn LED thay bóng huỳnh quang — tiết kiệm 60–80% điện',
      'Tắt đèn khi rời khỏi phòng (có thể dùng công tắc hẹn giờ)',
      'Tận dụng ánh sáng tự nhiên ban ngày',
      'Đèn cắm cảm biến chuyển động tốt hơn đèn để sáng 24/7',
    ]
  },
  {
    icon: '🔌',
    title: 'Tránh lãng phí điện chờ',
    tips: [
      'Rút phích cắm TV, sạc điện thoại khi không dùng — standby tiêu tốn 5–10W',
      'Dùng ổ điện có công tắc để tắt nhiều thiết bị cùng lúc',
      'Laptop ở chế độ sạc đầy nên rút dây (tránh quá nhiệt và hao pin)',
      'Tủ lạnh không nên để cạnh nguồn nhiệt (bếp, ánh nắng)',
    ]
  },
  {
    icon: '⏰',
    title: 'Sử dụng giờ thấp điểm',
    tips: [
      'Giặt đồ, nấu cơm vào buổi sáng sớm hoặc sau 22h',
      'Tránh dùng bình nóng lạnh trong giờ cao điểm 17h–20h',
      'Sạc pin điện thoại, laptop vào ban đêm',
      'Lên lịch sử dụng máy giặt vào cuối tuần buổi sáng',
    ]
  },
  {
    icon: '🍚',
    title: 'Nấu nướng hiệu quả',
    tips: [
      'Nồi cơm điện: cắm trước khi cần 20 phút, không để nóng quá lâu',
      'Bình siêu tốc đun đủ lượng nước cần, không đun thừa',
      'Dùng lò vi sóng nhanh hơn và ít điện hơn lò nướng với món nhỏ',
      'Hâm nóng thức ăn bằng nồi cơm điện tiết kiệm hơn lò vi sóng',
    ]
  },
];

function renderSeasonalTips(containerId) {
  const el = document.getElementById(containerId);
  if (!el) return;
  el.innerHTML = SEASONAL_TIPS.map(cat => `
    <div class="glass" style="margin-bottom:14px">
      <div class="card-header">
        <div class="card-title">${cat.icon} ${cat.title}</div>
      </div>
      <div class="card-body">
        <ul style="list-style:none;padding:0;margin:0">
          ${cat.tips.map(t => `
            <li style="display:flex;align-items:flex-start;gap:10px;padding:10px 0;border-bottom:1px solid var(--border)">
              <span style="color:#10b981;font-size:14px;margin-top:1px;flex-shrink:0">✓</span>
              <span style="font-size:13px;color:var(--text-main);line-height:1.5">${t}</span>
            </li>`).join('')}
        </ul>
      </div>
    </div>`).join('');
}

/* ─── Monthly Budget Planner ──────────────────────────────────── */
function calcMonthlyBudgetPlan(dailyBudget, rate, targetBill) {
  const monthlyKwh = dailyBudget * 30;
  // EVN tiers
  const tiers = [
    { lim: 50,   rate: 1806 },
    { lim: 50,   rate: 1866 },
    { lim: 100,  rate: 2167 },
    { lim: 100,  rate: 2729 },
    { lim: 100,  rate: 3050 },
    { lim: 9999, rate: 3151 },
  ];
  let cost = 0; let rem = monthlyKwh;
  for (const t of tiers) {
    const used = Math.min(rem, t.lim);
    cost += used * t.rate;
    rem -= used;
    if (rem <= 0) break;
  }
  const saving = cost - (targetBill || 0);
  return {
    monthlyKwh: Math.round(monthlyKwh * 10) / 10,
    evnCost:    Math.round(cost),
    saving:     Math.round(saving),
    withinBudget: saving <= 0
  };
}

function renderBudgetPlanner(containerId) {
  const el = document.getElementById(containerId);
  if (!el) return;
  el.innerHTML = `
    <div class="form-group">
      <label class="form-label">Ngân sách mục tiêu (kWh/ngày)</label>
      <input type="number" id="plannerBudget" class="form-input" step="0.1" min="0.1" max="20" value="2.0" placeholder="2.0">
    </div>
    <div class="form-group">
      <label class="form-label">Hóa đơn mục tiêu / tháng (₫)</label>
      <input type="number" id="plannerTarget" class="form-input" step="1000" min="0" max="5000000" value="300000" placeholder="300000">
    </div>
    <button class="btn btn-secondary w-100" onclick="runBudgetPlanner()">
      <i class="bi bi-calculator-fill"></i> Tính kế hoạch
    </button>
    <div id="plannerResult" style="margin-top:14px"></div>`;
}

function runBudgetPlanner() {
  const budget = parseFloat(document.getElementById('plannerBudget')?.value || 2);
  const target = parseFloat(document.getElementById('plannerTarget')?.value || 300000);
  const plan   = calcMonthlyBudgetPlan(budget, 3500, target);
  const el     = document.getElementById('plannerResult');
  if (!el) return;
  const color  = plan.withinBudget ? '#10b981' : '#ef4444';
  el.innerHTML = `
    <div style="padding:14px;border-radius:10px;background:${plan.withinBudget?'rgba(16,185,129,0.06)':'rgba(239,68,68,0.06)'};border:1px solid ${plan.withinBudget?'rgba(16,185,129,0.2)':'rgba(239,68,68,0.2)'}">
      <div style="font-size:13px;color:var(--text-muted);margin-bottom:10px">Kết quả tính toán:</div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px">
        <div style="text-align:center">
          <div style="font-size:22px;font-weight:800;color:#00d4ff">${plan.monthlyKwh} kWh</div>
          <div style="font-size:11px;color:var(--text-muted)">tiêu thụ/tháng</div>
        </div>
        <div style="text-align:center">
          <div style="font-size:22px;font-weight:800;color:${color}">${fmt.vndFull(plan.evnCost)}</div>
          <div style="font-size:11px;color:var(--text-muted)">hóa đơn EVN</div>
        </div>
      </div>
      <div style="margin-top:12px;text-align:center;font-size:13px;font-weight:700;color:${color}">
        ${plan.withinBudget
          ? `✅ Tiết kiệm được ${fmt.vndFull(Math.abs(plan.saving))} so với mục tiêu!`
          : `⚠️ Vượt mục tiêu ${fmt.vndFull(Math.abs(plan.saving))} — hãy giảm xuống ${Math.max(0.5, budget - 0.5).toFixed(1)} kWh/ngày`}
      </div>
    </div>`;
}

/* ─── Power Level Indicator ───────────────────────────────────── */
function getPowerLevel(kwh, budget) {
  const pct = budget > 0 ? kwh / budget : 0;
  if (pct <= 0)    return { label: 'Chưa dùng', color: '#64748b', icon: 'bi-circle' };
  if (pct <= 0.50) return { label: 'Tiết kiệm',  color: '#10b981', icon: 'bi-battery-full' };
  if (pct <= 0.75) return { label: 'Bình thường', color: '#f59e0b', icon: 'bi-battery-half' };
  if (pct <= 1.00) return { label: 'Gần giới hạn', color: '#fb923c', icon: 'bi-battery-low' };
  return { label: 'Vượt ngân sách', color: '#ef4444', icon: 'bi-battery-charging' };
}

/* ─── Quick Actions ───────────────────────────────────────────── */
function setupQuickActions() {
  const shortcuts = [
    { key: '1', tab: 'dashboard',  label: 'Dashboard' },
    { key: '2', tab: 'devices',    label: 'Thiết bị' },
    { key: '3', tab: 'usage',      label: 'Nhật ký' },
    { key: '4', tab: 'optimize',   label: 'Tối ưu' },
    { key: '5', tab: 'peak',       label: 'Lịch cao điểm' },
    { key: '6', tab: 'forecast',   label: 'Dự báo' },
    { key: '7', tab: 'settings',   label: 'Cài đặt' },
  ];
  document.addEventListener('keydown', e => {
    if (e.altKey) {
      const sc = shortcuts.find(s => s.key === e.key);
      if (sc) { e.preventDefault(); switchTab(sc.tab); }
    }
  });
}

/* ─── Theme / UI State Persistence ───────────────────────────── */
const UIState = {
  save(key, value) {
    try { localStorage.setItem('elec_' + key, JSON.stringify(value)); } catch {}
  },
  load(key, def) {
    try {
      const v = localStorage.getItem('elec_' + key);
      return v !== null ? JSON.parse(v) : def;
    } catch { return def; }
  }
};

/* ─── Number animation ────────────────────────────────────────── */
function animateNumber(el, from, to, duration = 800, decimals = 0) {
  const start = performance.now();
  function update(now) {
    const t   = Math.min((now - start) / duration, 1);
    const val = from + (to - from) * easeOut(t);
    el.textContent = val.toFixed(decimals);
    if (t < 1) requestAnimationFrame(update);
  }
  requestAnimationFrame(update);
}

function easeOut(t) { return 1 - Math.pow(1 - t, 3); }

/* ─── Debounce ────────────────────────────────────────────────── */
function debounce(fn, ms) {
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), ms);
  };
}

/* ─── Copy to clipboard ───────────────────────────────────────── */
function copyText(text) {
  navigator.clipboard.writeText(text)
    .then(() => toast('Đã sao chép!', 'success'))
    .catch(() => toast('Không thể sao chép', 'error'));
}

/* ─── Format duration ─────────────────────────────────────────── */
function fmtDuration(hours) {
  const h = Math.floor(hours);
  const m = Math.round((hours - h) * 60);
  if (h === 0) return `${m}p`;
  if (m === 0) return `${h}h`;
  return `${h}h${m}p`;
}

/* ─── Day of week label ───────────────────────────────────────── */
function dayLabel(dateStr) {
  const d = new Date(dateStr + 'T00:00:00');
  return ['CN','T2','T3','T4','T5','T6','T7'][d.getDay()];
}

/* ─── Weekly summary ──────────────────────────────────────────── */
function calcWeeklySummary(daily) {
  const thisWeek = daily.slice(-7);
  const lastWeek = daily.slice(-14, -7);
  const thisTotal = thisWeek.reduce((s, d) => s + d.kwh, 0);
  const lastTotal = lastWeek.reduce((s, d) => s + d.kwh, 0);
  const change    = lastTotal > 0 ? (thisTotal - lastTotal) / lastTotal * 100 : 0;
  return {
    thisWeek: Math.round(thisTotal * 1000) / 1000,
    lastWeek: Math.round(lastTotal * 1000) / 1000,
    change:   Math.round(change * 10) / 10,
    improved: change < 0
  };
}

/* ─── Render weekly comparison ────────────────────────────────── */
function renderWeeklySummary(stats, containerId) {
  const el = document.getElementById(containerId);
  if (!el || !stats?.daily?.length) return;
  const w = calcWeeklySummary(stats.daily);
  const color = w.improved ? '#10b981' : '#ef4444';
  const icon  = w.improved ? 'bi-arrow-down-circle-fill' : 'bi-arrow-up-circle-fill';
  el.innerHTML = `
    <div style="display:flex;align-items:center;gap:16px;flex-wrap:wrap">
      <div style="flex:1;text-align:center">
        <div style="font-size:11px;font-weight:700;text-transform:uppercase;color:var(--text-muted);margin-bottom:4px">Tuần này</div>
        <div style="font-size:22px;font-weight:800;color:#00d4ff">${w.thisWeek} kWh</div>
      </div>
      <div style="text-align:center;padding:0 8px">
        <i class="bi ${icon}" style="font-size:24px;color:${color}"></i>
        <div style="font-size:12px;font-weight:700;color:${color}">${w.change > 0 ? '+' : ''}${w.change}%</div>
        <div style="font-size:10px;color:var(--text-muted)">vs tuần trước</div>
      </div>
      <div style="flex:1;text-align:center">
        <div style="font-size:11px;font-weight:700;text-transform:uppercase;color:var(--text-muted);margin-bottom:4px">Tuần trước</div>
        <div style="font-size:22px;font-weight:800;color:var(--text-muted)">${w.lastWeek} kWh</div>
      </div>
    </div>`;
}

/* ─── Auto refresh dashboard ──────────────────────────────────── */
let _autoRefreshTimer = null;

function startAutoRefresh(intervalMs = 60000) {
  stopAutoRefresh();
  _autoRefreshTimer = setInterval(() => {
    if (State.activeTab === 'dashboard') {
      renderDashboard();
    }
  }, intervalMs);
}

function stopAutoRefresh() {
  if (_autoRefreshTimer) { clearInterval(_autoRefreshTimer); _autoRefreshTimer = null; }
}

/* ─── Initialize extras ───────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  setupQuickActions();
  startAutoRefresh(120000);
});

/* ─── EVN tier labels ─────────────────────────────────────────── */
const EVN_TIERS = [
  { label: 'Bậc 1', limit: 50,   price: 1806, color: '#10b981' },
  { label: 'Bậc 2', limit: 100,  price: 1866, color: '#34d399' },
  { label: 'Bậc 3', limit: 200,  price: 2167, color: '#f59e0b' },
  { label: 'Bậc 4', limit: 300,  price: 2729, color: '#fb923c' },
  { label: 'Bậc 5', limit: 400,  price: 3050, color: '#ef4444' },
  { label: 'Bậc 6', limit: 9999, price: 3151, color: '#dc2626' },
];

function getTier(monthlyKwh) {
  let rem = monthlyKwh;
  for (const t of EVN_TIERS) {
    if (rem <= t.limit) return t;
    rem -= t.limit;
  }
  return EVN_TIERS[EVN_TIERS.length - 1];
}

/* ─── Consumption grade ───────────────────────────────────────── */
function getConsumptionGrade(monthlyKwh) {
  if (monthlyKwh <= 50)  return { grade: 'A+', label: 'Xuất sắc', color: '#10b981' };
  if (monthlyKwh <= 100) return { grade: 'A',  label: 'Tốt',      color: '#34d399' };
  if (monthlyKwh <= 150) return { grade: 'B',  label: 'Khá',      color: '#f59e0b' };
  if (monthlyKwh <= 200) return { grade: 'C',  label: 'Trung bình',color: '#fb923c' };
  if (monthlyKwh <= 300) return { grade: 'D',  label: 'Cao',      color: '#ef4444' };
  return { grade: 'F', label: 'Rất cao', color: '#dc2626' };
}

/* ─── Device efficiency score ─────────────────────────────────── */
function deviceEfficiencyScore(dev) {
  const ratio = dev.priority / dev.power_w;
  const maxRatio = 5 / 10;
  return Math.min(100, Math.round(ratio / maxRatio * 100));
}

/* ─── Format numbers consistently ────────────────────────────── */
function numPad(n, decimals = 0) {
  return n.toLocaleString('vi-VN', { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
}

/* ─── Solar savings calculator (bonus feature) ───────────────── */
function calcSolarSavings(panelWatts, sunHoursPerDay, rate) {
  const dailyKwh   = panelWatts * sunHoursPerDay / 1000;
  const monthlyKwh = dailyKwh * 30;
  const savings    = monthlyKwh * rate;
  return { dailyKwh, monthlyKwh, savings };
}

/* ─── Local storage helpers ───────────────────────────────────── */
const LS = {
  get:    (k, d) => { try { const v = localStorage.getItem(k); return v ? JSON.parse(v) : d; } catch { return d; } },
  set:    (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)); } catch {} },
  remove: (k)    => { try { localStorage.removeItem(k); } catch {} }
};
