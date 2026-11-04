import { defineStore } from 'pinia'

import { http } from './http'

export type UserRole = 'student' | 'mentor' | 'admin'
export interface TokenPair {
  access_token: string
  refresh_token: string
  role: UserRole
}

const ACCESS_KEY = 'career.access_token'
const REFRESH_KEY = 'career.refresh_token'
const ROLE_KEY = 'career.role'

export const useSessionStore = defineStore('session', {
  state: () => ({
    accessToken: localStorage.getItem(ACCESS_KEY) as string | null,
    refreshToken: localStorage.getItem(REFRESH_KEY) as string | null,
    role: localStorage.getItem(ROLE_KEY) as UserRole | null,
  }),
  getters: {
    authenticated: (state) => Boolean(state.accessToken),
  },
  actions: {
    applyTokens(tokens: TokenPair) {
      this.accessToken = tokens.access_token
      this.refreshToken = tokens.refresh_token
      this.role = tokens.role
      localStorage.setItem(ACCESS_KEY, tokens.access_token)
      localStorage.setItem(REFRESH_KEY, tokens.refresh_token)
      localStorage.setItem(ROLE_KEY, tokens.role)
    },
    async login(identifier: string, password: string) {
      const response = await http.post<TokenPair>('/auth/login', { identifier, password })
      this.applyTokens(response.data)
    },
    async logout() {
      const token = this.refreshToken
      try {
        if (token) await http.post('/auth/logout', { refresh_token: token })
      } finally {
        this.clear()
      }
    },
    clear() {
      this.accessToken = null
      this.refreshToken = null
      this.role = null
      localStorage.removeItem(ACCESS_KEY)
      localStorage.removeItem(REFRESH_KEY)
      localStorage.removeItem(ROLE_KEY)
    },
  },
})
