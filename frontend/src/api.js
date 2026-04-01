const API_BASE = '/api'
const BACKEND_PORT = __BACKEND_PORT__
// 支持环境变量配置，生产环境可通过 VITE_BACKEND_HOST 设置
const BACKEND_HOST = typeof __BACKEND_HOST__ !== 'undefined' ? __BACKEND_HOST__ : 'localhost'
const BASE_URL = `http://${BACKEND_HOST}:${BACKEND_PORT}`

/**
 * 统一的API请求处理函数
 * @param {string} url - 请求URL
 * @param {object} options - fetch选项
 * @returns {Promise<object>} - 返回data字段或抛出错误
 */
async function apiRequest(url, options = {}) {
  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      }
    })

    // 处理HTTP错误状态码
    if (!response.ok) {
      if (response.status === 404) {
        throw new Error('API接口不存在')
      } else if (response.status === 500) {
        throw new Error('服务器内部错误')
      } else if (response.status === 429) {
        throw new Error('请求过于频繁，请稍后再试')
      } else {
        throw new Error(`请求失败 (${response.status})`)
      }
    }

    const result = await response.json()

    // 处理统一的API响应格式
    if (result.success === false) {
      // 新格式：{ success: false, error: { code, message } }
      throw new Error(result.error?.message || '请求失败')
    }

    // 新格式返回data字段，旧格式直接返回整个对象
    if (result.success === true && result.data) {
      return result.data
    }

    // 兼容旧格式
    return result
  } catch (error) {
    // 网络错误处理
    if (error.name === 'TypeError' && error.message.includes('fetch')) {
      throw new Error('网络连接失败，请检查后端服务是否正常运行')
    }
    throw error
  }
}

export async function getInitStatus() {
  return apiRequest(`${BASE_URL}${API_BASE}/init-status`)
}

export async function calculateWeightedReturn(formula, limit) {
  return apiRequest(`${BASE_URL}${API_BASE}/weighted-return/calculate`, {
    method: 'POST',
    body: JSON.stringify({ formula, limit })
  })
}

export async function getWeightedReturnHeatmap(formula, days = 10) {
  return apiRequest(`${BASE_URL}${API_BASE}/weighted-return/heatmap`, {
    method: 'POST',
    body: JSON.stringify({ formula, days })
  })
}

export async function updateData() {
  return apiRequest(`${BASE_URL}${API_BASE}/update-data`, {
    method: 'POST'
  })
}

export async function getUpdateStatus() {
  return apiRequest(`${BASE_URL}${API_BASE}/update-status`)
}

export async function cancelUpdate() {
  return apiRequest(`${BASE_URL}${API_BASE}/cancel-update`, {
    method: 'POST'
  })
}

export async function getLatestDate() {
  return apiRequest(`${BASE_URL}${API_BASE}/latest-date`)
}

export async function calculateWeightedRank(formula, limit) {
  return apiRequest(`${BASE_URL}${API_BASE}/weighted-rank/calculate`, {
    method: 'POST',
    body: JSON.stringify({ formula, limit })
  })
}

export async function getWeightedRankHeatmap(formula, days = 10) {
  return apiRequest(`${BASE_URL}${API_BASE}/weighted-rank/heatmap`, {
    method: 'POST',
    body: JSON.stringify({ formula, days })
  })
}