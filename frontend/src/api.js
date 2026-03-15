const API_BASE = '/api'
const BACKEND_PORT = __BACKEND_PORT__
const BASE_URL = `http://localhost:${BACKEND_PORT}`

export async function getInitStatus() {
  const response = await fetch(`${BASE_URL}${API_BASE}/init-status`)
  return response.json()
}

export async function calculateWeightedReturn(formula, limit) {
  const response = await fetch(`${BASE_URL}${API_BASE}/weighted-return/calculate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ formula, limit })
  })
  return response.json()
}

export async function getWeightedReturnHeatmap(formula, days = 10) {
  const response = await fetch(`${BASE_URL}${API_BASE}/weighted-return/heatmap`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ formula, days })
  })
  return response.json()
}

export async function updateData(action = 'incremental') {
  const response = await fetch(`${BASE_URL}${API_BASE}/update-data`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ action })
  })
  return response.json()
}

export async function getUpdateStatus() {
  const response = await fetch(`${BASE_URL}${API_BASE}/update-status`)
  return response.json()
}

export async function cancelUpdate() {
  const response = await fetch(`${BASE_URL}${API_BASE}/cancel-update`, {
    method: 'POST'
  })
  return response.json()
}

export async function getLatestDate() {
  const response = await fetch(`${BASE_URL}${API_BASE}/latest-date`)
  return response.json()
}