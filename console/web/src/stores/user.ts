import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '../api'

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('token') || '')
  const user = ref<{ id: number; username: string; display_name: string; roles: string[] } | null>(null)

  const isLoggedIn = computed(() => !!token.value)
  const roles = computed(() => user.value?.roles || [])
  const isAdmin = computed(() => roles.value.includes('admin'))

  async function login(username: string, password: string) {
    const { data } = await api.post('/auth/login', { username, password })
    token.value = data.access_token
    localStorage.setItem('token', data.access_token)
    await fetchMe()
  }

  async function fetchMe() {
    const { data } = await api.get('/auth/me')
    user.value = data
  }

  function logout() {
    token.value = ''
    user.value = null
    localStorage.removeItem('token')
  }

  return { token, user, isLoggedIn, roles, isAdmin, login, fetchMe, logout }
})
