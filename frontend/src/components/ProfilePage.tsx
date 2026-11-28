import { type FormEvent, useState } from "react"
import { changePassword, updateProfile } from "../api"
import { useAuth } from "../AuthContext"

export default function ProfilePage() {
  const { user, updateUser } = useAuth()
  const [fullName, setFullName] = useState(user?.full_name ?? "")
  const [email, setEmail] = useState(user?.email ?? "")
  const [profileMsg, setProfileMsg] = useState("")
  const [profileError, setProfileError] = useState("")

  const [current, setCurrent] = useState("")
  const [next, setNext] = useState("")
  const [pwMsg, setPwMsg] = useState("")
  const [pwError, setPwError] = useState("")

  async function saveProfile(e: FormEvent) {
    e.preventDefault()
    setProfileMsg("")
    setProfileError("")
    try {
      updateUser(await updateProfile({ full_name: fullName.trim(), email: email.trim() }))
      setProfileMsg("Profile saved.")
    } catch (err) {
      setProfileError(err instanceof Error ? err.message : "Something went wrong")
    }
  }

  async function savePassword(e: FormEvent) {
    e.preventDefault()
    setPwMsg("")
    setPwError("")
    try {
      await changePassword(current, next)
      setCurrent("")
      setNext("")
      setPwMsg("Password changed.")
    } catch (err) {
      setPwError(err instanceof Error ? err.message : "Something went wrong")
    }
  }

  if (!user) return null

  return (
    <section>
      <h2>My profile</h2>
      <p>
        Username: <strong>{user.username}</strong> (role: {user.role})
      </p>

      <h3>Update profile</h3>
      <form className="auth-form" onSubmit={saveProfile}>
        <label>
          Full name
          <input value={fullName} onChange={(e) => setFullName(e.target.value)} required />
        </label>
        <label>
          Email
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        </label>
        {profileError && <p className="error">{profileError}</p>}
        {profileMsg && <p className="success">{profileMsg}</p>}
        <button type="submit">Save profile</button>
      </form>

      <h3>Change password</h3>
      <form className="auth-form" onSubmit={savePassword}>
        <label>
          Current password
          <input type="password" value={current} onChange={(e) => setCurrent(e.target.value)} autoComplete="current-password" required />
        </label>
        <label>
          New password
          <input type="password" value={next} onChange={(e) => setNext(e.target.value)} autoComplete="new-password" required />
        </label>
        <small>At least 8 characters, with a letter and a digit.</small>
        {pwError && <p className="error">{pwError}</p>}
        {pwMsg && <p className="success">{pwMsg}</p>}
        <button type="submit">Change password</button>
      </form>
    </section>
  )
}
