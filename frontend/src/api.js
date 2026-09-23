// Tiny fetch wrapper. The Vite dev server proxies /api -> :8000.

async function call(path, opts = {}) {
  const res = await fetch(path, {
    headers: { 'Content-Type': 'application/json' },
    ...opts,
  })
  if (!res.ok) {
    let detail = res.statusText
    let code = null
    try {
      const body = await res.json()
      if (body && body.detail) {
        detail = typeof body.detail === 'object' ? body.detail.message : body.detail
        code = typeof body.detail === 'object' ? body.detail.code : null
      }
    } catch (_) {
      // not JSON
    }
    const error = new Error(`${res.status} ${detail}`)
    error.status = res.status
    error.code = code
    throw error
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
