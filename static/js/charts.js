/* ════════════════════════════════════════════════════════════════
   Charts — Bọc Chart.js: vẽ tất cả biểu đồ trong ứng dụng
   ════════════════════════════════════════════════════════════════ */

const CHART_DEFAULTS = {                       // cấu hình mặc định dùng chung cho tất cả biểu đồ
  responsive: true,                            // tự động co giãn theo kích thước container
  maintainAspectRatio: false,                  // không giữ tỉ lệ cố định → cho phép chiều cao tùy ý
  plugins: {                                   // cấu hình các plugin của Chart.js
    legend: {                                  // cấu hình phần chú thích (legend)
      labels: {
        color: '#94a3b8',                      // màu chữ chú thích: xám nhạt
        font: { family: 'Segoe UI', size: 12 },// font chữ và cỡ chữ
        usePointStyle: true,                   // dùng hình tròn nhỏ thay vì hình chữ nhật cho ký hiệu
        pointStyleWidth: 8,                    // độ rộng của ký hiệu hình tròn
        padding: 16                            // khoảng cách giữa các mục chú thích
      }
    },
    tooltip: {                                 // cấu hình tooltip (bong bóng khi hover)
      backgroundColor: 'rgba(4,15,38,0.96)',   // nền tooltip: xanh đen đậm, gần như đục hoàn toàn
      borderColor: 'rgba(0,212,255,0.2)',      // viền tooltip: xanh cyan mờ
      borderWidth: 1,                          // độ dày viền: 1px
      titleColor: '#f0f6ff',                   // màu tiêu đề tooltip: trắng sáng
      bodyColor: '#94a3b8',                    // màu nội dung tooltip: xám
      padding: 12,                             // khoảng đệm bên trong tooltip
      cornerRadius: 8,                         // bo góc tooltip
      titleFont: { family: 'Segoe UI', weight: 700, size: 13 },  // font tiêu đề tooltip
      bodyFont:  { family: 'Segoe UI', size: 12 },               // font nội dung tooltip
    }
  },
  scales: {                                    // cấu hình trục tọa độ
    x: {                                       // trục ngang X
      grid: { color: 'rgba(255,255,255,0.04)' },  // đường lưới dọc: trắng rất mờ
      ticks: { color: '#64748b', font: { family: 'Segoe UI', size: 11 } },  // nhãn trục X: xám, cỡ nhỏ
    },
    y: {                                       // trục dọc Y
      grid: { color: 'rgba(255,255,255,0.04)' },  // đường lưới ngang: trắng rất mờ
      ticks: { color: '#64748b', font: { family: 'Segoe UI', size: 11 } },  // nhãn trục Y: xám, cỡ nhỏ
    }
  }
};

/* Lưu trữ các instance Chart.js đang hoạt động để có thể hủy trước khi vẽ lại */
const Charts = {};                             // object map: tên biểu đồ → instance Chart.js

function destroyChart(key) {                   // hàm hủy biểu đồ cũ trước khi tạo biểu đồ mới
  if (Charts[key]) {                           // kiểm tra instance có tồn tại không
    Charts[key].destroy();                     // hủy instance (giải phóng canvas và event listeners)
    delete Charts[key];                        // xóa khỏi object lưu trữ
  }
}

