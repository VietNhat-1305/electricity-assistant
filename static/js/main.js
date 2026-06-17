/* ════════════════════════════════════════════════════════════════
   Main App — State, Rendering, Event Handlers
   ════════════════════════════════════════════════════════════════ */

/* ─── App State ───────────────────────────────────────────────── */
const State = {
  devices: [],
  usage: [],
  config: { daily_budget_kwh: 2.0, electricity_rate: 3500, peak_hours: [17,18,19,20,21] },
  stats: null,
  optimizeResult: null,
  peakResult: null,
  forecastResult: null,
  heatmapResult: null,
  activeTab: 'dashboard',
  usageDate: todayStr(),
  optimizeBudget: 2.0,
  peakBudget: 2.0,
  filterCategory: 'all',
};

/* ─── Tab Navigation ─────────────────────────────────────────── */
function switchTab(tab) {
  State.activeTab = tab;
  document.querySelectorAll('.tab-pane').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.nav-tab-btn').forEach(el => el.classList.remove('active'));
  const pane = document.getElementById('tab-' + tab);
  if (pane) pane.classList.add('active');
  document.querySelectorAll(`[data-tab="${tab}"]`).forEach(el => el.classList.add('active'));
  onTabActivated(tab);
}

function onTabActivated(tab) {
  if (tab === 'dashboard') renderDashboard();
  else if (tab === 'devices') renderDevicesTab();
  else if (tab === 'usage') renderUsageTab();
  else if (tab === 'forecast') renderForecastTab();
  else if (tab === 'settings') renderSettingsTab();
}

/* ─── DASHBOARD ───────────────────────────────────────────────── */
async function renderDashboard() {
  try {
    const stats = await API.getStats();
    State.stats = stats;
    renderKPIs(stats);
    renderDailyChart(stats.daily);
    renderDonutChart(stats.by_device);
    renderTips(stats.tips);
    renderBudgetGauge(stats.today_kwh, stats.budget);
    renderTopDevices(stats.by_device.slice(0, 5));
  } catch (e) { toast(e.message, 'error'); }
}

function renderKPIs(s) {
  const pct = s.budget > 0 ? (s.today_kwh / s.budget * 100) : 0;
  const isOver = s.today_kwh > s.budget;

  setKPI('kpiToday', fmt.kwh(s.today_kwh),
    `Ngân sách còn: ${fmt.kwh(s.budget_rem)}`,
    isOver ? 'red' : 'blue');

  setKPI('kpiAvg', fmt.kwhS(s.avg_kwh),
    `Trung bình ${s.n_days} ngày ghi nhận`, 'purple');

  setKPI('kpiMonthly', `${(s.monthly_kwh || 0).toFixed(0)} kWh`,
    `≈ ${fmt.vnd(s.est_evn)}/tháng (EVN)`, 'green');

  setKPI('kpiDevices', State.devices.length.toString(),
    `${State.devices.filter(d=>d.priority>=4).length} thiết bị ưu tiên cao`, 'amber');

  // Budget indicator
  const budgetBar = document.getElementById('budgetBarFill');
  const budgetPct = Math.min(100, pct);
  if (budgetBar) {
    budgetBar.style.width = budgetPct + '%';
    budgetBar.style.background = isOver
      ? 'linear-gradient(90deg, #ef4444, #dc2626)'
      : pct > 75
        ? 'linear-gradient(90deg, #f59e0b, #d97706)'
        : 'linear-gradient(90deg, #00d4ff, #0088cc)';
  }

  const budgetDisplay = document.getElementById('budgetDisplay');
  if (budgetDisplay) {
    budgetDisplay.dataset.budget = s.budget;
    budgetDisplay.textContent = `${s.today_kwh.toFixed(3)} / ${s.budget} kWh (${pct.toFixed(1)}%)`;
    budgetDisplay.style.color = isOver ? '#ef4444' : pct > 75 ? '#f59e0b' : '#10b981';
  }
}

function setKPI(id, value, sub, color) {
  const el = document.getElementById(id);
  if (!el) return;
  el.querySelector('.kpi-value').innerHTML = value;
  el.querySelector('.kpi-sub').textContent = sub;
  el.className = `kpi-card ${color}`;
}

function renderBudgetGauge(used, total) {
  const el = document.getElementById('gaugeWrap');
  if (!el) return;
  const pct = total > 0 ? Math.min(1, used / total) : 0;
  const r = 44; const circ = 2 * Math.PI * r;
  const offset = circ * (1 - pct);
  const color = pct > 1 ? '#ef4444' : pct > 0.75 ? '#f59e0b' : '#10b981';
  el.innerHTML = `
    <div class="budget-gauge">
      <svg viewBox="0 0 100 100">
        <circle class="gauge-bg" cx="50" cy="50" r="${r}"/>
        <circle class="gauge-fill" cx="50" cy="50" r="${r}"
          stroke="${color}" stroke-dasharray="${circ}" stroke-dashoffset="${offset}"
          style="transition:stroke-dashoffset 1s ease;"/>
      </svg>
      <div class="gauge-text">
        <div class="gauge-pct" style="color:${color}">${(pct*100).toFixed(0)}%</div>
        <div class="gauge-sub">hôm nay</div>
      </div>
    </div>`;
}

