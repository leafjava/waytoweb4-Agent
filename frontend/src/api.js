// Tiny fetch wrapper. The Vite dev server proxies /api -> :8000.

async function call(path, opts = {}) {
  const res = await fetch(path, {
    headers: { 'Content-Type': 'application/json' },
    ...opts,
  })
  if (!res.ok) {
    let detail = res.statusText
    try {
      const body = await res.json()
      if (body && body.detail) detail = body.detail
    } catch (_) {
      // not JSON
    }
    throw new Error(`${res.status} ${detail}`)
  }
  return res.json()
}

export function apiGet(path) {
  return call(path, { method: 'GET' })
}

export function apiPost(path, body) {
  return call(path, {
    method: 'POST',
    body: body == null ? null : JSON.stringify(body),
  })
}
