import axios from 'axios'

const client = axios.create({ baseURL: '/api', timeout: 30000 })

export function getSummary(code) {
  return client.get(`/r/${code}`)
}

export function guessCompany(companyName) {
  return client.post('/diagnose/guess', { company_name: companyName })
}

export function startDiagnosis(payload) {
  return client.post('/diagnose', { ...payload, website: '' })
}

export function sendCode(code, phone) {
  return client.post(`/r/${code}/send-code`, { phone })
}

export function verify(code, payload) {
  return client.post(`/r/${code}/verify`, payload)
}

export function getFull(code, token) {
  return client.get(`/r/${code}/full`, { params: { token } })
}

export function pdfUrl(code, token) {
  return `/api/r/${code}/pdf?token=${encodeURIComponent(token)}`
}

export const tokenKey = (code) => `unlock:${code}`

export function getToken(code) {
  return localStorage.getItem(tokenKey(code)) || ''
}

export function setToken(code, token) {
  localStorage.setItem(tokenKey(code), token)
}