function renderTips(tips) {
  const el = document.getElementById('tipsContainer');
  if (!el) return;
  if (!tips || !tips.length) {
    el.innerHTML = `<div class="empty-state"><i class="bi bi-check-circle"></i><h3>Tốt lắm!</h3><p>Không có gợi ý tiết kiệm nào</p></div>`;
    return;
  }
  el.innerHTML = tips.map(t => `
    <div class="tip-item">
      <div class="tip-icon ${t.level}">
        ${t.level === 'danger' ? '⚡' : '💡'}
      </div>
      <div>
        <div class="tip-text"><span class="tip-device">${t.device}</span> — ${t.msg}</div>
        <div class="tip-save">Tiết kiệm ~${t.save_kwh} kWh/ngày</div>
      </div>
    </div>`).join('');
}

function renderTopDevices(byDev) {
  const el = document.getElementById('topDevicesContainer');
  if (!el) return;
  if (!byDev.length) { el.innerHTML = '<div class="empty-state"><i class="bi bi-bar-chart"></i><p>Chưa có dữ liệu sử dụng</p></div>'; return; }
  const maxKwh = byDev[0]?.kwh || 1;
  el.innerHTML = byDev.map(d => `
    <div class="d-flex align-center justify-between mb-3" style="gap:10px">
      <span style="font-size:13px;font-weight:600;color:var(--text-bright);min-width:120px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${d.name}</span>
      <div style="flex:1">
        <div class="progress-bar-wrap">
          <div class="progress-bar-fill" style="width:${(d.kwh/maxKwh*100).toFixed(1)}%;background:${catColor(d.category)}"></div>
        </div>
      </div>
      <span style="font-size:12px;color:var(--text-muted);min-width:70px;text-align:right">${fmt.kwhS(d.kwh)}</span>
    </div>`).join('');
}

/* ─── DEVICES TAB ─────────────────────────────────────────────── */
async function renderDevicesTab() {
  const devs = await API.getDevices().catch(e => { toast(e.message,'error'); return []; });
  State.devices = devs;
  renderDeviceFilter();
  renderDeviceGrid(devs);
  renderCategoryChart(State.stats?.by_device || []);
}

function renderDeviceFilter() {
  const el = document.getElementById('deviceFilterBtns');
  if (!el) return;
  const cats = ['all', ...new Set(State.devices.map(d => d.category))];
  el.innerHTML = cats.map(c => `
    <button class="period-btn ${c===State.filterCategory?'active':''}" onclick="filterDevices('${c}')">
      ${c === 'all' ? '🔌 Tất cả' : `${CATEGORY_META[c]?.icon||'•'} ${catLabel(c)}`}
    </button>`).join('');
}

function filterDevices(cat) {
  State.filterCategory = cat;
  renderDeviceFilter();
  const filtered = cat === 'all' ? State.devices : State.devices.filter(d => d.category === cat);
  renderDeviceGrid(filtered);
}

function renderDeviceGrid(devs) {
  const el = document.getElementById('devicesGrid');
  if (!el) return;
  if (!devs.length) { el.innerHTML = '<div class="empty-state" style="grid-column:1/-1"><i class="bi bi-plug"></i><h3>Không có thiết bị</h3><p>Thêm thiết bị mới bên dưới</p></div>'; return; }
  el.innerHTML = devs.map(d => {
    const icon = deviceIcon(d);
    const bgCls = `cat-bg-${d.category}`;
    const clrCls = `cat-${d.category}`;
    const stars = Array.from({length:5},(_,i)=>`<div class="priority-star" style="background:${i<d.priority?'#f59e0b':'rgba(255,255,255,0.08)'}"></div>`).join('');
    return `
    <div class="device-card">
      <div class="device-card-icon ${bgCls} ${clrCls}" style="font-size:24px;width:48px;height:48px;border-radius:12px;display:flex;align-items:center;justify-content:center;">${icon}</div>
      <div class="device-card-name">${d.name}</div>
      <div class="device-card-power">⚡ ${d.power_w}W · ${d.max_daily_hours}h/ngày</div>
      <div class="priority-stars">${stars}</div>
      <div class="d-flex align-center gap-2">
        <span class="badge badge-gray">${catLabel(d.category)}</span>
        <span class="badge ${d.power_w>=500?'badge-red':d.power_w>=100?'badge-amber':'badge-green'}">${d.power_w>=500?'Tốn điện':d.power_w>=100?'Trung bình':'Tiết kiệm'}</span>
      </div>
      <div class="device-card-actions">
        <button class="btn btn-ghost btn-sm w-100" onclick="deleteDevice('${d.id}')">
          <i class="bi bi-trash3"></i> Xóa
        </button>
      </div>
    </div>`;
  }).join('');
}

async function deleteDevice(id) {
  if (!confirm('Xóa thiết bị này?')) return;
  try {
    await API.deleteDevice(id);
    toast('Đã xóa thiết bị', 'success');
    renderDevicesTab();
  } catch (e) { toast(e.message, 'error'); }
}

