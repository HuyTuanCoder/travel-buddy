import axios from 'axios'
import config from '@/utils/config'

const API_URL = config.apiUrl ?? 'http://localhost:8000'

const api = axios.create({
  baseURL: API_URL,
  withCredentials: true,
})

api.interceptors.request.use(
  (requestConfig) => {
    const isAuthEndpoint =
      requestConfig.url?.includes('/auth/register') ||
      requestConfig.url?.includes('/auth/login')

    if (!isAuthEndpoint) {
      const token = localStorage.getItem('access_token')
      if (token) {
        requestConfig.headers.Authorization = `Bearer ${token}`
      }
    }

    return requestConfig
  },
  (error) => Promise.reject(error),
)

export default api
