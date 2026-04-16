import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '../router'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
})

api.interceptors.request.use(config => {
  const token = sessionStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      sessionStorage.removeItem('access_token')
      sessionStorage.removeItem('user')
      router.push('/login')
      ElMessage.error('登录已过期，请重新登录')
    } else {
      const data = error.response?.data
      let msg = '请求失败'
      if (data) {
        if (typeof data.detail === 'string') {
          msg = data.detail
        } else {
          // DRF 字段级验证错误: { field: ["error1", ...], ... }
          const parts = []
          for (const [key, val] of Object.entries(data)) {
            const errors = Array.isArray(val) ? val.join('；') : val
            parts.push(`${key}: ${errors}`)
          }
          if (parts.length) msg = parts.join('\n')
        }
      }
      ElMessage.error(msg)
    }
    return Promise.reject(error)
  }
)

export default api
