import { useAppContext } from '../context/AppContext';

export default function useAuth() {
  const { authToken, setAuthToken, userData, setUserData } = useAppContext();
  return { authToken, setAuthToken, userData, setUserData };
}
