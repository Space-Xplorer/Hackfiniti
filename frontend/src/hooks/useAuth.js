import { useAppContext } from '../context/AppContext'
import { apiClient } from '../api/client'

export function useAuth() {
  const { user, token, login, logout, isAuthenticated } = useAppContext()

  async function signIn(email, password) {
    const data = await apiClient.login(email, password)
    if (!data.access_token) throw new Error(data.detail ?? 'Login failed')
    login(null, data.access_token)
    return data
  }

  async function signUp(email, password, fullName) {
    const user = await apiClient.register({ email, password, full_name: fullName })
    return user
  }

  return { user, token, isAuthenticated, signIn, signUp, logout }
}
