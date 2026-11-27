import { type FormEvent, useState } from "react"
import { useAuth } from "../AuthContext"

type Props = { mode: "login" | "signup" }

export default function AuthPage({ mode }: Props) {
  const { login, signup, notice } = useAuth()
  const [username, setUsername] = useState("")
  const [email, setEmail] = useState("")
  const [fullName, setFullName] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState("")
  const [busy, setBusy] = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError("")
    try {
      if (mode === "login") {
        await login(username.trim(), password)
      } else {
        await signup({ username: username.trim(), email: email.trim(), full_name: fullName.trim(), password })
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong")
    } finally {
      setBusy(false)
    }
  }

  return (
    <section>
      <h2>{mode === "login" ? "Log in" : "Create an account"}</h2>
      {notice && <p className="notice">{notice}</p>}

      <form className="auth-form" onSubmit={handleSubmit}>
        <label>
          Username
          <input value={username} onChange={(e) => setUsername(e.target.value)} autoComplete="username" required />
        </label>

        {mode === "signup" && (
          <>
            <label>
              Email
              <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
            </label>
            <label>
              Full name
              <input value={fullName} onChange={(e) => setFullName(e.target.value)} required />
            </label>
          </>
        )}

        <label>
          Password
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete={mode === "login" ? "current-password" : "new-password"}
            required
          />
        </label>
        {mode === "signup" && <small>At least 8 characters, with a letter and a digit.</small>}

        {error && <p className="error">{error}</p>}

        <button type="submit" disabled={busy}>
          {busy ? "Please wait..." : mode === "login" ? "Log in" : "Sign up"}
        </button>
      </form>

      <p>
        {mode === "login" ? (
          <>
            No account yet? <a href="#/signup">Sign up</a>
          </>
        ) : (
          <>
            Already have an account? <a href="#/login">Log in</a>
          </>
        )}
      </p>
    </section>
  )
}
