/* ════════════════════════════════════════════════════════════════
   Extras — Export CSV, Bảng độ phức tạp, Thống kê thiết bị, Gợi ý, Tiện ích
   ════════════════════════════════════════════════════════════════ */

/* ─── Xuất CSV nhật ký sử dụng ───────────────────────────────── */
async function exportUsageCSV() {             // hàm xuất toàn bộ nhật ký sử dụng ra file CSV
  const [devs, usage] = await Promise.all([API.getDevices(), API.getUsage()]).catch(() => [[], []]);  // tải song song thiết bị và nhật ký
  const devMap = Object.fromEntries(devs.map(d => [d.id, d]));  // dict tra cứu nhanh thiết bị theo ID
  const rows   = [['Ngày', 'Thiết bị', 'ID', 'Công suất (W)', 'Số giờ', 'kWh', 'Chi phí (₫)']];  // hàng tiêu đề CSV
  const cfg    = await API.getConfig().catch(() => ({ electricity_rate: 3500 }));  // tải config, dùng giá mặc định 3500₫ nếu lỗi

  usage.forEach(u => {                        // duyệt từng entry nhật ký
    const dev = devMap[u.device_id];          // lấy thông tin thiết bị tương ứng
    if (!dev) return;                         // bỏ qua nếu thiết bị không còn trong danh sách
    const kwh  = dev.power_w * u.hours / 1000;  // tính kWh = công suất (W) × giờ ÷ 1000
    const cost = Math.round(kwh * cfg.electricity_rate);  // tính chi phí = kWh × đơn giá (làm tròn ₫)
    rows.push([u.date, dev.name, dev.id, dev.power_w, u.hours, kwh.toFixed(3), cost]);  // thêm hàng dữ liệu
  });

  const csv  = rows.map(r => r.map(v => `"${v}"`).join(',')).join('\n');  // ghép thành chuỗi CSV: mỗi giá trị trong dấu "", phân cách bằng ,
  const blob = new Blob(['﻿' + csv], { type: 'text/csv;charset=utf-8;' });  // tạo Blob UTF-8 với BOM (﻿) để Excel nhận đúng tiếng Việt
  const url  = URL.createObjectURL(blob);    // tạo URL tạm từ Blob
  const a    = document.createElement('a'); // tạo thẻ <a> ẩn để trigger download
  a.href     = url;                          // đặt href = URL file
  a.download = `nhat-ky-dien-${todayStr()}.csv`;  // tên file download kèm ngày hôm nay
  a.click();                                  // click <a> để trigger download
  URL.revokeObjectURL(url);                  // giải phóng URL tạm khỏi bộ nhớ
  toast('Đã xuất file CSV!', 'success');     // thông báo thành công
}

async function exportOptimizeCSV(result) {   // hàm xuất kết quả so sánh DP vs Greedy ra CSV
  if (!result) { toast('Hãy chạy tối ưu trước', 'warning'); return; }  // cảnh báo nếu chưa có kết quả
  const { dp, greedy } = result;            // destructure kết quả tối ưu
  const rows = [['Thuật toán', 'Thiết bị', 'Số giờ', 'kWh', 'Điểm thoải mái']];  // hàng tiêu đề
  dp.schedule.forEach(s => rows.push(['DP', s.device.name, s.hours, s.kwh, s.comfort]));       // thêm hàng DP
  greedy.schedule.forEach(s => rows.push(['Greedy', s.device.name, s.hours, s.kwh, s.comfort])); // thêm hàng Greedy
  const csv  = rows.map(r => r.map(v => `"${v}"`).join(',')).join('\n');  // ghép thành chuỗi CSV
  const blob = new Blob(['﻿' + csv], { type: 'text/csv;charset=utf-8;' });  // Blob với BOM UTF-8
  const url  = URL.createObjectURL(blob);   // URL tạm
  const a    = document.createElement('a'); // thẻ <a> ẩn
  a.href = url; a.download = `toi-uu-dp-greedy-${todayStr()}.csv`; a.click();  // đặt tên file và trigger download
  URL.revokeObjectURL(url);                 // giải phóng bộ nhớ
  toast('Đã xuất kết quả tối ưu!', 'success');  // thông báo
}

