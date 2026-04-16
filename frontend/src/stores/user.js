import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useUserStore = defineStore('user', () => {
  const user = ref(JSON.parse(sessionStorage.getItem('user') || 'null'))
  const token = ref(sessionStorage.getItem('access_token') || '')

  const isLoggedIn = computed(() => !!token.value)
  const role = computed(() => user.value?.role || '')

  function setAuth(userData, accessToken, refreshToken) {
    user.value = userData
    token.value = accessToken
    sessionStorage.setItem('user', JSON.stringify(userData))
    sessionStorage.setItem('access_token', accessToken)
    sessionStorage.setItem('refresh_token', refreshToken)
  }

  function logout() {
    user.value = null
    token.value = ''
    sessionStorage.removeItem('user')
    sessionStorage.removeItem('access_token')
    sessionStorage.removeItem('refresh_token')
  }

  return { user, token, isLoggedIn, role, setAuth, logout }
})