async function resetDevices() {
  if (!confirm('Khôi phục về danh sách mặc định?')) return;
  try {
    await API.resetDevices();
    toast('Đã khôi phục danh sách thiết bị', 'success');
    renderDevicesTab();
  } catch (e) { toast(e.message, 'error'); }
}

function openAddDeviceModal() {
  document.getElementById('addDeviceModal').classList.add('show');
}

function closeAddDeviceModal() {
  document.getElementById('addDeviceModal').classList.remove('show');
  document.getElementById('addDeviceForm').reset();
}

async function submitAddDevice(e) {
  e.preventDefault();
  const f = e.target;
  const dev = {
    id: f.devId.value.trim().toLowerCase().replace(/\s+/g,'_'),
    name: f.devName.value.trim(),
    power_w: parseInt(f.devPower.value),
    priority: parseInt(f.devPriority.value),
    max_daily_hours: parseFloat(f.devHours.value),
    category: f.devCategory.value
  };
  if (!dev.id || !dev.name) { toast('Vui lòng điền đầy đủ', 'warning'); return; }
  try {
    await API.addDevice(dev);
    toast(`Đã thêm ${dev.name}`, 'success');
    closeAddDeviceModal();
    renderDevicesTab();
  } catch (e) { toast(e.message, 'error'); }
}

/* ─── USAGE TAB ───────────────────────────────────────────────── */
async function renderUsageTab() {
  State.usage = await API.getUsage().catch(() => []);
  renderUsageDateSelector();
  renderUsageForm();
  await renderHeatmap();
  renderUsageHistory();
}

function renderUsageDateSelector() {
  const el = document.getElementById('usageDateInput');
  if (el && !el.value) el.value = State.usageDate;
}

function setUsageDate(d) {
  State.usageDate = d;
  renderUsageForm();
}

function renderUsageForm() {
  const el = document.getElementById('usageFormRows');
  if (!el) return;
  const existing = {};
  State.usage.filter(u => u.date === State.usageDate).forEach(u => { existing[u.device_id] = u.hours; });
  el.innerHTML = State.devices.map(d => `
    <div class="usage-device-row">
      <div class="dev-icon">${deviceIcon(d)}</div>
      <div class="dev-info">
        <div class="dev-name">${d.name}</div>
        <div class="dev-power">${d.power_w}W · tối đa ${d.max_daily_hours}h</div>
      </div>
      <div style="display:flex;align-items:center;gap:8px">
        <input type="number" class="form-input dev-input" id="usage_${d.id}"
          value="${existing[d.id] || ''}" min="0" max="${d.max_daily_hours}" step="0.5"
          placeholder="0" style="width:75px;text-align:center"
          oninput="updateUsagePreview('${d.id}', this.value, ${d.power_w})">
        <span style="font-size:12px;color:var(--text-muted)">giờ</span>
      </div>
      <div id="usage_preview_${d.id}" style="min-width:65px;text-align:right;font-size:12px;color:var(--text-muted)">
        ${existing[d.id] ? fmt.kwh(d.power_w * existing[d.id] / 1000) : '—'}
      </div>
    </div>`).join('');
  updateUsageTotals();
}

function updateUsagePreview(id, h, power) {
  const el = document.getElementById(`usage_preview_${id}`);
  if (el) el.textContent = h > 0 ? fmt.kwh(power * h / 1000) : '—';
  updateUsageTotals();
}

function updateUsageTotals() {
  let total = 0;
  State.devices.forEach(d => {
    const el = document.getElementById(`usage_${d.id}`);
    if (el && el.value > 0) total += d.power_w * parseFloat(el.value) / 1000;
  });
  const el = document.getElementById('usageTotalKwh');
  if (el) {
    el.textContent = fmt.kwh(total);
    el.style.color = total > State.config.daily_budget_kwh ? '#ef4444' : '#10b981';
  }
  const pctEl = document.getElementById('usagePct');
  if (pctEl) {
    const pct = State.config.daily_budget_kwh > 0 ? (total / State.config.daily_budget_kwh * 100) : 0;
    pctEl.textContent = `${pct.toFixed(1)}% ngân sách`;
    pctEl.style.color = pct > 100 ? '#ef4444' : '#64748b';
  }
}

async function saveAllUsage() {
  let saved = 0;
  for (const d of State.devices) {
    const el = document.getElementById(`usage_${d.id}`);
    if (!el) continue;
    const h = parseFloat(el.value) || 0;
    try {
      await API.saveUsage(d.id, State.usageDate, h);
      if (h > 0) saved++;
    } catch (e) { toast(e.message, 'error'); return; }
  }
  State.usage = await API.getUsage();
  toast(`Đã lưu nhật ký ngày ${formatDateVN(State.usageDate)} (${saved} thiết bị)`, 'success');
  renderHeatmap();
  renderUsageHistory();
}

