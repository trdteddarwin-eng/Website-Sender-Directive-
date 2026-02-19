// Sequences page

async function pauseSequence(seqId) {
  const data = await apiPost(`/api/sequences/${seqId}/pause`);
  if (data.ok) { showToast('Sequence paused', 'info'); location.reload(); }
  else showToast(data.error || 'Failed', 'error');
}

async function resumeSequence(seqId) {
  const data = await apiPost(`/api/sequences/${seqId}/resume`);
  if (data.ok) { showToast('Sequence resumed', 'success'); location.reload(); }
  else showToast(data.error || 'Failed', 'error');
}

async function skipEmailInSeq(emailId) {
  const data = await apiPost(`/api/emails/${emailId}/skip`);
  if (data.ok) { showToast('Email skipped', 'info'); location.reload(); }
  else showToast(data.error || 'Failed', 'error');
}