/* ─── Biểu đồ đường: Tiêu thụ điện 14 ngày gần nhất ─────────── */
function renderDailyChart(daily) {             // vẽ biểu đồ đường tiêu thụ 14 ngày, daily là mảng {date, kwh}
  destroyChart('daily');                       // hủy biểu đồ cũ nếu có (tránh chồng lên nhau)
  const ctx = document.getElementById('chartDaily');  // lấy phần tử canvas trong HTML
  if (!ctx) return;                            // thoát nếu canvas không tồn tại

  const labels  = daily.map(d => fmt.date(d.date));       // nhãn trục X: mảng ngày "DD/MM"
  const dataKwh = daily.map(d => d.kwh);                  // dữ liệu: mảng số kWh mỗi ngày
  const budget  = daily.map(                               // đường ngân sách: giá trị không đổi theo ngày
    () => parseFloat(document.getElementById('budgetDisplay')?.dataset?.budget || 2)  // đọc ngân sách từ DOM
  );

  Charts.daily = new Chart(ctx, {              // tạo instance Chart.js mới và lưu vào Charts
    type: 'line',                              // loại biểu đồ: đường
    data: {
      labels,                                  // nhãn trục X
      datasets: [
        {
          label: 'Tiêu thụ (kWh)',             // nhãn hiển thị trong chú thích
          data: dataKwh,                        // dữ liệu tiêu thụ thực tế
          borderColor: '#00d4ff',               // màu đường: xanh cyan
          backgroundColor: 'rgba(0,212,255,0.08)',  // vùng tô dưới đường: xanh cyan rất mờ
          borderWidth: 2.5,                     // độ dày đường: 2.5px
          pointBackgroundColor: '#00d4ff',      // màu điểm tròn trên đường
          pointRadius: 4,                       // bán kính điểm: 4px
          pointHoverRadius: 7,                  // bán kính điểm khi hover: 7px (to hơn)
          fill: true,                           // tô màu vùng dưới đường
          tension: 0.4,                         // độ cong của đường (0=thẳng, 1=cong nhiều)
        },
        {
          label: 'Ngân sách',                  // đường giới hạn ngân sách
          data: budget,                         // giá trị ngân sách cố định (đường ngang)
          borderColor: 'rgba(239,68,68,0.5)',  // màu đường: đỏ mờ
          borderWidth: 1.5,                     // độ dày: 1.5px
          borderDash: [6, 3],                   // đường nét đứt: 6px nét, 3px khoảng trống
          pointRadius: 0,                       // không hiện điểm trên đường ngân sách
          fill: false,                          // không tô vùng dưới
          tension: 0,                           // đường thẳng hoàn toàn (không cong)
        }
      ]
    },
    options: {
      ...CHART_DEFAULTS,                        // kế thừa toàn bộ cài đặt mặc định
      plugins: {
        ...CHART_DEFAULTS.plugins,              // kế thừa cài đặt plugin mặc định
        tooltip: {
          ...CHART_DEFAULTS.plugins.tooltip,    // kế thừa cài đặt tooltip mặc định
          callbacks: {
            label: ctx => ctx.dataset.label + ': ' + ctx.parsed.y.toFixed(3) + ' kWh'  // format nhãn tooltip: "Tiêu thụ: 1.234 kWh"
          }
        }
      },
      scales: {
        x: { ...CHART_DEFAULTS.scales.x },     // dùng cài đặt trục X mặc định
        y: { ...CHART_DEFAULTS.scales.y, min: 0,  // trục Y bắt đầu từ 0
             title: { display: true, text: 'kWh', color: '#64748b' } }  // tiêu đề trục Y
      }
    }
  });
}

/* ─── Biểu đồ tròn Donut: Phân bổ kWh theo thiết bị ─────────── */
function renderDonutChart(byDevice) {          // vẽ biểu đồ donut, byDevice là mảng {name, kwh}
  destroyChart('donut');                       // hủy biểu đồ cũ
  const ctx = document.getElementById('chartDonut');  // lấy canvas
  if (!ctx || !byDevice.length) return;       // thoát nếu không có canvas hoặc không có dữ liệu
  const top    = byDevice.slice(0, 7);        // lấy tối đa 7 thiết bị (tránh biểu đồ quá rối)
  const colors = ['#00d4ff','#7c3aed','#10b981','#f59e0b','#ef4444','#fb923c','#38bdf8'];  // bảng màu 7 màu

  Charts.donut = new Chart(ctx, {             // tạo instance và lưu
    type: 'doughnut',                          // loại: donut (tròn có lỗ giữa)
    data: {
      labels: top.map(d => d.name),            // nhãn: tên thiết bị
      datasets: [{
        data: top.map(d => d.kwh),             // dữ liệu: kWh của mỗi thiết bị
        backgroundColor: colors,               // màu nền từng phần
        borderColor: 'rgba(0,0,0,0.3)',        // viền giữa các phần: đen mờ
        borderWidth: 2,                         // độ dày viền: 2px
        hoverBorderWidth: 3,                    // độ dày viền khi hover: 3px
      }]
    },
    options: {
      responsive: true,                         // tự động co giãn
      maintainAspectRatio: false,               // không giữ tỉ lệ
      cutout: '68%',                            // độ rỗng ở giữa: 68% (tạo "lỗ" của donut)
      plugins: {
        legend: {
          position: 'right',                    // chú thích nằm bên phải biểu đồ
          labels: { color: '#94a3b8', font: { size: 12 }, padding: 12, usePointStyle: true }
        },
        tooltip: {
          ...CHART_DEFAULTS.plugins.tooltip,
          callbacks: {
            label: ctx => `${ctx.label}: ${ctx.parsed.toFixed(3)} kWh`  // "Điều hòa: 1.234 kWh"
          }
        }
      }
    }
  });
}

