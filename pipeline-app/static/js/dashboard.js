// Dashboard — throughput chart
function initDashboard(throughputData) {
  const ctx = document.getElementById('throughput-chart');
  if (!ctx) return;

  // Build last 30 days labels
  const labels = [];
  const values = [];
  const now = new Date();
  for (let i = 29; i >= 0; i--) {
    const d = new Date(now);
    d.setDate(d.getDate() - i);
    const key = d.toISOString().slice(0, 10);
    labels.push(d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }));
    values.push(throughputData[key] || 0);
  }

  new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [{
        label: 'Leads Processed',
        data: values,
        backgroundColor: '#d4922a44',
        borderColor: '#d4922a',
        borderWidth: 1,
        borderRadius: 3,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: {
          grid: { color: '#1e293b' },
          ticks: { color: '#64748b', maxTicksLimit: 10, font: { size: 10 } },
        },
        y: {
          grid: { color: '#1e293b' },
          ticks: { color: '#64748b', stepSize: 1 },
          beginAtZero: true,
        },
      },
    },
  });
}
