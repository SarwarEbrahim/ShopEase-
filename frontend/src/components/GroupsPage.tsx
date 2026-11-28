import { type FormEvent, useEffect, useState } from "react"
import { createGroup, listGroups } from "../api"
import type { Group } from "../types"

export default function GroupsPage() {
  const [groups, setGroups] = useState<Group[] | null>(null)
  const [error, setError] = useState("")
  const [name, setName] = useState("")
  const [reloadKey, setReloadKey] = useState(0)

  useEffect(() => {
    let cancelled = false
    listGroups()
      .then((result) => {
        if (!cancelled) setGroups(result)
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof Error ? err.message : "Something went wrong")
      })
    return () => {
      cancelled = true
    }
  }, [reloadKey])

  async function handleCreate(e: FormEvent) {
    e.preventDefault()
    setError("")
    try {
      await createGroup(name.trim())
      setName("")
      setReloadKey((k) => k + 1)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong")
    }
  }

  return (
    <section>
      <h2>My groups</h2>

      <form className="filters" onSubmit={handleCreate}>
        <input value={name} onChange={(e) => setName(e.target.value)} placeholder="New group name" maxLength={80} required />
        <button type="submit">Create group</button>
      </form>

      {error && <p className="error">{error}</p>}
      {groups === null && !error && <p>Loading...</p>}
      {groups && groups.length === 0 && <p>You are not in any group yet.</p>}

      {groups && groups.length > 0 && (
        <table>
          <thead>
            <tr>
              <th>Group</th>
              <th>Owner</th>
              <th>My permissions</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {groups.map((g) => (
              <tr key={g.id}>
                <td>{g.name}</td>
                <td>{g.owner_username ?? "-"}</td>
                <td>{g.is_owner ? "owner (everything)" : g.my_permissions.join(", ") || "view only"}</td>
                <td className="actions">
                  <a href={`#/groups/${g.id}`}>Open</a>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  )
}