/* ─── Biểu đồ cột: So sánh điểm thoải mái DP vs Greedy ──────── */
function renderOptimizeChart(dp, greedy) {     // vẽ biểu đồ cột so sánh, dp và greedy là kết quả thuật toán
  destroyChart('optimize');                    // hủy biểu đồ cũ
  const ctx = document.getElementById('chartOptimize');  // lấy canvas
  if (!ctx) return;

  const dpNames  = dp.schedule.map(s => s.device.name);      // tên thiết bị trong lịch DP
  const grNames  = greedy.schedule.map(s => s.device.name);  // tên thiết bị trong lịch Greedy
  const allNames = [...new Set([...dpNames, ...grNames])];    // hợp nhất, loại trùng: tất cả tên thiết bị

  const dpMap = Object.fromEntries(dp.schedule.map(s => [s.device.name, s.comfort]));      // map tên → điểm DP
  const grMap = Object.fromEntries(greedy.schedule.map(s => [s.device.name, s.comfort]));  // map tên → điểm Greedy

  Charts.optimize = new Chart(ctx, {
    type: 'bar',                               // loại: biểu đồ cột
    data: {
      labels: allNames,                        // nhãn trục X: tên thiết bị
      datasets: [
        {
          label: 'DP (điểm thoải mái)',        // cột xanh cyan: điểm của DP
          data: allNames.map(n => dpMap[n] || 0),  // điểm DP cho từng thiết bị (0 nếu không dùng)
          backgroundColor: 'rgba(0,212,255,0.7)',   // màu nền cột: cyan
          borderColor: '#00d4ff',               // màu viền cột: cyan đậm hơn
          borderWidth: 1,                       // độ dày viền: 1px
          borderRadius: 6,                      // bo góc trên của cột: 6px
        },
        {
          label: 'Greedy (điểm thoải mái)',    // cột tím: điểm của Greedy
          data: allNames.map(n => grMap[n] || 0),  // điểm Greedy cho từng thiết bị
          backgroundColor: 'rgba(124,58,237,0.7)', // màu nền: tím
          borderColor: '#7c3aed',               // viền: tím đậm
          borderWidth: 1,
          borderRadius: 6,
        }
      ]
    },
    options: {
      ...CHART_DEFAULTS,
      plugins: { ...CHART_DEFAULTS.plugins },
      scales: {
        x: { ...CHART_DEFAULTS.scales.x },
        y: { ...CHART_DEFAULTS.scales.y, min: 0,  // trục Y từ 0
             title: { display: true, text: 'Điểm', color: '#64748b' } }  // tiêu đề trục Y
      }
    }
  });
}

/* ─── Biểu đồ đường kép: Dự báo 6 tháng (kWh + chi phí) ─────── */
function renderForecastChart(months) {         // vẽ biểu đồ dự báo, months là mảng {label, kwh, evn}
  destroyChart('forecast');                    // hủy biểu đồ cũ
  const ctx = document.getElementById('chartForecast');  // lấy canvas
  if (!ctx) return;

  Charts.forecast = new Chart(ctx, {
    type: 'line',                              // loại: đường
    data: {
      labels: months.map(m => m.label),        // nhãn: "Tháng +1", "Tháng +2", ...
      datasets: [
        {
          label: 'Dự báo tiêu thụ (kWh)',     // đường xanh: kWh dự báo
          data: months.map(m => m.kwh),        // dữ liệu kWh
          borderColor: '#00d4ff',               // màu đường: cyan
          backgroundColor: 'rgba(0,212,255,0.08)',  // tô màu dưới đường
          borderWidth: 2.5,
          pointBackgroundColor: '#00d4ff',      // màu điểm
          pointRadius: 5,
          fill: true,
          tension: 0.3,                         // cong nhẹ
          yAxisID: 'y',                         // gắn với trục Y bên trái
        },
        {
          label: 'Chi phí EVN (1000 ₫)',       // đường vàng: chi phí EVN
          data: months.map(m => m.evn / 1000), // chia 1000 để đơn vị là "1000 ₫" (tránh số quá lớn)
          borderColor: '#f59e0b',               // màu đường: vàng
          backgroundColor: 'rgba(245,158,11,0.06)',
          borderWidth: 2,
          pointBackgroundColor: '#f59e0b',
          pointRadius: 5,
          fill: true,
          tension: 0.3,
          yAxisID: 'y1',                        // gắn với trục Y1 bên phải (trục thứ hai)
        }
      ]
    },
    options: {
      ...CHART_DEFAULTS,
      interaction: { mode: 'index', intersect: false },  // tooltip hiện đồng thời cả 2 dataset khi hover
      plugins: { ...CHART_DEFAULTS.plugins },
      scales: {
        x: { ...CHART_DEFAULTS.scales.x },
        y:  { ...CHART_DEFAULTS.scales.y, title: { display: true, text: 'kWh', color: '#64748b' },
              position: 'left' },               // trục Y1 bên trái: đơn vị kWh
        y1: { ...CHART_DEFAULTS.scales.y, title: { display: true, text: '1000 ₫', color: '#64748b' },
              position: 'right',               // trục Y2 bên phải: đơn vị nghìn đồng
              grid: { drawOnChartArea: false } } // không vẽ lưới cho trục thứ hai (tránh rối)
      }
    }
  });
}

