/* ════════════════════════════════════════════════════════════════
   Main App — Trạng thái ứng dụng, Render giao diện, Xử lý sự kiện
   ════════════════════════════════════════════════════════════════ */

/* ─── Trạng thái toàn cục của ứng dụng ──────────────────────── */
const State = {                                // object lưu trạng thái ứng dụng (nguồn sự thật duy nhất)
  devices:        [],                          // danh sách thiết bị hiện tại (mảng Device objects)
  usage:          [],                          // danh sách nhật ký sử dụng (mảng UsageEntry objects)
  config:         { daily_budget_kwh: 2.0, electricity_rate: 3500, peak_hours: [17,18,19,20,21] },  // cài đặt mặc định
  stats:          null,                        // dữ liệu thống kê từ API (null nếu chưa tải)
  optimizeResult: null,                        // kết quả tối ưu DP vs Greedy (null nếu chưa chạy)
  peakResult:     null,                        // kết quả lịch cao điểm (null nếu chưa chạy)
  forecastResult: null,                        // kết quả dự báo (null nếu chưa tải)
  heatmapResult:  null,                        // dữ liệu heatmap 30 ngày (null nếu chưa tải)
  activeTab:      'dashboard',                 // tab đang hiển thị (mặc định là dashboard)
  usageDate:      todayStr(),                  // ngày đang ghi nhật ký (mặc định hôm nay)
  optimizeBudget: 2.0,                         // ngân sách cho tối ưu hóa (kWh)
  peakBudget:     2.0,                         // ngân sách cho lịch cao điểm (kWh)
  filterCategory: 'all',                       // bộ lọc danh mục thiết bị đang chọn
};

/* ─── Điều hướng Tab ─────────────────────────────────────────── */
function switchTab(tab) {                      // hàm chuyển sang tab được chỉ định
  State.activeTab = tab;                       // cập nhật trạng thái tab đang hoạt động
  document.querySelectorAll('.tab-pane').forEach(el => el.classList.remove('active'));    // ẩn tất cả tab content
  document.querySelectorAll('.nav-tab-btn').forEach(el => el.classList.remove('active')); // bỏ active tất cả nút nav
  const pane = document.getElementById('tab-' + tab);  // lấy phần tử tab content tương ứng
  if (pane) pane.classList.add('active');     // hiện tab content được chọn
  document.querySelectorAll(`[data-tab="${tab}"]`).forEach(el => el.classList.add('active'));  // active nút nav tương ứng
  onTabActivated(tab);                         // gọi hàm load dữ liệu cho tab vừa mở
}

function onTabActivated(tab) {                 // hàm xử lý khi tab được kích hoạt: load dữ liệu phù hợp
  if (tab === 'dashboard') renderDashboard();  // tab dashboard: tải thống kê và vẽ biểu đồ
  else if (tab === 'devices')  renderDevicesTab();   // tab thiết bị: tải danh sách thiết bị
  else if (tab === 'usage')    renderUsageTab();     // tab nhật ký: tải nhật ký và heatmap
  else if (tab === 'forecast') renderForecastTab();  // tab dự báo: tải dự báo 6 tháng
  else if (tab === 'settings') renderSettingsTab();  // tab cài đặt: tải config hiện tại
}

/* ─── TAB DASHBOARD ──────────────────────────────────────────── */
async function renderDashboard() {             // hàm chính render toàn bộ dashboard
  try {
    const stats = await API.getStats();        // gọi API lấy thống kê tổng hợp từ server
    State.stats = stats;                       // lưu vào State để các hàm khác dùng được
    renderKPIs(stats);                         // cập nhật 4 thẻ KPI (hôm nay, trung bình, tháng, thiết bị)
    renderDailyChart(stats.daily);             // vẽ biểu đồ đường 14 ngày
    renderDonutChart(stats.by_device);         // vẽ biểu đồ donut theo thiết bị
    renderTips(stats.tips);                    // hiện gợi ý tiết kiệm điện
    renderBudgetGauge(stats.today_kwh, stats.budget);  // vẽ đồng hồ tròn ngân sách
    renderTopDevices(stats.by_device.slice(0, 5));     // hiện top 5 thiết bị tốn điện nhất
  } catch (e) { toast(e.message, 'error'); }  // nếu lỗi: hiện toast thông báo lỗi
}

