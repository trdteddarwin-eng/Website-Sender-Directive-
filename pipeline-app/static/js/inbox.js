// TedCA Inbox — Client-side logic

let currentAccount = '';
let currentMessages = [];
let currentOffset = 0;
let currentUid = '';
const PAGE_SIZE = 50;

// ── Account selection ──────────────────────────────────

function selectAccount(email) {
  currentAccount = email;
  currentOffset = 0;
  currentMessages = [];
  currentUid = '';

  // Update active state
  document.querySelectorAll('.inbox-account-card').forEach(c => {
    c.classList.toggle('active', c.dataset.email === email);
  });

  document.getElementById('inbox-layout').style.display = '';
  document.getElementById('reading-pane').innerHTML = `
    <div class="inbox-reading-empty">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" width="48" height="48" style="opacity:0.3"><polyline points="22 12 16 12 14 15 10 15 8 12 2 12"/><path d="M5.45 5.11L2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"/></svg>
      <p style="color:var(--text-dim);margin-top:12px">Select a message to read</p>
    </div>`;

  loadMessages();
}

// ── Load messages ──────────────────────────────────────

async function loadMessages() {
  const list = document.getElementById('message-list');
  if (currentOffset === 0) {
    list.innerHTML = '<div class="inbox-loading"><div class="spinner"></div></div>';
  }

  try {
    const r = await fetch(`/api/inbox/messages?account=${encodeURIComponent(currentAccount)}&offset=${currentOffset}&limit=${PAGE_SIZE}`);
    const d = await r.json();

    if (!d.ok) {
      list.innerHTML = `<div class="empty-state"><p>${escapeHtml(d.error || 'Error loading messages')}</p></div>`;
      return;
    }

    if (currentOffset === 0) {
      currentMessages = d.messages;
    } else {
      currentMessages = currentMessages.concat(d.messages);
    }

    renderMessageList();

    // Show/hide load more
    const wrap = document.getElementById('load-more-wrap');
    wrap.style.display = d.messages.length >= PAGE_SIZE ? '' : 'none';
  } catch (e) {
    list.innerHTML = `<div class="empty-state"><p>Connection error</p></div>`;
  }
}

function loadMore() {
  currentOffset += PAGE_SIZE;
  loadMessages();
}

// ── Render message list ────────────────────────────────

function renderMessageList() {
  const list = document.getElementById('message-list');
  const filter = (document.getElementById('inbox-search').value || '').toLowerCase();

  const filtered = filter
    ? currentMessages.filter(m =>
        (m.from_name || '').toLowerCase().includes(filter) ||
        (m.from_email || '').toLowerCase().includes(filter) ||
        (m.subject || '').toLowerCase().includes(filter))
    : currentMessages;

  if (filtered.length === 0) {
    list.innerHTML = '<div class="empty-state"><p>No messages</p></div>';
    return;
  }

  list.innerHTML = filtered.map(m => `
    <div class="inbox-msg-row ${m.seen ? '' : 'unread'} ${m.uid === currentUid ? 'selected' : ''}"
         data-uid="${escapeHtml(m.uid)}" onclick="openMessage('${escapeHtml(m.uid)}')">
      <div class="inbox-msg-dot">${m.seen ? '' : '<span></span>'}</div>
      <div class="inbox-msg-content">
        <div class="inbox-msg-from">${escapeHtml(m.from_name || m.from_email)}</div>
        <div class="inbox-msg-subject">${escapeHtml(m.subject || '(no subject)')}</div>
      </div>
      <div class="inbox-msg-date">${formatDate(m.date)}</div>
    </div>
  `).join('');
}

function filterMessages() {
  renderMessageList();
}

// ── Open message ───────────────────────────────────────

async function openMessage(uid) {
  currentUid = uid;
  renderMessageList(); // Update selected state

  const pane = document.getElementById('reading-pane');
  pane.innerHTML = '<div class="inbox-loading"><div class="spinner"></div></div>';

  try {
    const r = await fetch(`/api/inbox/message?account=${encodeURIComponent(currentAccount)}&uid=${uid}`);
    const d = await r.json();

    if (!d.ok) {
      pane.innerHTML = `<div class="empty-state"><p>${escapeHtml(d.error || 'Error')}</p></div>`;
      return;
    }

    const msg = d.message;

    // Mark as read locally
    const localMsg = currentMessages.find(m => m.uid === uid);
    if (localMsg && !localMsg.seen) {
      localMsg.seen = true;
      renderMessageList();
      // Mark read on server (fire and forget)
      fetch('/api/inbox/mark', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({account: currentAccount, uid: uid, action: 'read'})
      });
      updateBadge(currentAccount, -1);
    }

    const body = msg.html || `<pre style="white-space:pre-wrap;font-family:inherit">${escapeHtml(msg.text || '(empty)')}</pre>`;

    pane.innerHTML = `
      <div class="inbox-reading-header">
        <div class="inbox-reading-subject">${escapeHtml(msg.subject)}</div>
        <div class="inbox-reading-meta">
          <span><strong>From:</strong> ${escapeHtml(msg.from_name)} &lt;${escapeHtml(msg.from_email)}&gt;</span>
          <span><strong>To:</strong> ${escapeHtml(msg.to)}</span>
          <span><strong>Date:</strong> ${formatDateFull(msg.date)}</span>
        </div>
        <div class="inbox-reading-actions">
          <button class="btn btn-ghost btn-sm" onclick="markUnread('${escapeHtml(uid)}')">Mark Unread</button>
          <button class="btn btn-danger btn-sm" onclick="deleteMsg('${escapeHtml(uid)}')">Delete</button>
        </div>
      </div>
      <div class="inbox-reading-body">
        <iframe id="email-frame" sandbox="allow-same-origin" srcdoc="${escapeAttr(body)}"></iframe>
      </div>`;

    // Auto-resize iframe
    const frame = document.getElementById('email-frame');
    frame.onload = () => {
      try {
        frame.style.height = frame.contentDocument.body.scrollHeight + 20 + 'px';
      } catch(e) {}
    };
  } catch (e) {
    pane.innerHTML = '<div class="empty-state"><p>Connection error</p></div>';
  }
}

