export const API_URL = (
  import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'
).replace(/\/$/, '')

export async function getHealth() {
  const res = await fetch(`${API_URL}/health`)
  if (!res.ok) throw new Error('API not healthy')
  return res.json()
}

export async function getConfig() {
  const res = await fetch(`${API_URL}/config`)
  if (!res.ok) throw new Error('Could not load config')
  return res.json()
}

// FastAPI returns detail as a string, or as a list of validation errors (422)
function formatDetail(detail) {
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return detail
      .map((d) => `${(d.loc || []).slice(1).join('.')}: ${d.msg}`)
      .join('; ')
  }
  return 'The request was rejected.'
}

export async function analyze(before, after, s, signal) {
  const form = new FormData()
  form.append('before', before)
  form.append('after', after)
  form.append('method', s.method)
  form.append('blur', s.blur)
  form.append('threshold', s.autoThreshold ? '' : s.threshold) // empty = Otsu
  form.append('min_area', s.minArea)
  form.append('max_width', s.maxWidth)
  form.append('align', s.align)
  form.append('normalize', s.normalize)

  let res
  try {
    res = await fetch(`${API_URL}/analyze`, { method: 'POST', body: form, signal })
  } catch (e) {
    if (e.name === 'AbortError') throw e
    throw new Error(`Cannot reach the API at ${API_URL}. Is the backend running?`)
  }

  if (!res.ok) {
    let message = `Request failed (${res.status}).`
    try {
      const body = await res.json()
      if (body.detail) message = formatDetail(body.detail)
    } catch {
      /* keep the generic message */
    }
    throw new Error(message)
  }
  return res.json()
}