function renderKPIs(s) {                       // cập nhật 4 thẻ KPI với dữ liệu thống kê s
  const pct    = s.budget > 0 ? (s.today_kwh / s.budget * 100) : 0;  // phần trăm ngân sách đã dùng hôm nay
  const isOver = s.today_kwh > s.budget;      // true nếu đã vượt ngân sách

  setKPI('kpiToday',                          // cập nhật thẻ "Hôm nay"
    fmt.kwh(s.today_kwh),                     // giá trị: kWh hôm nay
    `Ngân sách còn: ${fmt.kwh(s.budget_rem)}`, // phụ đề: ngân sách còn lại
    isOver ? 'red' : 'blue');                 // màu: đỏ nếu vượt, xanh nếu trong ngân sách

  setKPI('kpiAvg',                            // cập nhật thẻ "Trung bình/ngày"
    fmt.kwhS(s.avg_kwh),                      // giá trị: kWh trung bình mỗi ngày
    `Trung bình ${s.n_days} ngày ghi nhận`,   // phụ đề: số ngày đã ghi
    'purple');                                 // màu: tím

  setKPI('kpiMonthly',                        // cập nhật thẻ "Ước tính/tháng"
    `${(s.monthly_kwh || 0).toFixed(0)} kWh`, // giá trị: kWh/tháng ước tính
    `≈ ${fmt.vnd(s.est_evn)}/tháng (EVN)`,   // phụ đề: tiền điện EVN ước tính
    'green');                                  // màu: xanh lá

  setKPI('kpiDevices',                        // cập nhật thẻ "Thiết bị"
    State.devices.length.toString(),           // giá trị: tổng số thiết bị
    `${State.devices.filter(d=>d.priority>=4).length} thiết bị ưu tiên cao`,  // phụ đề: số thiết bị ưu tiên 4-5
    'amber');                                  // màu: vàng cam

  const budgetBar = document.getElementById('budgetBarFill');  // thanh tiến độ ngân sách
  const budgetPct = Math.min(100, pct);       // giới hạn tối đa 100% (tránh tràn thanh)
  if (budgetBar) {
    budgetBar.style.width = budgetPct + '%';  // đặt chiều rộng thanh theo % đã dùng
    budgetBar.style.background = isOver                    // đổi màu thanh theo mức sử dụng
      ? 'linear-gradient(90deg, #ef4444, #dc2626)'        // vượt ngân sách: đỏ đậm
      : pct > 75
        ? 'linear-gradient(90deg, #f59e0b, #d97706)'      // sắp hết: vàng
        : 'linear-gradient(90deg, #00d4ff, #0088cc)';     // an toàn: xanh cyan
  }

  const budgetDisplay = document.getElementById('budgetDisplay');  // text hiện ngân sách
  if (budgetDisplay) {
    budgetDisplay.dataset.budget = s.budget;  // lưu giá trị ngân sách vào data attribute (charts.js đọc)
    budgetDisplay.textContent = `${s.today_kwh.toFixed(3)} / ${s.budget} kWh (${pct.toFixed(1)}%)`;  // "0.500 / 2.0 kWh (25.0%)"
    budgetDisplay.style.color = isOver ? '#ef4444' : pct > 75 ? '#f59e0b' : '#10b981';  // màu chữ theo mức
  }
}

function setKPI(id, value, sub, color) {       // hàm cập nhật nội dung 1 thẻ KPI
  const el = document.getElementById(id);      // lấy phần tử thẻ KPI
  if (!el) return;                             // bỏ qua nếu không tìm thấy
  el.querySelector('.kpi-value').innerHTML = value;   // đặt giá trị chính (hỗ trợ HTML)
  el.querySelector('.kpi-sub').textContent = sub;     // đặt phụ đề (text thuần)
  el.className = `kpi-card ${color}`;          // đặt class màu (kpi-card blue/purple/green/amber/red)
}