async function renderHeatmap() {
  const data = await API.getHeatmap().catch(() => null);
  if (!data) return;
  State.heatmapResult = data;
  const el = document.getElementById('heatmapGrid');
  if (!el) return;
  const { days, max_kwh } = data;
  const maxV = max_kwh || 1;
  el.innerHTML = days.map(d => {
    const pct = d.kwh / maxV;
    const alpha = 0.1 + pct * 0.75;
    const bg = d.kwh === 0 ? 'rgba(255,255,255,0.04)' :
               pct > 0.8 ? `rgba(239,68,68,${alpha})` :
               pct > 0.5 ? `rgba(245,158,11,${alpha})` :
               `rgba(16,185,129,${alpha})`;
    return `<div class="heatmap-cell" style="background:${bg}"
      data-tooltip="${formatDateVN(d.date)}: ${d.kwh} kWh"></div>`;
  }).join('');
}

function renderUsageHistory() {
  const el = document.getElementById('usageHistoryTable');
  if (!el) return;
  const grouped = {};
  State.usage.forEach(u => { grouped[u.date] = grouped[u.date] || []; grouped[u.date].push(u); });
  const dates = Object.keys(grouped).sort().reverse().slice(0, 14);
  if (!dates.length) { el.innerHTML = '<div class="empty-state"><i class="bi bi-calendar-x"></i><p>Chưa có nhật ký nào</p></div>'; return; }
  const devMap = Object.fromEntries(State.devices.map(d => [d.id, d]));
  el.innerHTML = `<table class="data-table" style="width:100%">
    <thead><tr>
      <th>Ngày</th><th>Thiết bị sử dụng</th><th>Tổng kWh</th><th>Chi phí</th><th></th>
    </tr></thead>
    <tbody>${dates.map(date => {
      const entries = grouped[date];
      const totalKwh = entries.reduce((s,u) => s + (devMap[u.device_id]?.kwh(u.hours) || 0), 0);
      const names = entries.filter(u => u.hours > 0).map(u => devMap[u.device_id]?.name || u.device_id).join(', ');
      return `<tr>
        <td><span style="font-weight:600;color:var(--text-bright)">${formatDateVN(date)}</span></td>
        <td style="color:var(--text-muted);font-size:12px;max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${names||'—'}</td>
        <td><span style="font-weight:700;color:${totalKwh>State.config.daily_budget_kwh?'#ef4444':'#10b981'}">${totalKwh.toFixed(3)}</span> kWh</td>
        <td style="color:var(--text-muted)">${fmt.vnd(totalKwh * State.config.electricity_rate)}</td>
        <td><button class="btn btn-ghost btn-icon btn-sm" onclick="deleteDay('${date}')" title="Xóa ngày này"><i class="bi bi-trash3" style="color:#ef4444"></i></button></td>
      </tr>`;
    }).join('')}</tbody>
  </table>`;
}

async function deleteDay(date) {
  if (!confirm(`Xóa toàn bộ dữ liệu ngày ${formatDateVN(date)}?`)) return;
  try {
    await API.deleteDay(date);
    State.usage = await API.getUsage();
    toast(`Đã xóa dữ liệu ngày ${formatDateVN(date)}`, 'success');
    renderUsageHistory();
    renderHeatmap();
  } catch (e) { toast(e.message, 'error'); }
}

/* ─── OPTIMIZE TAB ────────────────────────────────────────────── */
async function runOptimize() {
  const budget = parseFloat(document.getElementById('optimizeBudget')?.value || State.optimizeBudget);
  State.optimizeBudget = budget;
  const btn = document.getElementById('btnOptimize');
  if (btn) { btn.disabled = true; btn.innerHTML = '<span class="spinner" style="width:18px;height:18px;border-width:2px"></span> Đang tính...'; }
  try {
    const result = await API.optimize(budget);
    State.optimizeResult = result;
    renderOptimizeResults(result);
    toast('Tối ưu hóa hoàn thành!', 'success');
  } catch (e) { toast(e.message, 'error'); }
  finally {
    if (btn) { btn.disabled = false; btn.innerHTML = '<i class="bi bi-lightning-fill"></i> Chạy tối ưu'; }
  }
}