/* ─── Bảng độ phức tạp thuật toán ────────────────────────────── */
function renderComplexityTable(containerId) {  // hàm render bảng so sánh Big-O DP vs Greedy vs Brute Force
  const el = document.getElementById(containerId);  // lấy container
  if (!el) return;                            // thoát nếu không tìm thấy
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

/* ─── Thống kê chi tiết từng thiết bị ────────────────────────── */
async function renderDeviceStatsDetail(containerId) {  // hàm render bảng thống kê chi tiết từng thiết bị
  const el = document.getElementById(containerId);     // lấy container
  if (!el) return;                                      // thoát nếu không tìm thấy
  const [devs, usage, cfg] = await Promise.all([       // tải song song 3 API
    API.getDevices(), API.getUsage(), API.getConfig()
  ]).catch(() => [[], [], { electricity_rate: 3500 }]); // fallback nếu lỗi

  const devMap  = Object.fromEntries(devs.map(d => [d.id, d]));  // dict thiết bị theo ID (không dùng trực tiếp, dùng gián tiếp)
  const dateSet = new Set(usage.map(u => u.date));      // tập hợp các ngày đã ghi (Set loại bỏ trùng lặp)
  const nDays   = Math.max(dateSet.size, 1);            // số ngày đã ghi (tối thiểu 1 để tránh chia cho 0)

  const stats = devs.map(dev => {                       // tính thống kê cho từng thiết bị
    const entries   = usage.filter(u => u.device_id === dev.id);  // lọc nhật ký của thiết bị này
    const totalH    = entries.reduce((s, u) => s + u.hours, 0);   // tổng giờ đã dùng
    const totalKwh  = dev.power_w * totalH / 1000;                // tổng kWh tiêu thụ
    const cost      = totalKwh * cfg.electricity_rate;            // tổng chi phí (₫)
    const avgH      = totalH / nDays;                              // giờ trung bình/ngày
    const usedDays  = new Set(entries.map(u => u.date)).size;     // số ngày thực sự có dùng thiết bị
    return {
      dev, totalH, totalKwh, cost, avgH, usedDays,
      usagePct:    usedDays / nDays,                               // tỉ lệ ngày dùng / tổng ngày ghi
      monthlyKwh:  dev.power_w * avgH * 30 / 1000,                // kWh ước tính/tháng (dựa trên trung bình)
      monthlyCost: dev.power_w * avgH * 30 / 1000 * cfg.electricity_rate  // chi phí ước tính/tháng
    };
  }).filter(s => s.totalH > 0)                          // chỉ giữ thiết bị có ghi nhật ký
    .sort((a, b) => b.totalKwh - a.totalKwh);          // sắp xếp giảm dần theo kWh

  if (!stats.length) {                                  // nếu không có thiết bị nào có dữ liệu
    el.innerHTML = '<div class="empty-state"><i class="bi bi-bar-chart"></i><p>Chưa có dữ liệu. Hãy ghi nhật ký trước.</p></div>';
    return;
  }

  const maxKwh = stats[0].totalKwh;                    // kWh lớn nhất (để chuẩn hóa thanh tiến độ)
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

/* ─── Kho gợi ý tiết kiệm điện theo chủ đề ──────────────────── */
const SEASONAL_TIPS = [                       // mảng các danh mục gợi ý tiết kiệm điện
  {
    icon: '❄️',                               // icon danh mục điều hòa
    title: 'Điều hòa tiết kiệm điện',         // tiêu đề danh mục
    tips: [                                    // danh sách gợi ý cụ thể
      'Đặt nhiệt độ 26–28°C thay vì 18–20°C — tiết kiệm tới 30% điện năng',  // gợi ý 1: nhiệt độ hợp lý
      'Bật chế độ "Economy" hoặc "Eco" trên điều hòa',                         // gợi ý 2: chế độ tiết kiệm
      'Vệ sinh lọc điều hòa mỗi 1–2 tháng để tăng hiệu suất',                 // gợi ý 3: bảo trì
      'Kết hợp quạt điện + điều hòa để tối ưu làm mát',                       // gợi ý 4: dùng kết hợp
    ]
  },
  {
    icon: '💡',                               // icon danh mục chiếu sáng
    title: 'Chiếu sáng thông minh',
    tips: [
      'Dùng đèn LED thay bóng huỳnh quang — tiết kiệm 60–80% điện',          // LED hiệu quả hơn nhiều
      'Tắt đèn khi rời khỏi phòng (có thể dùng công tắc hẹn giờ)',            // thói quen cơ bản
      'Tận dụng ánh sáng tự nhiên ban ngày',                                   // sử dụng ánh sáng miễn phí
      'Đèn cắm cảm biến chuyển động tốt hơn đèn để sáng 24/7',               // cảm biến giúp tự động tắt
    ]
  },
  {
    icon: '🔌',                               // icon danh mục điện chờ standby
    title: 'Tránh lãng phí điện chờ',
    tips: [
      'Rút phích cắm TV, sạc điện thoại khi không dùng — standby tiêu tốn 5–10W',  // standby tốn điện thầm lặng
      'Dùng ổ điện có công tắc để tắt nhiều thiết bị cùng lúc',              // tiện lợi, tắt hàng loạt
      'Laptop ở chế độ sạc đầy nên rút dây (tránh quá nhiệt và hao pin)',    // bảo vệ pin dài hạn
      'Tủ lạnh không nên để cạnh nguồn nhiệt (bếp, ánh nắng)',               // tủ lạnh hoạt động khó hơn khi nóng
    ]
  },
  {
    icon: '⏰',                               // icon danh mục giờ thấp điểm
    title: 'Sử dụng giờ thấp điểm',
    tips: [
      'Giặt đồ, nấu cơm vào buổi sáng sớm hoặc sau 22h',                    // tránh giờ 17h-21h cao điểm
      'Tránh dùng bình nóng lạnh trong giờ cao điểm 17h–20h',               // bình nóng lạnh tốn nhiều điện
      'Sạc pin điện thoại, laptop vào ban đêm',                               // ban đêm là giờ thấp điểm
      'Lên lịch sử dụng máy giặt vào cuối tuần buổi sáng',                  // cuối tuần sáng thường thấp điểm
    ]
  },
  {
    icon: '🍚',                               // icon danh mục nấu nướng
    title: 'Nấu nướng hiệu quả',
    tips: [
      'Nồi cơm điện: cắm trước khi cần 20 phút, không để nóng quá lâu',     // giữ nóng tốn điện liên tục
      'Bình siêu tốc đun đủ lượng nước cần, không đun thừa',                // đun thừa = lãng phí
      'Dùng lò vi sóng nhanh hơn và ít điện hơn lò nướng với món nhỏ',      // vi sóng hiệu quả hơn cho món nhỏ
      'Hâm nóng thức ăn bằng nồi cơm điện tiết kiệm hơn lò vi sóng',       // nồi cơm dùng ít điện hơn vi sóng
    ]
  },
];

function renderSeasonalTips(containerId) {    // hàm render danh sách gợi ý tiết kiệm điện
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
    </div>`).join('');                        // join('') ghép các thẻ card thành chuỗi HTML
}

/* ─── Lập kế hoạch ngân sách tháng ──────────────────────────── */
function calcMonthlyBudgetPlan(dailyBudget, rate, targetBill) {  // hàm tính hóa đơn EVN và so với mục tiêu
  const monthlyKwh = dailyBudget * 30;       // kWh/tháng = kWh/ngày × 30 ngày
  const tiers = [                            // 6 bậc giá điện EVN (₫/kWh)
    { lim: 50,   rate: 1806 },               // bậc 1: 0–50 kWh
    { lim: 50,   rate: 1866 },               // bậc 2: 51–100 kWh
    { lim: 100,  rate: 2167 },               // bậc 3: 101–200 kWh
    { lim: 100,  rate: 2729 },               // bậc 4: 201–300 kWh
    { lim: 100,  rate: 3050 },               // bậc 5: 301–400 kWh
    { lim: 9999, rate: 3151 },               // bậc 6: >400 kWh
  ];
  let cost = 0; let rem = monthlyKwh;        // cost: tổng tiền; rem: kWh còn lại chưa tính
  for (const t of tiers) {                  // duyệt từng bậc
    const used = Math.min(rem, t.lim);      // kWh áp dụng bậc này = min(còn lại, giới hạn bậc)
    cost += used * t.rate;                   // cộng tiền bậc này vào tổng
    rem -= used;                             // trừ đi phần đã tính
    if (rem <= 0) break;                    // đã tính hết, không cần duyệt thêm
  }
  const saving = cost - (targetBill || 0);  // chênh lệch so với hóa đơn mục tiêu (âm = đạt mục tiêu)
  return {
    monthlyKwh:   Math.round(monthlyKwh * 10) / 10,  // làm tròn 1 chữ số thập phân
    evnCost:      Math.round(cost),                    // làm tròn ₫
    saving:       Math.round(saving),                  // chênh lệch (dương = vượt mục tiêu)
    withinBudget: saving <= 0                          // true nếu hóa đơn EVN ≤ mục tiêu
  };
}

function renderBudgetPlanner(containerId) {  // hàm render form lập kế hoạch ngân sách
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
    <div id="plannerResult" style="margin-top:14px"></div>`;  // container hiện kết quả sau khi tính
}

function runBudgetPlanner() {               // hàm tính và hiện kết quả kế hoạch ngân sách
  const budget = parseFloat(document.getElementById('plannerBudget')?.value || 2);    // đọc ngân sách từ ô nhập
  const target = parseFloat(document.getElementById('plannerTarget')?.value || 300000);  // đọc hóa đơn mục tiêu
  const plan   = calcMonthlyBudgetPlan(budget, 3500, target);  // tính theo bậc EVN
  const el     = document.getElementById('plannerResult');     // container kết quả
  if (!el) return;
  const color  = plan.withinBudget ? '#10b981' : '#ef4444';   // màu: xanh nếu đạt, đỏ nếu vượt
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
          ? `✅ Tiết kiệm được ${fmt.vndFull(Math.abs(plan.saving))} so với mục tiêu!`             // đạt mục tiêu
          : `⚠️ Vượt mục tiêu ${fmt.vndFull(Math.abs(plan.saving))} — hãy giảm xuống ${Math.max(0.5, budget - 0.5).toFixed(1)} kWh/ngày`}  // gợi ý giảm ngân sách
      </div>
    </div>`;
}

/* ─── Chỉ số mức tiêu thụ điện hiện tại ─────────────────────── */
function getPowerLevel(kwh, budget) {         // trả về nhãn, màu, icon tương ứng với % ngân sách đã dùng
  const pct = budget > 0 ? kwh / budget : 0; // tỉ lệ đã dùng (0 nếu budget = 0)
  if (pct <= 0)    return { label: 'Chưa dùng',    color: '#64748b', icon: 'bi-circle' };         // 0%: chưa có dữ liệu
  if (pct <= 0.50) return { label: 'Tiết kiệm',    color: '#10b981', icon: 'bi-battery-full' };   // 0–50%: tốt
  if (pct <= 0.75) return { label: 'Bình thường',  color: '#f59e0b', icon: 'bi-battery-half' };   // 50–75%: bình thường
  if (pct <= 1.00) return { label: 'Gần giới hạn', color: '#fb923c', icon: 'bi-battery-low' };    // 75–100%: cần chú ý
  return { label: 'Vượt ngân sách', color: '#ef4444', icon: 'bi-battery-charging' };              // >100%: vượt ngân sách
}

/* ─── Phím tắt Alt+1…7 chuyển tab ───────────────────────────── */
function setupQuickActions() {               // hàm đăng ký phím tắt bàn phím để chuyển tab nhanh
  const shortcuts = [                        // mảng ánh xạ phím → tab
    { key: '1', tab: 'dashboard',  label: 'Dashboard' },    // Alt+1 → Dashboard
    { key: '2', tab: 'devices',    label: 'Thiết bị' },     // Alt+2 → Thiết bị
    { key: '3', tab: 'usage',      label: 'Nhật ký' },      // Alt+3 → Nhật ký
    { key: '4', tab: 'optimize',   label: 'Tối ưu' },       // Alt+4 → Tối ưu
    { key: '5', tab: 'peak',       label: 'Lịch cao điểm' },// Alt+5 → Cao điểm
    { key: '6', tab: 'forecast',   label: 'Dự báo' },       // Alt+6 → Dự báo
    { key: '7', tab: 'settings',   label: 'Cài đặt' },      // Alt+7 → Cài đặt
  ];
  document.addEventListener('keydown', e => {  // lắng nghe sự kiện bàn phím toàn trang
    if (e.altKey) {                           // chỉ xử lý khi giữ phím Alt
      const sc = shortcuts.find(s => s.key === e.key);  // tìm shortcut tương ứng với phím nhấn
      if (sc) { e.preventDefault(); switchTab(sc.tab); }  // ngăn hành vi mặc định và chuyển tab
    }
  });
}

/* ─── Lưu và đọc trạng thái UI từ localStorage ──────────────── */
const UIState = {                            // object tiện ích lưu trạng thái UI vào localStorage
  save(key, value) {                         // lưu giá trị vào localStorage với prefix 'elec_'
    try { localStorage.setItem('elec_' + key, JSON.stringify(value)); } catch {}  // try-catch để tránh lỗi nếu localStorage đầy
  },
  load(key, def) {                           // đọc giá trị từ localStorage, trả về def nếu không có
    try {
      const v = localStorage.getItem('elec_' + key);   // đọc chuỗi JSON từ storage
      return v !== null ? JSON.parse(v) : def;          // parse JSON nếu có, trả về default nếu không có
    } catch { return def; }                 // trả về default nếu parse thất bại
  }
};

/* ─── Hoạt ảnh đếm số (count-up animation) ──────────────────── */
function animateNumber(el, from, to, duration = 800, decimals = 0) {  // hoạt ảnh đổi số mượt mà từ 'from' đến 'to'
  const start = performance.now();            // thời điểm bắt đầu hoạt ảnh (milliseconds)
  function update(now) {                      // hàm cập nhật từng frame
    const t   = Math.min((now - start) / duration, 1);  // t ∈ [0,1]: tiến độ hoạt ảnh (0=bắt đầu, 1=kết thúc)
    const val = from + (to - from) * easeOut(t);        // giá trị hiện tại theo hàm easeOut
    el.textContent = val.toFixed(decimals);  // cập nhật text với số chữ số thập phân chỉ định
    if (t < 1) requestAnimationFrame(update); // nếu chưa xong → yêu cầu frame tiếp theo
  }
  requestAnimationFrame(update);             // bắt đầu vòng lặp animation
}

function easeOut(t) { return 1 - Math.pow(1 - t, 3); }  // hàm easeOut cubic: bắt đầu nhanh, dần dần chậm lại

/* ─── Debounce — trì hoãn gọi hàm ───────────────────────────── */
function debounce(fn, ms) {                  // trả về phiên bản debounced của hàm fn: chỉ gọi sau ms kể từ lần gọi cuối
  let timer;                                 // biến lưu ID của setTimeout
  return (...args) => {                      // hàm wrapper nhận cùng args
    clearTimeout(timer);                     // hủy timer cũ nếu có (reset đếm ngược)
    timer = setTimeout(() => fn(...args), ms);  // đặt timer mới: sau ms ms mới gọi fn
  };
}

/* ─── Sao chép text vào clipboard ────────────────────────────── */
function copyText(text) {                    // hàm copy chuỗi text vào clipboard
  navigator.clipboard.writeText(text)        // API clipboard không đồng bộ
    .then(() => toast('Đã sao chép!', 'success'))   // thành công: toast xanh
    .catch(() => toast('Không thể sao chép', 'error'));  // thất bại: toast đỏ
}

/* ─── Định dạng thời gian (giờ + phút) ───────────────────────── */
function fmtDuration(hours) {               // chuyển số giờ (thực) thành chuỗi "Xh Yp"
  const h = Math.floor(hours);              // phần nguyên giờ
  const m = Math.round((hours - h) * 60);  // phần lẻ quy ra phút (làm tròn)
  if (h === 0) return `${m}p`;             // chỉ có phút: "30p"
  if (m === 0) return `${h}h`;             // chỉ có giờ: "2h"
  return `${h}h${m}p`;                     // có cả hai: "1h30p"
}

/* ─── Nhãn ngày trong tuần (tiếng Việt) ──────────────────────── */
function dayLabel(dateStr) {                 // chuyển chuỗi ngày "YYYY-MM-DD" thành nhãn "CN/T2/…/T7"
  const d = new Date(dateStr + 'T00:00:00');  // thêm giờ để tránh lệch múi giờ UTC
  return ['CN','T2','T3','T4','T5','T6','T7'][d.getDay()];  // getDay(): 0=CN, 1=T2, …, 6=T7
}

/* ─── So sánh tuần này vs tuần trước ─────────────────────────── */
function calcWeeklySummary(daily) {          // tính tổng kWh tuần này và tuần trước, % thay đổi
  const thisWeek  = daily.slice(-7);         // 7 ngày gần nhất (tuần này)
  const lastWeek  = daily.slice(-14, -7);    // 7 ngày trước đó (tuần trước)
  const thisTotal = thisWeek.reduce((s, d) => s + d.kwh, 0);   // tổng kWh tuần này
  const lastTotal = lastWeek.reduce((s, d) => s + d.kwh, 0);   // tổng kWh tuần trước
  const change    = lastTotal > 0 ? (thisTotal - lastTotal) / lastTotal * 100 : 0;  // % thay đổi (0 nếu tuần trước = 0)
  return {
    thisWeek:  Math.round(thisTotal * 1000) / 1000,  // làm tròn 3 chữ số (kWh)
    lastWeek:  Math.round(lastTotal * 1000) / 1000,  // làm tròn 3 chữ số
    change:    Math.round(change * 10) / 10,          // làm tròn 1 chữ số thập phân (%)
    improved:  change < 0                             // true nếu tuần này dùng ít hơn tuần trước
  };
}

/* ─── Render so sánh tuần ────────────────────────────────────── */
function renderWeeklySummary(stats, containerId) {  // hàm hiện card so sánh kWh tuần này vs tuần trước
  const el = document.getElementById(containerId);
  if (!el || !stats?.daily?.length) return;  // thoát nếu không tìm thấy hoặc chưa có dữ liệu
  const w     = calcWeeklySummary(stats.daily);  // tính dữ liệu so sánh
  const color = w.improved ? '#10b981' : '#ef4444';  // xanh nếu cải thiện, đỏ nếu tăng
  const icon  = w.improved ? 'bi-arrow-down-circle-fill' : 'bi-arrow-up-circle-fill';  // icon mũi tên
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

/* ─── Tự động làm mới dashboard ──────────────────────────────── */
let _autoRefreshTimer = null;               // biến lưu ID của setInterval (null = chưa khởi động)

function startAutoRefresh(intervalMs = 60000) {  // bắt đầu tự động làm mới dashboard theo chu kỳ
  stopAutoRefresh();                         // dừng timer cũ trước (tránh chạy nhiều timer song song)
  _autoRefreshTimer = setInterval(() => {    // đặt timer lặp lại
    if (State.activeTab === 'dashboard') {   // chỉ làm mới khi đang ở tab dashboard
      renderDashboard();                     // gọi lại render dashboard để lấy số liệu mới nhất
    }
  }, intervalMs);                            // chu kỳ làm mới (mặc định 60 giây)
}

function stopAutoRefresh() {                // dừng timer tự động làm mới
  if (_autoRefreshTimer) { clearInterval(_autoRefreshTimer); _autoRefreshTimer = null; }  // xóa interval và reset biến
}

/* ─── Khởi tạo các tính năng phụ khi DOM sẵn sàng ──────────── */
document.addEventListener('DOMContentLoaded', () => {  // chờ DOM tải xong
  setupQuickActions();                       // đăng ký phím tắt Alt+1…7
  startAutoRefresh(120000);                 // bắt đầu tự động làm mới mỗi 120 giây (2 phút)
});

/* ─── Danh sách 6 bậc giá điện EVN ──────────────────────────── */
const EVN_TIERS = [                          // mảng hằng số 6 bậc giá điện EVN Việt Nam
  { label: 'Bậc 1', limit: 50,   price: 1806, color: '#10b981' },  // bậc 1: 0–50 kWh → 1.806₫
  { label: 'Bậc 2', limit: 100,  price: 1866, color: '#34d399' },  // bậc 2: 51–100 kWh → 1.866₫
  { label: 'Bậc 3', limit: 200,  price: 2167, color: '#f59e0b' },  // bậc 3: 101–200 kWh → 2.167₫
  { label: 'Bậc 4', limit: 300,  price: 2729, color: '#fb923c' },  // bậc 4: 201–300 kWh → 2.729₫
  { label: 'Bậc 5', limit: 400,  price: 3050, color: '#ef4444' },  // bậc 5: 301–400 kWh → 3.050₫
  { label: 'Bậc 6', limit: 9999, price: 3151, color: '#dc2626' },  // bậc 6: >400 kWh → 3.151₫
];

function getTier(monthlyKwh) {              // trả về bậc điện hiện tại dựa trên kWh tháng
  let rem = monthlyKwh;                    // kWh còn lại chưa phân bậc
  for (const t of EVN_TIERS) {            // duyệt từng bậc
    if (rem <= t.limit) return t;          // nếu còn lại ≤ giới hạn bậc → đây là bậc hiện tại
    rem -= t.limit;                        // trừ đi giới hạn bậc và tiếp tục bậc sau
  }
  return EVN_TIERS[EVN_TIERS.length - 1]; // trả về bậc 6 nếu vượt tất cả
}

/* ─── Xếp loại mức tiêu thụ điện tháng ──────────────────────── */
function getConsumptionGrade(monthlyKwh) {  // xếp loại A+ đến F theo kWh/tháng
  if (monthlyKwh <= 50)  return { grade: 'A+', label: 'Xuất sắc',   color: '#10b981' };  // ≤50 kWh: xuất sắc
  if (monthlyKwh <= 100) return { grade: 'A',  label: 'Tốt',        color: '#34d399' };  // ≤100 kWh: tốt
  if (monthlyKwh <= 150) return { grade: 'B',  label: 'Khá',        color: '#f59e0b' };  // ≤150 kWh: khá
  if (monthlyKwh <= 200) return { grade: 'C',  label: 'Trung bình', color: '#fb923c' };  // ≤200 kWh: trung bình
  if (monthlyKwh <= 300) return { grade: 'D',  label: 'Cao',        color: '#ef4444' };  // ≤300 kWh: cao
  return { grade: 'F', label: 'Rất cao', color: '#dc2626' };                              // >300 kWh: rất cao
}

/* ─── Điểm hiệu quả của thiết bị ────────────────────────────── */
function deviceEfficiencyScore(dev) {       // tính điểm hiệu quả 0–100 cho thiết bị dựa trên tỉ lệ ưu tiên/công suất
  const ratio    = dev.priority / dev.power_w;  // tỉ lệ: ưu tiên càng cao, công suất càng thấp → thiết bị càng hiệu quả
  const maxRatio = 5 / 10;                  // tỉ lệ tối đa lý thuyết: ưu tiên 5 / công suất 10W
  return Math.min(100, Math.round(ratio / maxRatio * 100));  // điểm 0–100, tối đa 100
}

/* ─── Định dạng số theo locale Việt Nam ─────────────────────── */
function numPad(n, decimals = 0) {          // định dạng số theo chuẩn Việt Nam (dấu . ngăn cách nghìn)
  return n.toLocaleString('vi-VN', { minimumFractionDigits: decimals, maximumFractionDigits: decimals });  // ví dụ: 1234567 → "1.234.567"
}

/* ─── Tính toán tiết kiệm điện từ pin mặt trời (bonus) ──────── */
function calcSolarSavings(panelWatts, sunHoursPerDay, rate) {  // ước tính tiền tiết kiệm khi lắp pin mặt trời
  const dailyKwh   = panelWatts * sunHoursPerDay / 1000;  // kWh/ngày = công suất tấm pin × giờ nắng ÷ 1000
  const monthlyKwh = dailyKwh * 30;                        // kWh/tháng = kWh/ngày × 30
  const savings    = monthlyKwh * rate;                    // tiền tiết kiệm = kWh/tháng × đơn giá ₫/kWh
  return { dailyKwh, monthlyKwh, savings };                // trả về object chứa 3 giá trị
}

/* ─── Tiện ích đọc/ghi localStorage ─────────────────────────── */
const LS = {                                // object tiện ích localStorage ngắn gọn hơn UIState
  get:    (k, d) => { try { const v = localStorage.getItem(k); return v ? JSON.parse(v) : d; } catch { return d; } },  // đọc và parse JSON, trả default nếu lỗi
  set:    (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)); } catch {} },  // lưu JSON, im lặng nếu lỗi
  remove: (k)    => { try { localStorage.removeItem(k); } catch {} }                  // xóa key, im lặng nếu lỗi
};