/* ─── Biểu đồ phân cực: Phân bổ kWh theo danh mục ──────────── */
function renderCategoryChart(byDevice) {       // vẽ biểu đồ polar area theo danh mục
  destroyChart('category');                    // hủy biểu đồ cũ
  const ctx = document.getElementById('chartCategory');  // lấy canvas
  if (!ctx || !byDevice.length) return;       // thoát nếu không có dữ liệu

  const grouped = {};                          // object gom nhóm kWh theo danh mục
  byDevice.forEach(d => {
    grouped[d.category] = (grouped[d.category] || 0) + d.kwh;  // cộng dồn kWh của cùng danh mục
  });

  const labels = Object.keys(grouped).map(k => catLabel(k));      // nhãn: tên danh mục tiếng Việt
  const data   = Object.values(grouped);                          // dữ liệu: tổng kWh mỗi danh mục
  const colors = Object.keys(grouped).map(k => catColor(k));      // màu: theo danh mục

  Charts.category = new Chart(ctx, {
    type: 'polarArea',                         // loại: polar area (tròn phân cực)
    data: {
      labels,
      datasets: [{
        data,
        backgroundColor: colors.map(c => c + '88'),  // thêm alpha '88' (hex) = ~54% opacity
        borderColor: colors,                   // viền màu đậm hơn
        borderWidth: 1.5,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'right',                   // chú thích bên phải
          labels: { color: '#94a3b8', font: { size: 11 }, padding: 10 }
        },
        tooltip: {
          ...CHART_DEFAULTS.plugins.tooltip,
          callbacks: { label: ctx => `${ctx.label}: ${ctx.parsed.r.toFixed(2)} kWh` }  // "Làm mát: 1.23 kWh"
        }
      },
      scales: {
        r: {                                   // trục bán kính (polar)
          grid: { color: 'rgba(255,255,255,0.06)' },   // lưới bán kính: trắng rất mờ
          ticks: { color: '#64748b', font: { size: 10 }, backdropColor: 'transparent' }  // nhãn giá trị
        }
      }
    }
  });
}

/* ─── Biểu đồ cột: Chi phí điện EVN theo từng bậc ───────────── */
function renderEvnChart(breakdown) {           // vẽ biểu đồ bậc giá EVN, breakdown là mảng {bac, kwh, rate, cost}
  destroyChart('evn');                         // hủy biểu đồ cũ
  const ctx = document.getElementById('chartEvn');  // lấy canvas
  if (!ctx) return;

  const tierColors = ['#10b981','#34d399','#f59e0b','#fb923c','#ef4444','#dc2626'];  // màu 6 bậc: xanh → đỏ

  Charts.evn = new Chart(ctx, {
    type: 'bar',                               // loại: cột
    data: {
      labels: breakdown.map(b => `Bậc ${b.bac}`),  // nhãn: "Bậc 1", "Bậc 2", ...
      datasets: [{
        label: 'Chi phí (₫)',                  // nhãn dataset
        data: breakdown.map(b => b.cost),      // dữ liệu: tiền của từng bậc (₫)
        backgroundColor: tierColors.slice(0, breakdown.length),  // màu tương ứng với số bậc thực tế
        borderRadius: 6,                        // bo góc cột
        borderSkipped: false,                  // bo cả góc dưới (không bỏ qua góc nào)
      }]
    },
    options: {
      ...CHART_DEFAULTS,
      plugins: {
        ...CHART_DEFAULTS.plugins,
        tooltip: {
          ...CHART_DEFAULTS.plugins.tooltip,
          callbacks: {
            label: ctx =>                      // format tooltip: "35.000 ₫ (15.00 kWh × 2.167 ₫/kWh)"
              `${fmt.vndFull(ctx.parsed.y)} (${breakdown[ctx.dataIndex]?.kwh} kWh × ${breakdown[ctx.dataIndex]?.rate} ₫/kWh)`
          }
        }
      },
      scales: {
        x: { ...CHART_DEFAULTS.scales.x },
        y: { ...CHART_DEFAULTS.scales.y,
             ticks: { ...CHART_DEFAULTS.scales.y.ticks,
                      callback: v => `${(v/1000).toFixed(0)}k` } }  // format trục Y: "35k" thay vì "35000"
      }
    }
  });
}