function renderOptimizeResults(res) {
  const { dp, greedy, counterexample } = res;
  const dpWins = dp.total_comfort >= greedy.total_comfort;

  // DP panel
  const dpEl = document.getElementById('dpPanel');
  if (dpEl) {
    dpEl.innerHTML = `
      <div class="algo-header dp">
        <div>
          <div class="algo-title">🧮 DP — Group Knapsack ${dpWins ? '<span class="badge badge-green" style="margin-left:6px">THẮNG</span>' : ''}</div>
          <div class="algo-complexity">${dp.complexity}</div>
        </div>
        <div class="algo-score" style="color:#00d4ff">${dp.total_comfort.toFixed(1)} <span style="font-size:13px;color:var(--text-muted)">điểm</span></div>
      </div>
      <div class="algo-body">
        <div style="display:flex;gap:16px;margin-bottom:14px">
          <div style="text-align:center;flex:1;background:rgba(0,212,255,0.06);border-radius:10px;padding:10px;border:1px solid rgba(0,212,255,0.15)">
            <div style="font-size:20px;font-weight:800;color:#00d4ff">${dp.total_kwh}</div>
            <div style="font-size:11px;color:var(--text-muted)">kWh sử dụng</div>
          </div>
          <div style="text-align:center;flex:1;background:rgba(16,185,129,0.06);border-radius:10px;padding:10px;border:1px solid rgba(16,185,129,0.15)">
            <div style="font-size:20px;font-weight:800;color:#10b981">${fmt.vnd(dp.daily_cost)}</div>
            <div style="font-size:11px;color:var(--text-muted)">chi phí/ngày</div>
          </div>
          <div style="text-align:center;flex:1;background:rgba(124,58,237,0.06);border-radius:10px;padding:10px;border:1px solid rgba(124,58,237,0.15)">
            <div style="font-size:20px;font-weight:800;color:#a78bfa">${fmt.vnd(dp.monthly_cost)}</div>
            <div style="font-size:11px;color:var(--text-muted)">ước tính/tháng</div>
          </div>
        </div>
        ${renderScheduleItems(dp.schedule)}
      </div>`;
  }

  // Greedy panel
  const grEl = document.getElementById('greedyPanel');
  if (grEl) {
    grEl.innerHTML = `
      <div class="algo-header greedy">
        <div>
          <div class="algo-title">⚡ Greedy — Ưu tiên/Công suất ${!dpWins ? '<span class="badge badge-green" style="margin-left:6px">THẮNG</span>' : ''}</div>
          <div class="algo-complexity">${greedy.complexity}</div>
        </div>
        <div class="algo-score" style="color:#a78bfa">${greedy.total_comfort.toFixed(1)} <span style="font-size:13px;color:var(--text-muted)">điểm</span></div>
      </div>
      <div class="algo-body">
        <div style="display:flex;gap:16px;margin-bottom:14px">
          <div style="text-align:center;flex:1;background:rgba(124,58,237,0.06);border-radius:10px;padding:10px;border:1px solid rgba(124,58,237,0.15)">
            <div style="font-size:20px;font-weight:800;color:#a78bfa">${greedy.total_kwh}</div>
            <div style="font-size:11px;color:var(--text-muted)">kWh sử dụng</div>
          </div>
          <div style="text-align:center;flex:1;background:rgba(16,185,129,0.06);border-radius:10px;padding:10px;border:1px solid rgba(16,185,129,0.15)">
            <div style="font-size:20px;font-weight:800;color:#10b981">${fmt.vnd(greedy.daily_cost)}</div>
            <div style="font-size:11px;color:var(--text-muted)">chi phí/ngày</div>
          </div>
          <div style="text-align:center;flex:1;background:rgba(245,158,11,0.06);border-radius:10px;padding:10px;border:1px solid rgba(245,158,11,0.15)">
            <div style="font-size:20px;font-weight:800;color:#f59e0b">${fmt.vnd(greedy.monthly_cost)}</div>
            <div style="font-size:11px;color:var(--text-muted)">ước tính/tháng</div>
          </div>
        </div>
        ${renderScheduleItems(greedy.schedule)}
      </div>`;
  }

  // Chart
  renderOptimizeChart(dp, greedy);

  // Summary
  const diff = dp.total_comfort - greedy.total_comfort;
  const sumEl = document.getElementById('optimizeSummary');
  if (sumEl) {
    sumEl.innerHTML = `
      <div style="padding:16px;background:rgba(0,212,255,0.05);border:1px solid rgba(0,212,255,0.2);border-radius:12px;text-align:center">
        ${diff > 0
          ? `<div style="color:#10b981;font-weight:700;font-size:15px">✅ DP tốt hơn Greedy ${diff.toFixed(1)} điểm!</div>
             <div style="color:var(--text-muted);font-size:12px;margin-top:4px">DP đảm bảo lịch tối ưu toàn cục, Greedy có thể bỏ lỡ các thiết bị giá trị cao</div>`
          : diff < 0
            ? `<div style="color:#a78bfa;font-weight:700;font-size:15px">⚡ Greedy tốt hơn DP trong trường hợp này!</div>
               <div style="color:var(--text-muted);font-size:12px;margin-top:4px">Với ngân sách này, Greedy tìm được lịch tốt hơn</div>`
            : `<div style="color:#f59e0b;font-weight:700;font-size:15px">= Kết quả bằng nhau!</div>`}
      </div>`;
  }

  // Counterexample
  renderCounterexample(counterexample);
}

function renderScheduleItems(schedule) {
  if (!schedule.length) return '<div class="empty-state" style="padding:20px"><p>Không có thiết bị nào được chọn</p></div>';
  return schedule.map(s => `
    <div class="schedule-item">
      <span class="schedule-item-icon">${deviceIcon(s.device)}</span>
      <div style="flex:1">
        <div class="schedule-item-name">${s.device.name}</div>
        <div class="schedule-item-detail">${s.hours}h · ${s.kwh} kWh · ${s.device.power_w}W</div>
      </div>
      <div class="schedule-item-score" style="color:#f59e0b">${s.comfort.toFixed(1)} điểm</div>
    </div>`).join('');
}

