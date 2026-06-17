/* ════════════════════════════════════════════════════════════════
   Charts — Chart.js wrappers
   ════════════════════════════════════════════════════════════════ */

const CHART_DEFAULTS = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      labels: {
        color: '#94a3b8',
        font: { family: 'Segoe UI', size: 12 },
        usePointStyle: true,
        pointStyleWidth: 8,
        padding: 16
      }
    },
    tooltip: {
      backgroundColor: 'rgba(4,15,38,0.96)',
      borderColor: 'rgba(0,212,255,0.2)',
      borderWidth: 1,
      titleColor: '#f0f6ff',
      bodyColor: '#94a3b8',
      padding: 12,
      cornerRadius: 8,
      titleFont: { family: 'Segoe UI', weight: 700, size: 13 },
      bodyFont: { family: 'Segoe UI', size: 12 },
    }
  },
  scales: {
    x: {
      grid: { color: 'rgba(255,255,255,0.04)' },
      ticks: { color: '#64748b', font: { family: 'Segoe UI', size: 11 } },
    },
    y: {
      grid: { color: 'rgba(255,255,255,0.04)' },
      ticks: { color: '#64748b', font: { family: 'Segoe UI', size: 11 } },
    }
  }
};

/* Active chart instances (so we can destroy & recreate) */
const Charts = {};

function destroyChart(key) {
  if (Charts[key]) { Charts[key].destroy(); delete Charts[key]; }
}

/* ─── Daily kWh line chart ────────────────────────────────────── */
function renderDailyChart(daily) {
  destroyChart('daily');
  const ctx = document.getElementById('chartDaily');
  if (!ctx) return;
  const labels  = daily.map(d => fmt.date(d.date));
  const dataKwh = daily.map(d => d.kwh);
  const budget  = daily.map(() => parseFloat(document.getElementById('budgetDisplay')?.dataset?.budget || 2));

  Charts.daily = new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [
        {
          label: 'Tiêu thụ (kWh)',
          data: dataKwh,
          borderColor: '#00d4ff',
          backgroundColor: 'rgba(0,212,255,0.08)',
          borderWidth: 2.5,
          pointBackgroundColor: '#00d4ff',
          pointRadius: 4,
          pointHoverRadius: 7,
          fill: true,
          tension: 0.4,
        },
        {
          label: 'Ngân sách',
          data: budget,
          borderColor: 'rgba(239,68,68,0.5)',
          borderWidth: 1.5,
          borderDash: [6, 3],
          pointRadius: 0,
          fill: false,
          tension: 0,
        }
      ]
    },
    options: {
      ...CHART_DEFAULTS,
      plugins: {
        ...CHART_DEFAULTS.plugins,
        tooltip: {
          ...CHART_DEFAULTS.plugins.tooltip,
          callbacks: {
            label: ctx => ctx.dataset.label + ': ' + ctx.parsed.y.toFixed(3) + ' kWh'
          }
        }
      },
      scales: {
        x: { ...CHART_DEFAULTS.scales.x },
        y: { ...CHART_DEFAULTS.scales.y, min: 0, title: { display: true, text: 'kWh', color: '#64748b' } }
      }
    }
  });
}

/* ─── Device donut ────────────────────────────────────────────── */
function renderDonutChart(byDevice) {
  destroyChart('donut');
  const ctx = document.getElementById('chartDonut');
  if (!ctx || !byDevice.length) return;
  const top = byDevice.slice(0, 7);
  const colors = ['#00d4ff','#7c3aed','#10b981','#f59e0b','#ef4444','#fb923c','#38bdf8'];
  Charts.donut = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: top.map(d => d.name),
      datasets: [{
        data: top.map(d => d.kwh),
        backgroundColor: colors,
        borderColor: 'rgba(0,0,0,0.3)',
        borderWidth: 2,
        hoverBorderWidth: 3,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '68%',
      plugins: {
        legend: {
          position: 'right',
          labels: { color: '#94a3b8', font: { size: 12 }, padding: 12, usePointStyle: true }
        },
        tooltip: {
          ...CHART_DEFAULTS.plugins.tooltip,
          callbacks: {
            label: ctx => `${ctx.label}: ${ctx.parsed.toFixed(3)} kWh`
          }
        }
      }
    }
  });
}

/* ─── Optimize compare bar chart ──────────────────────────────── */
function renderOptimizeChart(dp, greedy) {
  destroyChart('optimize');
  const ctx = document.getElementById('chartOptimize');
  if (!ctx) return;

  const dpNames   = dp.schedule.map(s => s.device.name);
  const grNames   = greedy.schedule.map(s => s.device.name);
  const allNames  = [...new Set([...dpNames, ...grNames])];

  const dpMap  = Object.fromEntries(dp.schedule.map(s => [s.device.name, s.comfort]));
  const grMap  = Object.fromEntries(greedy.schedule.map(s => [s.device.name, s.comfort]));

  Charts.optimize = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: allNames,
      datasets: [
        {
          label: 'DP (điểm thoải mái)',
          data: allNames.map(n => dpMap[n] || 0),
          backgroundColor: 'rgba(0,212,255,0.7)',
          borderColor: '#00d4ff',
          borderWidth: 1,
          borderRadius: 6,
        },
        {
          label: 'Greedy (điểm thoải mái)',
          data: allNames.map(n => grMap[n] || 0),
          backgroundColor: 'rgba(124,58,237,0.7)',
          borderColor: '#7c3aed',
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
        y: { ...CHART_DEFAULTS.scales.y, min: 0, title: { display: true, text: 'Điểm', color: '#64748b' } }
      }
    }
  });
}

