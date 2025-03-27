import axios from 'axios'

export const API_BASE_URL = 'http://localhost:5000'

// Axios instance with auth header
export const authAxios = axios.create({
  baseURL: API_BASE_URL
})

// Add request interceptor
authAxios.interceptors.request.use(config => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})