function renderCounterexample(ce) {
  const el = document.getElementById('counterexampleBox');
  if (!el) return;
  const { dp, greedy, dp_wins } = ce;
  el.innerHTML = `
    <div class="counterex-title">
      <i class="bi bi-exclamation-triangle-fill"></i>
      Phản ví dụ — Tại sao Greedy không luôn tối ưu
    </div>
    <p style="font-size:13px;color:var(--text-muted);margin-bottom:4px">
      Budget = 0.30 kWh | Loa Bluetooth (200W, ưu=3, ratio=<strong style="color:#f59e0b">0.0150</strong>) vs Điều hòa nhỏ (300W, ưu=4, ratio=<strong style="color:#f59e0b">0.0133</strong>)
    </p>
    <p style="font-size:13px;color:var(--text-muted)">
      Greedy chọn Loa trước (ratio cao) → dùng 0.20kWh → còn 0.10kWh, không đủ cho Điều hòa (0.30kWh) → chỉ đạt 3 điểm
    </p>
    <div class="counterex-row">
      <div class="counterex-algo ${dp_wins ? 'winner' : 'loser'} ${dp_wins ? 'winner-glow' : ''}">
        <div style="font-weight:700;color:${dp_wins?'#10b981':'#ef4444'};margin-bottom:8px">
          ${dp_wins ? '✅' : '❌'} DP — ${dp.total_comfort} điểm
        </div>
        ${dp.schedule.map(s=>`<div style="font-size:12px;color:var(--text-muted)">• ${s.device.name}: ${s.hours}h = ${s.comfort} điểm</div>`).join('')||'<div style="color:var(--text-muted);font-size:12px">Không dùng thiết bị nào</div>'}
      </div>
      <div class="counterex-algo ${!dp_wins ? 'winner' : 'loser'}">
        <div style="font-weight:700;color:${!dp_wins?'#10b981':'#ef4444'};margin-bottom:8px">
          ${!dp_wins ? '✅' : '❌'} Greedy — ${greedy.total_comfort} điểm
        </div>
        ${greedy.schedule.map(s=>`<div style="font-size:12px;color:var(--text-muted)">• ${s.device.name}: ${s.hours}h = ${s.comfort} điểm</div>`).join('')||'<div style="color:var(--text-muted);font-size:12px">Không dùng thiết bị nào</div>'}
      </div>
    </div>
    <p style="font-size:12px;color:var(--text-muted);margin-top:10px;padding-top:10px;border-top:1px solid var(--border)">
      <strong style="color:#f59e0b">Kết luận:</strong> DP duyệt tất cả tổ hợp → đảm bảo tối ưu toàn cục. Greedy chỉ nhìn "hiệu quả cục bộ" → có thể sai.
    </p>`;
}

/* ─── PEAK TAB ────────────────────────────────────────────────── */
async function runPeakSchedule() {
  const budget = parseFloat(document.getElementById('peakBudget')?.value || 2);
  State.peakBudget = budget;
  const btn = document.getElementById('btnPeak');
  if (btn) { btn.disabled = true; btn.innerHTML = '<span class="spinner" style="width:18px;height:18px;border-width:2px"></span>'; }
  try {
    const result = await API.getPeak(budget);
    State.peakResult = result;
    renderPeakSchedule(result);
  } catch (e) { toast(e.message, 'error'); }
  finally { if (btn) { btn.disabled = false; btn.innerHTML = '<i class="bi bi-clock-fill"></i> Tạo lịch'; } }
}

function renderPeakSchedule(result) {
  const { schedule, peak_hours } = result;
  const peakSet = new Set(peak_hours);
  const el = document.getElementById('peakTimeline');
  if (!el) return;

  // Build hour → devices map
  const hourDevices = {};
  for (const [devId, item] of Object.entries(schedule)) {
    for (const slot of item.slots) {
      const h = slot.start;
      hourDevices[h] = hourDevices[h] || [];
      hourDevices[h].push(item.device.name);
    }
  }

  el.innerHTML = Array.from({length:24},(_,h) => {
    const isPeak = peakSet.has(h);
    const devs = hourDevices[h] || [];
    const hasDevice = devs.length > 0;
    const cls = hasDevice ? 'device-on' : isPeak ? 'peak' : 'off-peak';
    const title = hasDevice ? devs.join(', ') : isPeak ? 'Giờ cao điểm' : 'Giờ thấp điểm';
    return `<div class="timeline-hour ${cls}" title="${title}">
      <span>${h.toString().padStart(2,'0')}</span>
    </div>`;
  }).join('');

  // Device list
  const listEl = document.getElementById('peakDeviceList');
  if (!listEl) return;
  const entries = Object.values(schedule);
  if (!entries.length) { listEl.innerHTML = '<div class="empty-state"><p>Không có thiết bị nào</p></div>'; return; }
  listEl.innerHTML = entries.map(item => {
    const offSlots = item.slots.filter(s => !peakSet.has(s.start));
    const onSlots  = item.slots.filter(s => peakSet.has(s.start));
    return `
      <div class="schedule-item">
        <span class="schedule-item-icon">${deviceIcon(item.device)}</span>
        <div style="flex:1">
          <div class="schedule-item-name">${item.device.name}</div>
          <div class="schedule-item-detail">
            ${offSlots.length ? `<span style="color:#10b981">Thấp điểm: ${offSlots.map(s=>s.start+'h').join(', ')}</span>` : ''}
            ${onSlots.length  ? `<span style="color:#ef4444;margin-left:8px">Cao điểm: ${onSlots.map(s=>s.start+'h').join(', ')}</span>` : ''}
          </div>
        </div>
        <div style="text-align:right">
          <div style="font-size:13px;font-weight:700;color:#f59e0b">${item.hours}h</div>
          <div style="font-size:11px;color:var(--text-muted)">${item.kwh} kWh</div>
        </div>
      </div>`;
  }).join('');
}

