import { useShield } from '../context/ShieldContext'

export default function useAuth() {
  const { authToken, setAuthToken, userData, setUserData } = useShield()
  return { authToken, setAuthToken, userData, setUserData }
}
