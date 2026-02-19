// Analytics — Chart.js visualizations

function initAnalytics(funnelData, emailData, sentimentData, throughputData) {
  // Conversion Funnel
  const funnelCtx = document.getElementById('funnel-chart');
  if (funnelCtx) {
    new Chart(funnelCtx, {
      type: 'bar',
      data: {
        labels: ['Qualified', 'Researched', 'Sites Built', 'Emailed', 'Replied'],
        datasets: [{
          data: [funnelData.qualified, funnelData.researched, funnelData.sites_built, funnelData.emailed, funnelData.replied],
          backgroundColor: ['#3b82f6', '#8b5cf6', '#d4922a', '#22c55e', '#f472b6'],
          borderRadius: 4,
        }],
      },
      options: {
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { color: '#1e293b' }, ticks: { color: '#64748b' } },
          y: { grid: { display: false }, ticks: { color: '#e2e8f0', font: { size: 12 } } },
        },
      },
    });
  }

  // Email Performance
  const emailCtx = document.getElementById('email-chart');
  if (emailCtx) {
    new Chart(emailCtx, {
      type: 'doughnut',
      data: {
        labels: ['Opened', 'Replied', 'Bounced', 'Pending'],
        datasets: [{
          data: [emailData.opened, emailData.replied, emailData.bounced, Math.max(0, emailData.sent - emailData.opened - emailData.bounced)],
          backgroundColor: ['#3b82f6', '#22c55e', '#ef4444', '#334155'],
          borderWidth: 0,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'bottom', labels: { color: '#94a3b8', padding: 12, font: { size: 11 } } },
        },
      },
    });
  }

  // Reply Sentiment
  const sentCtx = document.getElementById('sentiment-chart');
  if (sentCtx) {
    new Chart(sentCtx, {
      type: 'pie',
      data: {
        labels: ['Positive', 'Neutral', 'Negative', 'Out of Office'],
        datasets: [{
          data: [sentimentData.positive, sentimentData.neutral, sentimentData.negative, sentimentData.out_of_office],
          backgroundColor: ['#22c55e', '#64748b', '#ef4444', '#f59e0b'],
          borderWidth: 0,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'bottom', labels: { color: '#94a3b8', padding: 12, font: { size: 11 } } },
        },
      },
    });
  }

  // Throughput over time
  const tpCtx = document.getElementById('throughput-line');
  if (tpCtx) {
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
    new Chart(tpCtx, {
      type: 'line',
      data: {
        labels,
        datasets: [{
          label: 'Leads/Day',
          data: values,
          borderColor: '#d4922a',
          backgroundColor: '#d4922a22',
          fill: true,
          tension: 0.3,
          pointRadius: 2,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { color: '#1e293b' }, ticks: { color: '#64748b', maxTicksLimit: 10, font: { size: 10 } } },
          y: { grid: { color: '#1e293b' }, ticks: { color: '#64748b', stepSize: 1 }, beginAtZero: true },
        },
      },
    });
  }
}
