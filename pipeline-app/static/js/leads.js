// Leads page — filter, sort, search
document.addEventListener('DOMContentLoaded', function() {
  const form = document.getElementById('leads-filters');
  if (!form) return;

  // Auto-submit on filter change
  form.querySelectorAll('select').forEach(el => {
    el.addEventListener('change', () => form.submit());
  });

  // Debounced search
  let searchTimeout;
  const searchInput = form.querySelector('input[name="search"]');
  if (searchInput) {
    searchInput.addEventListener('input', () => {
      clearTimeout(searchTimeout);
      searchTimeout = setTimeout(() => form.submit(), 500);
    });
  }
});

// Sort by column
function sortLeads(column) {
  const params = new URLSearchParams(window.location.search);
  const currentSort = params.get('sort');
  const currentDir = params.get('dir') || 'desc';

  if (currentSort === column) {
    params.set('dir', currentDir === 'desc' ? 'asc' : 'desc');
  } else {
    params.set('sort', column);
    params.set('dir', 'desc');
  }
  params.set('page', '1');
  window.location.search = params.toString();
}

// Run pipeline for a specific lead
async function runPipelineFor(slug) {
  if (!confirm(`Run pipeline for ${slug}?`)) return;
  const data = await apiPost('/api/pipeline/run', { slug });
  if (data.ok) {
    showToast(`Pipeline started for ${slug}`, 'success');
    setTimeout(() => window.location.href = '/pipeline', 1000);
  } else {
    showToast(data.error || 'Failed to start pipeline', 'error');
  }
}