/* ─── Forecast line chart ─────────────────────────────────────── */
function renderForecastChart(months) {
  destroyChart('forecast');
  const ctx = document.getElementById('chartForecast');
  if (!ctx) return;
  Charts.forecast = new Chart(ctx, {
    type: 'line',
    data: {
      labels: months.map(m => m.label),
      datasets: [
        {
          label: 'Dự báo tiêu thụ (kWh)',
          data: months.map(m => m.kwh),
          borderColor: '#00d4ff',
          backgroundColor: 'rgba(0,212,255,0.08)',
          borderWidth: 2.5,
          pointBackgroundColor: '#00d4ff',
          pointRadius: 5,
          fill: true,
          tension: 0.3,
          yAxisID: 'y',
        },
        {
          label: 'Chi phí EVN (1000 ₫)',
          data: months.map(m => m.evn / 1000),
          borderColor: '#f59e0b',
          backgroundColor: 'rgba(245,158,11,0.06)',
          borderWidth: 2,
          pointBackgroundColor: '#f59e0b',
          pointRadius: 5,
          fill: true,
          tension: 0.3,
          yAxisID: 'y1',
        }
      ]
    },
    options: {
      ...CHART_DEFAULTS,
      interaction: { mode: 'index', intersect: false },
      plugins: { ...CHART_DEFAULTS.plugins },
      scales: {
        x: { ...CHART_DEFAULTS.scales.x },
        y: { ...CHART_DEFAULTS.scales.y, title: { display: true, text: 'kWh', color: '#64748b' }, position: 'left' },
        y1: { ...CHART_DEFAULTS.scales.y, title: { display: true, text: '1000 ₫', color: '#64748b' }, position: 'right', grid: { drawOnChartArea: false } }
      }
    }
  });
}

/* ─── Device by category donut ────────────────────────────────── */
function renderCategoryChart(byDevice) {
  destroyChart('category');
  const ctx = document.getElementById('chartCategory');
  if (!ctx || !byDevice.length) return;

  const grouped = {};
  byDevice.forEach(d => {
    grouped[d.category] = (grouped[d.category] || 0) + d.kwh;
  });

  const labels = Object.keys(grouped).map(k => catLabel(k));
  const data   = Object.values(grouped);
  const colors = Object.keys(grouped).map(k => catColor(k));

  Charts.category = new Chart(ctx, {
    type: 'polarArea',
    data: {
      labels,
      datasets: [{
        data,
        backgroundColor: colors.map(c => c + '88'),
        borderColor: colors,
        borderWidth: 1.5,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'right',
          labels: { color: '#94a3b8', font: { size: 11 }, padding: 10 }
        },
        tooltip: {
          ...CHART_DEFAULTS.plugins.tooltip,
          callbacks: { label: ctx => `${ctx.label}: ${ctx.parsed.r.toFixed(2)} kWh` }
        }
      },
      scales: {
        r: {
          grid: { color: 'rgba(255,255,255,0.06)' },
          ticks: { color: '#64748b', font: { size: 10 }, backdropColor: 'transparent' }
        }
      }
    }
  });
}

/* ─── EVN breakdown bar ───────────────────────────────────────── */
function renderEvnChart(breakdown) {
  destroyChart('evn');
  const ctx = document.getElementById('chartEvn');
  if (!ctx) return;
  const tierColors = ['#10b981','#34d399','#f59e0b','#fb923c','#ef4444','#dc2626'];
  Charts.evn = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: breakdown.map(b => `Bậc ${b.bac}`),
      datasets: [{
        label: 'Chi phí (₫)',
        data: breakdown.map(b => b.cost),
        backgroundColor: tierColors.slice(0, breakdown.length),
        borderRadius: 6,
        borderSkipped: false,
      }]
    },
    options: {
      ...CHART_DEFAULTS,
      plugins: {
        ...CHART_DEFAULTS.plugins,
        tooltip: {
          ...CHART_DEFAULTS.plugins.tooltip,
          callbacks: {
            label: ctx => `${fmt.vndFull(ctx.parsed.y)} (${breakdown[ctx.dataIndex]?.kwh} kWh × ${breakdown[ctx.dataIndex]?.rate} ₫/kWh)`
          }
        }
      },
      scales: {
        x: { ...CHART_DEFAULTS.scales.x },
        y: { ...CHART_DEFAULTS.scales.y, ticks: { ...CHART_DEFAULTS.scales.y.ticks, callback: v => `${(v/1000).toFixed(0)}k` } }
      }
    }
  });
}