/* ─── FORECAST TAB ────────────────────────────────────────────── */
async function renderForecastTab() {
  try {
    const data = await API.getForecast();
    State.forecastResult = data;
    renderForecastCards(data);
    if (data.months.length) renderForecastChart(data.months);
  } catch (e) { toast(e.message, 'error'); }
}

function renderForecastCards(data) {
  const el = document.getElementById('forecastSummary');
  if (!el) return;
  if (!data.avg_daily_kwh) {
    el.innerHTML = `<div class="empty-state"><i class="bi bi-graph-up"></i><h3>Chưa có dữ liệu</h3><p>Hãy ghi nhật ký ít nhất 1 ngày để xem dự báo</p></div>`;
    return;
  }
  el.innerHTML = `
    <div class="stats-strip">
      <div class="stats-strip-item">
        <div class="stats-strip-val" style="color:#00d4ff">${data.avg_daily_kwh}</div>
        <div class="stats-strip-lbl">kWh/ngày TB</div>
      </div>
      <div class="stats-strip-item">
        <div class="stats-strip-val" style="color:#a78bfa">${data.monthly_kwh}</div>
        <div class="stats-strip-lbl">kWh/tháng dự báo</div>
      </div>
      <div class="stats-strip-item">
        <div class="stats-strip-val" style="color:#f59e0b">${fmt.vnd(data.evn)}</div>
        <div class="stats-strip-lbl">Hóa đơn EVN</div>
      </div>
      <div class="stats-strip-item">
        <div class="stats-strip-val" style="color:#10b981">${fmt.vnd(data.saving)}</div>
        <div class="stats-strip-lbl">Có thể tiết kiệm</div>
      </div>
    </div>
    <div class="forecast-grid">
      ${data.months.slice(0,3).map(m=>`
        <div class="forecast-month">
          <div class="forecast-month-label">${m.label}</div>
          <div class="forecast-kwh">${m.kwh} kWh</div>
          <div class="forecast-vnd">${fmt.vndFull(m.evn)}</div>
        </div>`).join('')}
    </div>`;

  // Optimized comparison
  const optEl = document.getElementById('forecastOptimized');
  if (optEl && data.opt_monthly_kwh) {
    const save = data.saving;
    optEl.innerHTML = `
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
        <div style="padding:16px;border-radius:12px;background:rgba(239,68,68,0.06);border:1px solid rgba(239,68,68,0.2)">
          <div style="font-size:11px;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.5px;margin-bottom:6px">Hiện tại</div>
          <div style="font-size:22px;font-weight:800;color:#ef4444">${data.monthly_kwh} kWh</div>
          <div style="font-size:12px;color:var(--text-muted)">${fmt.vndFull(data.evn)}/tháng</div>
        </div>
        <div style="padding:16px;border-radius:12px;background:rgba(16,185,129,0.06);border:1px solid rgba(16,185,129,0.2)">
          <div style="font-size:11px;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.5px;margin-bottom:6px">Sau tối ưu DP</div>
          <div style="font-size:22px;font-weight:800;color:#10b981">${data.opt_monthly_kwh} kWh</div>
          <div style="font-size:12px;color:var(--text-muted)">${fmt.vndFull(data.opt_evn)}/tháng</div>
        </div>
      </div>
      ${save > 0 ? `<div style="text-align:center;margin-top:14px;padding:12px;background:rgba(16,185,129,0.06);border-radius:10px;border:1px solid rgba(16,185,129,0.2)">
        <span style="color:#10b981;font-weight:700;font-size:15px">💰 Tiết kiệm được ${fmt.vndFull(save)}/tháng nếu dùng lịch DP!</span>
      </div>` : ''}`;
  }
}

/* ─── SETTINGS TAB ────────────────────────────────────────────── */
async function renderSettingsTab() {
  const cfg = await API.getConfig().catch(() => State.config);
  State.config = cfg;
  const b = document.getElementById('cfgBudget');
  const r = document.getElementById('cfgRate');
  const p = document.getElementById('cfgPeakHours');
  if (b) b.value = cfg.daily_budget_kwh;
  if (r) r.value = cfg.electricity_rate;
  if (p) p.value = cfg.peak_hours.join(', ');
}

