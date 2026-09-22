import { useEffect, useState } from 'react'
import { apiGet } from './api'

// Polls a JSON endpoint every `ms` milliseconds.
// Returns { data, error, loading }.

export function usePoll(path, ms = 1500) {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    let timer = null

    async function tick() {
      try {
        const json = await apiGet(path)
        if (!cancelled) {
          setData(json)
          setError(null)
          setLoading(false)
        }
      } catch (e) {
        if (!cancelled) {
          setError(e.message || String(e))
          setLoading(false)
        }
      } finally {
        if (!cancelled) {
          timer = setTimeout(tick, ms)
        }
      }
    }

    tick()
    return () => {
      cancelled = true
      if (timer) clearTimeout(timer)
    }
  }, [path, ms])

  return { data, error, loading }
}