function renderBudgetGauge(used, total) {      // vẽ đồng hồ tròn SVG thể hiện % ngân sách đã dùng
  const el = document.getElementById('gaugeWrap');  // lấy container
  if (!el) return;
  const pct    = total > 0 ? Math.min(1, used / total) : 0;  // tỉ lệ đã dùng (0–1), tối đa 1
  const r      = 44;                           // bán kính vòng tròn SVG (px)
  const circ   = 2 * Math.PI * r;             // chu vi vòng tròn (dùng để tính stroke-dasharray)
  const offset = circ * (1 - pct);            // phần chưa tô = chu vi × (1 - tỉ lệ) → tạo hiệu ứng đồng hồ
  const color  = pct > 1 ? '#ef4444' : pct > 0.75 ? '#f59e0b' : '#10b981';  // màu: đỏ/vàng/xanh
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

function renderTips(tips) {                    // hiện danh sách gợi ý tiết kiệm điện
  const el = document.getElementById('tipsContainer');
  if (!el) return;
  if (!tips || !tips.length) {               // nếu không có gợi ý nào
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
    </div>`).join('');                         // join('') ghép các phần tử HTML thành một chuỗi
}

function renderTopDevices(byDev) {             // hiện top thiết bị tốn điện nhất với thanh tiến độ
  const el = document.getElementById('topDevicesContainer');
  if (!el) return;
  if (!byDev.length) {
    el.innerHTML = '<div class="empty-state"><i class="bi bi-bar-chart"></i><p>Chưa có dữ liệu sử dụng</p></div>';
    return;
  }
  const maxKwh = byDev[0]?.kwh || 1;         // kWh lớn nhất để chuẩn hóa thanh tiến độ (tránh chia 0)
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

/* ─── TAB THIẾT BỊ ───────────────────────────────────────────── */
async function renderDevicesTab() {            // hàm render toàn bộ tab Thiết bị
  const devs = await API.getDevices().catch(e => { toast(e.message,'error'); return []; });  // tải thiết bị, nếu lỗi trả mảng rỗng
  State.devices = devs;                        // cập nhật State
  renderDeviceFilter();                        // render bộ lọc danh mục
  renderDeviceGrid(devs);                      // render lưới thẻ thiết bị
  renderCategoryChart(State.stats?.by_device || []);  // vẽ biểu đồ phân loại (nếu có stats)
}

function renderDeviceFilter() {                // render các nút lọc theo danh mục
  const el = document.getElementById('deviceFilterBtns');
  if (!el) return;
  const cats = ['all', ...new Set(State.devices.map(d => d.category))];  // ['all', 'cooling', 'lighting', ...]
  el.innerHTML = cats.map(c => `
    <button class="period-btn ${c===State.filterCategory?'active':''}" onclick="filterDevices('${c}')">
      ${c === 'all' ? '🔌 Tất cả' : `${CATEGORY_META[c]?.icon||'•'} ${catLabel(c)}`}
    </button>`).join('');
}

function filterDevices(cat) {                  // hàm lọc thiết bị theo danh mục được chọn
  State.filterCategory = cat;                  // lưu bộ lọc hiện tại
  renderDeviceFilter();                        // render lại nút lọc (để cập nhật active)
  const filtered = cat === 'all'              // lọc danh sách thiết bị
    ? State.devices                           // 'all': hiện tất cả
    : State.devices.filter(d => d.category === cat);  // khác: chỉ hiện đúng danh mục
  renderDeviceGrid(filtered);                  // render lưới thiết bị đã lọc
}

function renderDeviceGrid(devs) {              // render lưới thẻ thiết bị
  const el = document.getElementById('devicesGrid');
  if (!el) return;
  if (!devs.length) {
    el.innerHTML = '<div class="empty-state" style="grid-column:1/-1"><i class="bi bi-plug"></i><h3>Không có thiết bị</h3><p>Thêm thiết bị mới bên dưới</p></div>';
    return;
  }
  el.innerHTML = devs.map(d => {
    const icon   = deviceIcon(d);              // lấy emoji icon cho thiết bị
    const bgCls  = `cat-bg-${d.category}`;    // class nền màu theo danh mục
    const clrCls = `cat-${d.category}`;       // class màu chữ theo danh mục
    const stars  = Array.from({length:5},(_,i) =>  // tạo 5 ô nhỏ đánh dấu độ ưu tiên
      `<div class="priority-star" style="background:${i<d.priority?'#f59e0b':'rgba(255,255,255,0.08)'}"></div>`
    ).join('');                                // ô vàng nếu i < priority, xám nếu ngược lại
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

async function deleteDevice(id) {              // hàm xóa thiết bị theo ID
  if (!confirm('Xóa thiết bị này?')) return;  // hỏi xác nhận trước khi xóa
  try {
    await API.deleteDevice(id);               // gọi API xóa
    toast('Đã xóa thiết bị', 'success');     // thông báo thành công
    renderDevicesTab();                        // render lại tab
  } catch (e) { toast(e.message, 'error'); }  // thông báo lỗi
}

async function resetDevices() {               // hàm khôi phục danh sách thiết bị về mặc định
  if (!confirm('Khôi phục về danh sách mặc định?')) return;
  try {
    await API.resetDevices();                 // gọi API reset
    toast('Đã khôi phục danh sách thiết bị', 'success');
    renderDevicesTab();
  } catch (e) { toast(e.message, 'error'); }
}

function openAddDeviceModal() {               // hiện modal thêm thiết bị mới
  document.getElementById('addDeviceModal').classList.add('show');  // thêm class 'show' → modal hiện ra
}

function closeAddDeviceModal() {              // ẩn modal thêm thiết bị
  document.getElementById('addDeviceModal').classList.remove('show');  // xóa class 'show' → modal ẩn
  document.getElementById('addDeviceForm').reset();  // xóa dữ liệu đã nhập trong form
}

async function submitAddDevice(e) {           // xử lý submit form thêm thiết bị
  e.preventDefault();                         // ngăn form reload trang (hành vi mặc định)
  const f = e.target;                         // lấy phần tử form
  const dev = {                               // tạo object thiết bị từ dữ liệu form
    id:              f.devId.value.trim().toLowerCase().replace(/\s+/g,'_'),  // ID: chữ thường, thay space bằng _
    name:            f.devName.value.trim(),  // tên thiết bị (bỏ khoảng trắng thừa)
    power_w:         parseInt(f.devPower.value),   // công suất: parse thành số nguyên
    priority:        parseInt(f.devPriority.value), // ưu tiên: parse thành số nguyên
    max_daily_hours: parseFloat(f.devHours.value),  // giờ tối đa: parse thành số thực
    category:        f.devCategory.value      // danh mục: lấy giá trị select
  };
  if (!dev.id || !dev.name) { toast('Vui lòng điền đầy đủ', 'warning'); return; }  // kiểm tra bắt buộc
  try {
    await API.addDevice(dev);                 // gọi API thêm thiết bị
    toast(`Đã thêm ${dev.name}`, 'success'); // thông báo thành công
    closeAddDeviceModal();                    // đóng modal
    renderDevicesTab();                       // render lại tab
  } catch (e) { toast(e.message, 'error'); }
}

/* ─── TAB NHẬT KÝ ────────────────────────────────────────────── */
async function renderUsageTab() {             // hàm render toàn bộ tab Nhật ký
  State.usage = await API.getUsage().catch(() => []);  // tải nhật ký, trả mảng rỗng nếu lỗi
  renderUsageDateSelector();                  // cập nhật ô chọn ngày
  renderUsageForm();                          // render form nhập giờ cho từng thiết bị
  await renderHeatmap();                      // vẽ heatmap 30 ngày
  renderUsageHistory();                       // hiện bảng lịch sử 14 ngày
}

function renderUsageDateSelector() {          // đặt giá trị mặc định cho ô chọn ngày
  const el = document.getElementById('usageDateInput');
  if (el && !el.value) el.value = State.usageDate;  // chỉ đặt nếu ô chưa có giá trị
}

function setUsageDate(d) {                    // hàm đổi ngày đang ghi nhật ký
  State.usageDate = d;                        // cập nhật State
  renderUsageForm();                          // render lại form với dữ liệu của ngày mới
}

function renderUsageForm() {                  // render form nhập giờ sử dụng từng thiết bị
  const el = document.getElementById('usageFormRows');
  if (!el) return;
  const existing = {};                        // object lưu số giờ đã có cho ngày này
  State.usage
    .filter(u => u.date === State.usageDate) // lọc nhật ký của ngày đang chọn
    .forEach(u => { existing[u.device_id] = u.hours; });  // map device_id → số giờ

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
  updateUsageTotals();                        // tính và hiện tổng kWh ngay khi render
}

function updateUsagePreview(id, h, power) {  // cập nhật preview kWh khi thay đổi số giờ
  const el = document.getElementById(`usage_preview_${id}`);  // lấy phần tử hiện kWh preview
  if (el) el.textContent = h > 0 ? fmt.kwh(power * h / 1000) : '—';  // tính và hiện kWh, hoặc '—' nếu 0
  updateUsageTotals();                        // cập nhật tổng ngay
}

function updateUsageTotals() {               // tính và hiện tổng kWh + % ngân sách của tất cả thiết bị
  let total = 0;                             // tổng kWh
  State.devices.forEach(d => {
    const el = document.getElementById(`usage_${d.id}`);  // ô nhập giờ của thiết bị d
    if (el && el.value > 0) total += d.power_w * parseFloat(el.value) / 1000;  // cộng kWh vào tổng
  });
  const el = document.getElementById('usageTotalKwh');
  if (el) {
    el.textContent  = fmt.kwh(total);        // hiện tổng kWh
    el.style.color  = total > State.config.daily_budget_kwh ? '#ef4444' : '#10b981';  // đỏ nếu vượt ngân sách
  }
  const pctEl = document.getElementById('usagePct');
  if (pctEl) {
    const pct = State.config.daily_budget_kwh > 0 ? (total / State.config.daily_budget_kwh * 100) : 0;  // % ngân sách
    pctEl.textContent  = `${pct.toFixed(1)}% ngân sách`;
    pctEl.style.color  = pct > 100 ? '#ef4444' : '#64748b';  // đỏ nếu vượt 100%
  }
}

async function saveAllUsage() {              // lưu nhật ký của tất cả thiết bị cho ngày hiện tại
  let saved = 0;                            // đếm số thiết bị đã lưu thành công
  for (const d of State.devices) {         // duyệt từng thiết bị
    const el = document.getElementById(`usage_${d.id}`);  // lấy ô nhập giờ
    if (!el) continue;                     // bỏ qua nếu không tìm thấy ô nhập
    const h = parseFloat(el.value) || 0;  // đọc số giờ (0 nếu trống)
    try {
      await API.saveUsage(d.id, State.usageDate, h);  // gọi API lưu (kể cả h=0 để xóa dữ liệu cũ)
      if (h > 0) saved++;                  // đếm nếu có sử dụng
    } catch (e) { toast(e.message, 'error'); return; }  // dừng nếu có lỗi
  }
  State.usage = await API.getUsage();      // tải lại nhật ký để cập nhật State
  toast(`Đã lưu nhật ký ngày ${formatDateVN(State.usageDate)} (${saved} thiết bị)`, 'success');
  renderHeatmap();                          // cập nhật heatmap với dữ liệu mới
  renderUsageHistory();                     // cập nhật bảng lịch sử
}

async function renderHeatmap() {            // vẽ heatmap 30 ngày màu sắc
  const data = await API.getHeatmap().catch(() => null);  // tải dữ liệu, null nếu lỗi
  if (!data) return;                        // thoát nếu không có dữ liệu
  State.heatmapResult = data;               // lưu vào State
  const el = document.getElementById('heatmapGrid');
  if (!el) return;
  const { days, max_kwh } = data;           // destructure: mảng ngày và giá trị max
  const maxV = max_kwh || 1;               // tránh chia cho 0 nếu chưa có dữ liệu
  el.innerHTML = days.map(d => {
    const pct   = d.kwh / maxV;            // tỉ lệ so với ngày có kWh cao nhất (0–1)
    const alpha = 0.1 + pct * 0.75;       // độ đục màu: 0.1 (rỗng) đến 0.85 (tối đa)
    const bg = d.kwh === 0 ? 'rgba(255,255,255,0.04)'          // 0 kWh: xám rất mờ
             : pct > 0.8   ? `rgba(239,68,68,${alpha})`        // >80% max: đỏ
             : pct > 0.5   ? `rgba(245,158,11,${alpha})`       // >50% max: vàng
                           : `rgba(16,185,129,${alpha})`;      // ≤50% max: xanh lá
    return `<div class="heatmap-cell" style="background:${bg}"
      data-tooltip="${formatDateVN(d.date)}: ${d.kwh} kWh"></div>`;  // tooltip hiện ngày và kWh
  }).join('');
}

function renderUsageHistory() {             // render bảng lịch sử sử dụng 14 ngày gần nhất
  const el = document.getElementById('usageHistoryTable');
  if (!el) return;
  const grouped = {};                       // gom nhóm nhật ký theo ngày
  State.usage.forEach(u => {
    grouped[u.date] = grouped[u.date] || []; // tạo mảng cho ngày nếu chưa có
    grouped[u.date].push(u);                // thêm entry vào nhóm ngày
  });
  const dates = Object.keys(grouped).sort().reverse().slice(0, 14);  // lấy 14 ngày mới nhất, sắp xếp giảm dần
  if (!dates.length) {
    el.innerHTML = '<div class="empty-state"><i class="bi bi-calendar-x"></i><p>Chưa có nhật ký nào</p></div>';
    return;
  }
  const devMap = Object.fromEntries(State.devices.map(d => [d.id, d]));  // dict tra cứu nhanh thiết bị theo ID
  el.innerHTML = `<table class="data-table" style="width:100%">
    <thead><tr>
      <th>Ngày</th><th>Thiết bị sử dụng</th><th>Tổng kWh</th><th>Chi phí</th><th></th>
    </tr></thead>
    <tbody>${dates.map(date => {
      const entries  = grouped[date];        // các entry của ngày này
      const totalKwh = entries.reduce((s,u) => s + (devMap[u.device_id]?.kwh(u.hours) || 0), 0);  // tổng kWh ngày
      const names    = entries.filter(u => u.hours > 0).map(u => devMap[u.device_id]?.name || u.device_id).join(', ');  // tên các thiết bị đã dùng
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

async function deleteDay(date) {            // xóa toàn bộ nhật ký của 1 ngày
  if (!confirm(`Xóa toàn bộ dữ liệu ngày ${formatDateVN(date)}?`)) return;
  try {
    await API.deleteDay(date);              // gọi API xóa
    State.usage = await API.getUsage();    // tải lại nhật ký
    toast(`Đã xóa dữ liệu ngày ${formatDateVN(date)}`, 'success');
    renderUsageHistory();                   // cập nhật bảng lịch sử
    renderHeatmap();                        // cập nhật heatmap
  } catch (e) { toast(e.message, 'error'); }
}

/* ─── TAB TỐI ƯU ─────────────────────────────────────────────── */
async function runOptimize() {              // hàm chạy so sánh DP vs Greedy
  const budget = parseFloat(document.getElementById('optimizeBudget')?.value || State.optimizeBudget);  // đọc ngân sách từ slider
  State.optimizeBudget = budget;            // lưu vào State
  const btn = document.getElementById('btnOptimize');
  if (btn) { btn.disabled = true; btn.innerHTML = '<span class="spinner" style="width:18px;height:18px;border-width:2px"></span> Đang tính...'; }  // hiện spinner trong khi chạy
  try {
    const result = await API.optimize(budget);  // gọi API chạy DP + Greedy
    State.optimizeResult = result;           // lưu kết quả vào State
    renderOptimizeResults(result);           // render kết quả lên giao diện
    toast('Tối ưu hóa hoàn thành!', 'success');
  } catch (e) { toast(e.message, 'error'); }
  finally {
    if (btn) { btn.disabled = false; btn.innerHTML = '<i class="bi bi-lightning-fill"></i> Chạy tối ưu'; }  // khôi phục nút
  }
}

function renderOptimizeResults(res) {       // render kết quả so sánh DP vs Greedy
  const { dp, greedy, counterexample } = res;  // destructure kết quả
  const dpWins = dp.total_comfort >= greedy.total_comfort;  // true nếu DP có điểm cao hơn hoặc bằng

  // Render panel kết quả DP
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

  // Render panel kết quả Greedy
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

  renderOptimizeChart(dp, greedy);          // vẽ biểu đồ cột so sánh điểm từng thiết bị

  // Render tóm tắt so sánh
  const diff  = dp.total_comfort - greedy.total_comfort;  // chênh lệch điểm DP - Greedy
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

  renderCounterexample(counterexample);     // render phần phản ví dụ Loa vs Điều hòa
}

function renderScheduleItems(schedule) {   // render danh sách thiết bị trong lịch của 1 thuật toán
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

function renderCounterexample(ce) {        // render phản ví dụ chứng minh Greedy không luôn tối ưu
  const el = document.getElementById('counterexampleBox');
  if (!el) return;
  const { dp, greedy, dp_wins } = ce;     // destructure: kết quả DP, Greedy và người thắng
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

/* ─── TAB LỊCH CAO ĐIỂM ──────────────────────────────────────── */
async function runPeakSchedule() {          // hàm tạo lịch tránh giờ cao điểm
  const budget = parseFloat(document.getElementById('peakBudget')?.value || 2);  // đọc ngân sách từ slider
  State.peakBudget = budget;                // lưu vào State
  const btn = document.getElementById('btnPeak');
  if (btn) { btn.disabled = true; btn.innerHTML = '<span class="spinner" style="width:18px;height:18px;border-width:2px"></span>'; }  // hiện spinner
  try {
    const result = await API.getPeak(budget);  // gọi API tạo lịch
    State.peakResult = result;               // lưu kết quả
    renderPeakSchedule(result);              // render lên giao diện
  } catch (e) { toast(e.message, 'error'); }
  finally { if (btn) { btn.disabled = false; btn.innerHTML = '<i class="bi bi-clock-fill"></i> Tạo lịch'; } }
}

function renderPeakSchedule(result) {       // render lịch 24h và danh sách thiết bị theo giờ
  const { schedule, peak_hours } = result;  // destructure kết quả
  const peakSet = new Set(peak_hours);      // set để tra cứu O(1) giờ cao điểm
  const el = document.getElementById('peakTimeline');
  if (!el) return;

  const hourDevices = {};                   // map giờ → danh sách tên thiết bị đang chạy
  for (const [devId, item] of Object.entries(schedule)) {  // duyệt từng thiết bị trong lịch
    for (const slot of item.slots) {        // duyệt từng slot giờ của thiết bị
      const h = slot.start;                 // giờ bắt đầu slot
      hourDevices[h] = hourDevices[h] || []; // tạo mảng cho giờ nếu chưa có
      hourDevices[h].push(item.device.name); // thêm tên thiết bị vào giờ đó
    }
  }

  el.innerHTML = Array.from({length:24},(_,h) => {  // tạo 24 cột giờ (0h đến 23h)
    const isPeak    = peakSet.has(h);       // true nếu giờ h là cao điểm
    const devs      = hourDevices[h] || []; // danh sách thiết bị chạy lúc h
    const hasDevice = devs.length > 0;      // true nếu có thiết bị nào đó đang chạy
    const cls   = hasDevice ? 'device-on' : isPeak ? 'peak' : 'off-peak';  // class màu cột
    const title = hasDevice ? devs.join(', ') : isPeak ? 'Giờ cao điểm' : 'Giờ thấp điểm';  // tooltip
    return `<div class="timeline-hour ${cls}" title="${title}">
      <span>${h.toString().padStart(2,'0')}</span>
    </div>`;
  }).join('');

  const listEl = document.getElementById('peakDeviceList');  // container danh sách thiết bị
  if (!listEl) return;
  const entries = Object.values(schedule);  // mảng thiết bị từ object schedule
  if (!entries.length) { listEl.innerHTML = '<div class="empty-state"><p>Không có thiết bị nào</p></div>'; return; }
  listEl.innerHTML = entries.map(item => {
    const offSlots = item.slots.filter(s => !peakSet.has(s.start));  // các slot giờ thấp điểm
    const onSlots  = item.slots.filter(s =>  peakSet.has(s.start));  // các slot giờ cao điểm
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

/* ─── TAB DỰ BÁO ─────────────────────────────────────────────── */
async function renderForecastTab() {        // hàm render toàn bộ tab Dự báo
  try {
    const data = await API.getForecast();   // gọi API lấy dự báo 6 tháng
    State.forecastResult = data;            // lưu kết quả
    renderForecastCards(data);              // render thẻ tóm tắt và so sánh
    if (data.months.length) renderForecastChart(data.months);  // vẽ biểu đồ nếu có dữ liệu
  } catch (e) { toast(e.message, 'error'); }
}

function renderForecastCards(data) {        // render các thẻ và bảng tóm tắt dự báo
  const el = document.getElementById('forecastSummary');
  if (!el) return;
  if (!data.avg_daily_kwh) {               // nếu chưa có dữ liệu nhật ký
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

  const optEl = document.getElementById('forecastOptimized');  // container so sánh hiện tại vs tối ưu
  if (optEl && data.opt_monthly_kwh) {
    const save = data.saving;               // số tiền tiết kiệm được nếu dùng lịch DP
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

/* ─── TAB CÀI ĐẶT ────────────────────────────────────────────── */
async function renderSettingsTab() {        // hàm render tab Cài đặt với giá trị hiện tại
  const cfg = await API.getConfig().catch(() => State.config);  // tải config, dùng State nếu lỗi
  State.config = cfg;                       // cập nhật State
  const b = document.getElementById('cfgBudget');    // ô ngân sách
  const r = document.getElementById('cfgRate');      // ô giá điện
  const p = document.getElementById('cfgPeakHours'); // ô giờ cao điểm
  if (b) b.value = cfg.daily_budget_kwh;   // điền giá trị hiện tại vào ô ngân sách
  if (r) r.value = cfg.electricity_rate;   // điền giá điện hiện tại
  if (p) p.value = cfg.peak_hours.join(', ');  // điền giờ cao điểm dạng "17, 18, 19, 20, 21"
}

async function saveSettings(e) {           // xử lý submit form cài đặt
  e.preventDefault();                      // ngăn reload trang
  const b  = parseFloat(document.getElementById('cfgBudget').value);    // đọc ngân sách mới
  const r  = parseFloat(document.getElementById('cfgRate').value);      // đọc giá điện mới
  const ph = document.getElementById('cfgPeakHours').value
    .split(',')                            // tách theo dấu phẩy: "17, 18, 19" → ["17", " 18", " 19"]
    .map(x => parseInt(x.trim()))          // parse từng phần tử thành số nguyên
    .filter(n => !isNaN(n) && n >= 0 && n <= 23);  // lọc: chỉ giữ số hợp lệ (0-23)
  try {
    await API.saveConfig({ daily_budget_kwh: b, electricity_rate: r, peak_hours: ph });  // gọi API lưu
    State.config = { daily_budget_kwh: b, electricity_rate: r, peak_hours: ph };  // cập nhật State
    toast('Đã lưu cài đặt', 'success');
  } catch (e) { toast(e.message, 'error'); }
}

async function calcEvnPreview() {          // tính và hiện chi tiết tiền điện EVN
  const kwh = parseFloat(document.getElementById('evnKwh')?.value || 0);  // đọc kWh từ ô nhập
  if (!kwh || kwh < 0) { toast('Nhập số kWh hợp lệ', 'warning'); return; }  // kiểm tra hợp lệ
  try {
    const data = await API.calcEvn(kwh);   // gọi API tính EVN
    renderEvnResult(data);                 // render bảng chi tiết từng bậc
    renderEvnChart(data.breakdown);        // vẽ biểu đồ cột từng bậc
  } catch (e) { toast(e.message, 'error'); }
}

function renderEvnResult(data) {           // render bảng chi tiết tính tiền điện EVN
  const el = document.getElementById('evnResult');
  if (!el) return;
  const tierColors = ['#10b981','#34d399','#f59e0b','#fb923c','#ef4444','#dc2626'];  // màu 6 bậc
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

/* ─── CẬP NHẬT GIÁ TRỊ SLIDER ───────────────────────────────── */
function updateSlider(inputId, displayId, unit) {  // cập nhật text hiển thị giá trị của slider
  const v  = document.getElementById(inputId)?.value;  // đọc giá trị slider
  const el = document.getElementById(displayId);       // lấy phần tử hiển thị
  if (el) el.textContent = v + (unit || '');            // cập nhật text: "2.0 kWh"
}

/* ─── KHỞI TẠO ỨNG DỤNG ─────────────────────────────────────── */
async function init() {                     // hàm khởi tạo chạy khi trang load xong
  try {
    [State.devices, State.config] = await Promise.all([  // tải song song thiết bị và config
      API.getDevices(), API.getConfig()
    ]);
  } catch (e) { toast('Không thể kết nối server', 'error'); }  // thông báo lỗi kết nối

  document.querySelectorAll('[data-tab]').forEach(btn => {  // gắn sự kiện click cho tất cả nút tab
    btn.addEventListener('click', () => switchTab(btn.dataset.tab));  // khi click → chuyển tab
  });

  const dateInput = document.getElementById('usageDateInput');  // ô chọn ngày nhật ký
  if (dateInput) {
    dateInput.value = State.usageDate;      // đặt giá trị mặc định = hôm nay
    dateInput.addEventListener('change', e => setUsageDate(e.target.value));  // khi đổi ngày → cập nhật State
  }

  const optSlider = document.getElementById('optimizeBudget');  // slider ngân sách tối ưu
  if (optSlider) {
    optSlider.value = State.config.daily_budget_kwh;  // đặt giá trị = ngân sách từ config
    optSlider.addEventListener('input', e => {
      updateSlider('optimizeBudget', 'optimizeBudgetDisplay', ' kWh');  // cập nhật text hiển thị
      State.optimizeBudget = parseFloat(e.target.value);  // cập nhật State
    });
    updateSlider('optimizeBudget', 'optimizeBudgetDisplay', ' kWh');  // khởi tạo text ban đầu
  }

  const peakSlider = document.getElementById('peakBudget');  // slider ngân sách lịch cao điểm
  if (peakSlider) {
    peakSlider.value = State.config.daily_budget_kwh;  // đặt giá trị mặc định
    peakSlider.addEventListener('input', () => updateSlider('peakBudget', 'peakBudgetDisplay', ' kWh'));
    updateSlider('peakBudget', 'peakBudgetDisplay', ' kWh');
  }

  const evnInput = document.getElementById('evnKwh');  // ô nhập kWh để tính EVN
  if (evnInput) evnInput.addEventListener('keydown', e => { if (e.key==='Enter') calcEvnPreview(); });  // Enter → tính luôn

  const addForm = document.getElementById('addDeviceForm');   // form thêm thiết bị
  if (addForm) addForm.addEventListener('submit', submitAddDevice);  // gắn handler submit

  const cfgForm = document.getElementById('settingsForm');    // form cài đặt
  if (cfgForm) cfgForm.addEventListener('submit', saveSettings);  // gắn handler submit

  document.querySelectorAll('.modal-backdrop').forEach(el => {  // gắn sự kiện đóng modal khi click nền
    el.addEventListener('click', e => { if (e.target === el) el.classList.remove('show'); });  // chỉ đóng khi click đúng nền (không phải nội dung modal)
  });

  switchTab('dashboard');                   // mở tab dashboard ngay khi khởi động
}

document.addEventListener('DOMContentLoaded', init);  // chờ DOM tải xong rồi mới gọi init()
