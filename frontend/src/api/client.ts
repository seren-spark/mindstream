import axios, { type AxiosInstance, type AxiosRequestConfig } from 'axios'
import { getErrorMessage, parseApiError, type ApiErrorResponse } from '@/types/api'

const http: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 10000,
  headers: {
    Accept: 'application/json',
  },
})

http.interceptors.response.use(
  (response) => response,
  (error) => {
    const parsed = parseApiError(error)
    console.error('[API Error]', parsed.code ?? error.response?.status, parsed.detail)
    return Promise.reject(error)
  },
)

/** 类型安全的 GET — T 为 response.data 的类型 */
export async function apiGet<T>(url: string, config?: AxiosRequestConfig) {
  const { data } = await http.get<T>(url, config)
  return data
}

export async function apiPost<T>(url: string, body?: unknown, config?: AxiosRequestConfig) {
  const { data } = await http.post<T>(url, body, config)
  return data
}

export async function apiPut<T>(url: string, body?: unknown, config?: AxiosRequestConfig) {
  const { data } = await http.put<T>(url, body, config)
  return data
}

export async function apiPatch<T>(url: string, body?: unknown, config?: AxiosRequestConfig) {
  const { data } = await http.patch<T>(url, body, config)
  return data
}

export async function apiDelete<T = void>(url: string, config?: AxiosRequestConfig) {
  const { data } = await http.delete<T>(url, config)
  return data
}

export { http, parseApiError, getErrorMessage, type ApiErrorResponse }
export default http
