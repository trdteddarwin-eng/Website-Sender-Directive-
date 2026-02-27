const STORAGE_KEY = 'ketka_demo_last_start';
const COOLDOWN_MS = 15 * 60 * 1000; // 15 minutes

export function canStartDemo(): boolean {
  const last = localStorage.getItem(STORAGE_KEY);
  if (!last) return true;
  const elapsed = Date.now() - parseInt(last, 10);
  return elapsed >= COOLDOWN_MS;
}

export function recordDemoStart(): void {
  localStorage.setItem(STORAGE_KEY, Date.now().toString());
}

export function getRemainingCooldown(): number {
  const last = localStorage.getItem(STORAGE_KEY);
  if (!last) return 0;
  const elapsed = Date.now() - parseInt(last, 10);
  const remaining = COOLDOWN_MS - elapsed;
  return remaining > 0 ? Math.ceil(remaining / 1000) : 0;
}
