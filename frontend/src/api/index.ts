import axios from 'axios'

const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 10000,
})

http.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('[API Error]', error)
    return Promise.reject(error)
  },
)

export default http
