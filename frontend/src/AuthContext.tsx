import { createContext, type ReactNode, useCallback, useContext, useEffect, useState } from "react"
import * as api from "./api"
import { AUTH_EXPIRED_EVENT, clearToken, getToken, setToken } from "./auth"
import type { SignupInput, User } from "./types"

type AuthState = {
  user: User | null
  loading: boolean // true while we check a saved token after a page reload
  notice: string // for example "Your session has expired"
  login: (username: string, password: string) => Promise<void>
  signup: (input: SignupInput) => Promise<void>
  logout: () => void
  updateUser: (user: User) => void
}

const AuthContext = createContext<AuthState | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  // Start in the loading state when a token is saved, so the page never flashes
  // the guest (login) screen while the session is being restored.
  const [loading, setLoading] = useState(() => getToken() !== null)
  const [notice, setNotice] = useState("")

  // Restore the session after a reload: ask the server who the token belongs to.
  useEffect(() => {
    if (getToken() === null) return
    api
      .getMe()
      .then(setUser)
      .catch(() => clearToken())
      .finally(() => setLoading(false))
  }, [])

  // The API layer fires this when the server answers 401 to a request with a token.
  useEffect(() => {
    const onExpired = () => {
      setUser(null)
      setNotice("Your session has expired. Please log in again.")
    }
    window.addEventListener(AUTH_EXPIRED_EVENT, onExpired)
    return () => window.removeEventListener(AUTH_EXPIRED_EVENT, onExpired)
  }, [])

  const login = useCallback(async (username: string, password: string) => {
    const result = await api.login(username, password)
    setToken(result.access_token)
    setUser(result.user)
    setNotice("")
  }, [])

  const signup = useCallback(
    async (input: SignupInput) => {
      await api.signup(input)
      await login(input.username, input.password)
    },
    [login],
  )

  const logout = useCallback(() => {
    // Tell the server (it records the logout), then forget the token either way.
    api.logoutRequest().catch(() => undefined)
    clearToken()
    setUser(null)
    setNotice("")
  }, [])

  return (
    <AuthContext.Provider value={{ user, loading, notice, login, signup, logout, updateUser: setUser }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthState {
  const value = useContext(AuthContext)
  if (value === null) throw new Error("useAuth must be used inside AuthProvider")
  return value
}
