// Lead detail — tabs + actions
document.addEventListener('DOMContentLoaded', function() {
  // Tab switching
  document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
      const target = tab.dataset.tab;
      document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
      tab.classList.add('active');
      document.getElementById('tab-' + target)?.classList.add('active');
    });
  });

  // Load research data
  loadResearch();
});

async function loadResearch() {
  const el = document.getElementById('research-data');
  if (!el) return;
  const slug = el.dataset.slug;
  if (!slug) return;

  try {
    const data = await apiGet(`/api/leads/${slug}/research`);
    if (data.error) {
      el.innerHTML = '<p class="text-dim">No research data available. Run the pipeline first.</p>';
      return;
    }

    let html = '';
    if (data.pain_points && data.pain_points.length) {
      html += '<h4 style="margin-bottom: 8px; color: var(--accent);">Pain Points</h4><ul style="margin-bottom: 16px; padding-left: 18px;">';
      data.pain_points.forEach(p => { html += `<li style="margin-bottom: 4px;">${p}</li>`; });
      html += '</ul>';
    }
    if (data.roi_estimate) {
      html += `<h4 style="margin-bottom: 8px; color: var(--accent);">ROI Estimate</h4><p style="margin-bottom: 16px;">${data.roi_estimate}</p>`;
    }
    if (data.services && data.services.length) {
      html += '<h4 style="margin-bottom: 8px; color: var(--accent);">Services</h4><p style="margin-bottom: 16px;">' + data.services.join(', ') + '</p>';
    }
    if (data.icebreaker) {
      html += `<h4 style="margin-bottom: 8px; color: var(--accent);">Icebreaker</h4><p style="margin-bottom: 16px;">${data.icebreaker}</p>`;
    }
    if (data.reviews) {
      const reviews = data.reviews;
      if (reviews.average_rating) {
        html += `<h4 style="margin-bottom: 8px; color: var(--accent);">Google Reviews</h4><p>Rating: ${reviews.average_rating}/5 (${reviews.review_count || '?'} reviews)</p>`;
      }
    }
    el.innerHTML = html || '<p class="text-dim">Research data loaded but appears empty.</p>';
  } catch(e) {
    el.innerHTML = '<p class="text-dim">Failed to load research data.</p>';
  }
}

async function skipEmail(emailId) {
  if (!confirm('Skip this email?')) return;
  const data = await apiPost(`/api/emails/${emailId}/skip`);
  if (data.ok) {
    showToast('Email skipped', 'info');
    setTimeout(() => location.reload(), 500);
  }
}
