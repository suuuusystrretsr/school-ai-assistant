export function toReadableError(detail: unknown, fallback: string): string {
  if (typeof detail === 'string' && detail.trim()) {
    return detail;
  }

  if (Array.isArray(detail)) {
    const parts = detail
      .map((item) => {
        if (typeof item === 'string') return item;
        if (item && typeof item === 'object') {
          const msg = (item as { msg?: unknown }).msg;
          if (typeof msg === 'string' && msg.trim()) return msg;
        }
        return null;
      })
      .filter((v): v is string => Boolean(v));

    if (parts.length) return parts.join(', ');
  }

  if (detail && typeof detail === 'object') {
    const msg = (detail as { msg?: unknown }).msg;
    if (typeof msg === 'string' && msg.trim()) {
      return msg;
    }
  }

  return fallback;
}