// ── Actions ────────────────────────────────────────────

async function markUnread(uid) {
  try {
    await fetch('/api/inbox/mark', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({account: currentAccount, uid: uid, action: 'unread'})
    });
    const msg = currentMessages.find(m => m.uid === uid);
    if (msg) msg.seen = false;
    renderMessageList();
    updateBadge(currentAccount, 1);
    showToast('Marked as unread', 'info');
  } catch (e) {
    showToast('Error marking unread', 'error');
  }
}

async function deleteMsg(uid) {
  if (!confirm('Delete this message?')) return;
  try {
    await fetch('/api/inbox/delete', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({account: currentAccount, uid: uid})
    });
    currentMessages = currentMessages.filter(m => m.uid !== uid);
    currentUid = '';
    renderMessageList();
    document.getElementById('reading-pane').innerHTML = `
      <div class="inbox-reading-empty">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" width="48" height="48" style="opacity:0.3"><polyline points="22 12 16 12 14 15 10 15 8 12 2 12"/><path d="M5.45 5.11L2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"/></svg>
        <p style="color:var(--text-dim);margin-top:12px">Message deleted</p>
      </div>`;
    showToast('Message deleted', 'success');
  } catch (e) {
    showToast('Error deleting message', 'error');
  }
}

function refreshAll() {
  if (currentAccount) {
    currentOffset = 0;
    currentMessages = [];
    loadMessages();
  }
  // Refresh badges
  fetchBadges();
}

// ── Badge management ───────────────────────────────────

function updateBadge(email, delta) {
  const badge = document.getElementById('badge-' + email);
  if (!badge) return;
  let count = parseInt(badge.textContent || '0') + delta;
  if (count < 0) count = 0;
  badge.textContent = count;
  badge.style.display = count > 0 ? '' : 'none';

  // Also update sidebar badge
  const sidebarBadge = document.getElementById('inbox-badge');
  if (sidebarBadge) {
    let total = parseInt(sidebarBadge.textContent || '0') + delta;
    if (total < 0) total = 0;
    sidebarBadge.textContent = total;
    sidebarBadge.style.display = total > 0 ? '' : 'none';
  }
}

async function fetchBadges() {
  try {
    const r = await fetch('/api/inbox/unread-total');
    const d = await r.json();
    if (d.ok) {
      for (const [email, count] of Object.entries(d.counts)) {
        const badge = document.getElementById('badge-' + email);
        if (badge) {
          badge.textContent = count;
          badge.style.display = count > 0 ? '' : 'none';
        }
      }
      const sidebarBadge = document.getElementById('inbox-badge');
      if (sidebarBadge) {
        sidebarBadge.textContent = d.total;
        sidebarBadge.style.display = d.total > 0 ? '' : 'none';
      }
    }
  } catch(e) {}
}

// ── SSE: live updates ──────────────────────────────────

(function initSSE() {
  const es = new EventSource('/inbox/stream');

  es.addEventListener('new_email', function(e) {
    try {
      const data = JSON.parse(e.data);
      showToast(`New email from ${data.from_name || data.from_email}: ${data.subject}`, 'info');

      // Update badge
      updateBadge(data.account, 1);

      // If this account is selected, prepend to list
      if (data.account === currentAccount) {
        currentMessages.unshift({
          uid: data.uid,
          from_name: data.from_name || '',
          from_email: data.from_email || '',
          subject: data.subject || '',
          date: new Date().toISOString(),
          seen: false,
        });
        renderMessageList();
      }
    } catch(err) {}
  });

  es.onerror = function() {
    // Reconnect handled by EventSource automatically
  };
})();

// ── Helpers ────────────────────────────────────────────

function escapeHtml(s) {
  if (!s) return '';
  const div = document.createElement('div');
  div.textContent = s;
  return div.innerHTML;
}

function escapeAttr(s) {
  if (!s) return '';
  return s.replace(/&/g,'&amp;').replace(/"/g,'&quot;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

function formatDate(isoStr) {
  if (!isoStr) return '';
  try {
    const d = new Date(isoStr);
    const now = new Date();
    // Today: show time
    if (d.toDateString() === now.toDateString()) {
      return d.toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'});
    }
    // This year: show month/day
    if (d.getFullYear() === now.getFullYear()) {
      return d.toLocaleDateString([], {month: 'short', day: 'numeric'});
    }
    // Older
    return d.toLocaleDateString([], {month: 'short', day: 'numeric', year: 'numeric'});
  } catch(e) { return isoStr; }
}

function formatDateFull(isoStr) {
  if (!isoStr) return '';
  try {
    return new Date(isoStr).toLocaleString([], {
      weekday: 'short', month: 'short', day: 'numeric', year: 'numeric',
      hour: '2-digit', minute: '2-digit'
    });
  } catch(e) { return isoStr; }
}
