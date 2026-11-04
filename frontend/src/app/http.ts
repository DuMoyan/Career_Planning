import axios, { AxiosError, type AxiosRequestConfig } from 'axios'

const ACCESS_KEY = 'career.access_token'
const REFRESH_KEY = 'career.refresh_token'
const ROLE_KEY = 'career.role'

export async function withSingleRefresh<T>(
  request: () => Promise<T>,
  retry: () => Promise<T>,
  refresh: () => Promise<void>,
  logout: () => void,
): Promise<T> {
  try {
    return await request()
  } catch (error) {
    if ((error as AxiosError).response?.status !== 401) throw error
    try {
      await refresh()
      return await retry()
    } catch (refreshError) {
      logout()
      throw refreshError
    }
  }
}

export const http = axios.create({ baseURL: '/api/v1', timeout: 15_000 })

http.interceptors.request.use((config) => {
  const token = localStorage.getItem(ACCESS_KEY)
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

type RetryConfig = AxiosRequestConfig & { _careerRetried?: boolean }

http.interceptors.response.use(undefined, async (error: AxiosError) => {
  const config = error.config as RetryConfig | undefined
  const refreshToken = localStorage.getItem(REFRESH_KEY)
  if (error.response?.status !== 401 || !config || config._careerRetried || !refreshToken) {
    return Promise.reject(error)
  }
  config._careerRetried = true
  try {
    const response = await axios.post('/api/v1/auth/refresh', { refresh_token: refreshToken })
    localStorage.setItem(ACCESS_KEY, response.data.access_token)
    localStorage.setItem(REFRESH_KEY, response.data.refresh_token)
    localStorage.setItem(ROLE_KEY, response.data.role)
    config.headers = { ...config.headers, Authorization: `Bearer ${response.data.access_token}` }
    return http.request(config)
  } catch (refreshError) {
    localStorage.removeItem(ACCESS_KEY)
    localStorage.removeItem(REFRESH_KEY)
    localStorage.removeItem(ROLE_KEY)
    return Promise.reject(refreshError)
  }
})