async function saveSettings(e) {
  e.preventDefault();
  const b  = parseFloat(document.getElementById('cfgBudget').value);
  const r  = parseFloat(document.getElementById('cfgRate').value);
  const ph = document.getElementById('cfgPeakHours').value
    .split(',').map(x => parseInt(x.trim())).filter(n => !isNaN(n) && n >= 0 && n <= 23);
  try {
    await API.saveConfig({ daily_budget_kwh: b, electricity_rate: r, peak_hours: ph });
    State.config = { daily_budget_kwh: b, electricity_rate: r, peak_hours: ph };
    toast('Đã lưu cài đặt', 'success');
  } catch (e) { toast(e.message, 'error'); }
}

async function calcEvnPreview() {
  const kwh = parseFloat(document.getElementById('evnKwh')?.value || 0);
  if (!kwh || kwh < 0) { toast('Nhập số kWh hợp lệ', 'warning'); return; }
  try {
    const data = await API.calcEvn(kwh);
    renderEvnResult(data);
    renderEvnChart(data.breakdown);
  } catch (e) { toast(e.message, 'error'); }
}

function renderEvnResult(data) {
  const el = document.getElementById('evnResult');
  if (!el) return;
  const tierColors = ['#10b981','#34d399','#f59e0b','#fb923c','#ef4444','#dc2626'];
  el.innerHTML = `
    <div style="text-align:center;padding:16px 0;border-bottom:1px solid var(--border)">
      <div style="font-size:28px;font-weight:800;color:#f59e0b">${fmt.vndFull(data.total)}</div>
      <div style="font-size:13px;color:var(--text-muted)">cho ${data.kwh} kWh/tháng</div>
    </div>
    ${data.breakdown.map((b,i) => `
      <div class="evn-tier">
        <div class="evn-tier-num" style="background:${tierColors[i]}22;color:${tierColors[i]}">${b.bac}</div>
        <div style="flex:1">
          <div style="font-size:12px;color:var(--text-bright);margin-bottom:4px">${b.kwh} kWh × ${b.rate.toLocaleString()} ₫</div>
          <div class="evn-tier-bar"><div class="evn-tier-fill" style="width:${(b.cost/data.total*100).toFixed(1)}%;background:${tierColors[i]}"></div></div>
        </div>
        <div style="font-size:13px;font-weight:700;color:${tierColors[i]};min-width:80px;text-align:right">${fmt.vndFull(b.cost)}</div>
      </div>`).join('')}`;
}

/* ─── SLIDER DISPLAY ──────────────────────────────────────────── */
function updateSlider(inputId, displayId, unit) {
  const v = document.getElementById(inputId)?.value;
  const el = document.getElementById(displayId);
  if (el) el.textContent = v + (unit || '');
}

/* ─── INIT ────────────────────────────────────────────────────── */
async function init() {
  try {
    [State.devices, State.config] = await Promise.all([API.getDevices(), API.getConfig()]);
  } catch (e) { toast('Không thể kết nối server', 'error'); }

  // Tab navigation
  document.querySelectorAll('[data-tab]').forEach(btn => {
    btn.addEventListener('click', () => switchTab(btn.dataset.tab));
  });

  // Usage date
  const dateInput = document.getElementById('usageDateInput');
  if (dateInput) {
    dateInput.value = State.usageDate;
    dateInput.addEventListener('change', e => setUsageDate(e.target.value));
  }

  // Optimize budget slider
  const optSlider = document.getElementById('optimizeBudget');
  if (optSlider) {
    optSlider.value = State.config.daily_budget_kwh;
    optSlider.addEventListener('input', e => {
      updateSlider('optimizeBudget', 'optimizeBudgetDisplay', ' kWh');
      State.optimizeBudget = parseFloat(e.target.value);
    });
    updateSlider('optimizeBudget', 'optimizeBudgetDisplay', ' kWh');
  }

  // Peak budget slider
  const peakSlider = document.getElementById('peakBudget');
  if (peakSlider) {
    peakSlider.value = State.config.daily_budget_kwh;
    peakSlider.addEventListener('input', () => updateSlider('peakBudget', 'peakBudgetDisplay', ' kWh'));
    updateSlider('peakBudget', 'peakBudgetDisplay', ' kWh');
  }

  // EVN input
  const evnInput = document.getElementById('evnKwh');
  if (evnInput) evnInput.addEventListener('keydown', e => { if (e.key==='Enter') calcEvnPreview(); });

  // Add device form
  const addForm = document.getElementById('addDeviceForm');
  if (addForm) addForm.addEventListener('submit', submitAddDevice);

  // Settings form
  const cfgForm = document.getElementById('settingsForm');
  if (cfgForm) cfgForm.addEventListener('submit', saveSettings);

  // Click outside modal
  document.querySelectorAll('.modal-backdrop').forEach(el => {
    el.addEventListener('click', e => { if (e.target === el) el.classList.remove('show'); });
  });

  // Load dashboard
  switchTab('dashboard');
}

document.addEventListener('DOMContentLoaded', init);
