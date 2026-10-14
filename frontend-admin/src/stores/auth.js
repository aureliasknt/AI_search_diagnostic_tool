import axios from 'axios'
import { reactive, readonly } from 'vue'

const state = reactive({
  token: localStorage.getItem('admin_token') || '',
  role: localStorage.getItem('admin_role') || '',
  username: localStorage.getItem('admin_username') || '',
})

export const client = axios.create({ baseURL: '/api' })
client.interceptors.request.use((cfg) => {
  if (state.token) cfg.headers.Authorization = `Bearer ${state.token}`
  return cfg
})
client.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err?.response?.status === 401) useAuth().logout()
    return Promise.reject(err)
  },
)

export function useAuth() {
  return {
    get token() { return state.token },
    get role() { return state.role },
    get username() { return state.username },
    async login(username, password) {
      const { data } = await client.post('/auth/login', { username, password })
      state.token = data.token
      state.role = data.role
      state.username = data.username
      localStorage.setItem('admin_token', data.token)
      localStorage.setItem('admin_role', data.role)
      localStorage.setItem('admin_username', data.username)
    },
    logout() {
      state.token = state.role = state.username = ''
      localStorage.removeItem('admin_token')
      localStorage.removeItem('admin_role')
      localStorage.removeItem('admin_username')
      if (location.pathname !== '/login') location.href = '/login'
    },
  }
}

export const authState = readonly(state)
