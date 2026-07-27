const jsonHeaders = { 'Content-Type': 'application/json' }

async function read(res) {
  const data = await res.json().catch(() => ({}))
  if (!res.ok) throw new Error(data.detail || 'AIVOA could not complete this request.')
  return data
}

export const sendMessage = (payload) => fetch('/api/copilot', {method:'POST', headers:jsonHeaders, body:JSON.stringify(payload)}).then(read)
export const uploadDocument = (file) => { const body = new FormData(); body.append('file', file); return fetch('/api/documents', {method:'POST', body}).then(read) }
export const commitComplaint = (payload) => fetch('/api/complaints', {method:'POST', headers:jsonHeaders, body:JSON.stringify(payload)}).then(read)

