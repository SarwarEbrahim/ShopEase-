import { type FormEvent, useEffect, useState } from "react"
import {
  addMember,
  assignGroupProduct,
  createGroupProduct,
  deleteGroup,
  deleteGroupProduct,
  getGroup,
  listGroupProducts,
  removeMember,
  renameGroup,
  updateGroupProduct,
  updateMember,
  type Permissions,
} from "../api"
import type { GroupDetail, GroupProduct, Member, ProductInput } from "../types"

type Props = { groupId: number }

const EMPTY_PRODUCT = { name: "", category: "", price: "", stock: "0" }

function toInput(f: typeof EMPTY_PRODUCT): ProductInput {
  return { name: f.name.trim(), description: null, price: f.price, stock: Number(f.stock), category: f.category.trim() }
}

export default function GroupView({ groupId }: Props) {
  const [group, setGroup] = useState<GroupDetail | null>(null)
  const [products, setProducts] = useState<GroupProduct[]>([])
  const [error, setError] = useState("")
  const [reloadKey, setReloadKey] = useState(0)

  const [newName, setNewName] = useState("")
  const [memberName, setMemberName] = useState("")
  const [memberPerms, setMemberPerms] = useState<Permissions>({ can_create: false, can_edit: false, can_assign: false })

  const [form, setForm] = useState(EMPTY_PRODUCT)
  const [editingId, setEditingId] = useState<number | null>(null)

  useEffect(() => {
    let cancelled = false
    Promise.all([getGroup(groupId), listGroupProducts(groupId)])
      .then(([g, p]) => {
        if (cancelled) return
        setGroup(g)
        setProducts(p)
        setNewName(g.name)
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof Error ? err.message : "Something went wrong")
      })
    return () => {
      cancelled = true
    }
  }, [groupId, reloadKey])

  // Run an action, then reload. The server decides if it is allowed and sends a message if not.
  async function run(action: () => Promise<unknown>) {
    setError("")
    try {
      await action()
      setReloadKey((k) => k + 1)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong")
    }
  }

  if (!group) {
    return (
      <section>
        <p>
          <a href="#/groups">Back to groups</a>
        </p>
        {error ? <p className="error">{error}</p> : <p>Loading...</p>}
      </section>
    )
  }

  const can = (p: string) => group.my_permissions.includes(p)
  const people: { id: number; name: string }[] = [
    { id: group.owner_id, name: `${group.owner_username ?? "owner"} (owner)` },
    ...group.members.map((m) => ({ id: m.user_id, name: m.username })),
  ]

  function permsOf(m: Member): Permissions {
    return { can_create: m.can_create, can_edit: m.can_edit, can_assign: m.can_assign }
  }

  function startEdit(p: GroupProduct) {
    setEditingId(p.id)
    setForm({ name: p.name, category: p.category, price: String(p.price), stock: String(p.stock) })
  }

  async function submitProduct(e: FormEvent) {
    e.preventDefault()
    const input = toInput(form)
    const id = editingId
    setEditingId(null)
    setForm(EMPTY_PRODUCT)
    await run(() => (id === null ? createGroupProduct(groupId, input) : updateGroupProduct(groupId, id, input)))
  }

  return (
    <section>
      <p>
        <a href="#/groups">Back to groups</a>
      </p>
      <h2>{group.name}</h2>
      <p>
        Owner: <strong>{group.owner_username}</strong>. Your permissions:{" "}
        <strong>{group.is_owner ? "owner (everything)" : group.my_permissions.join(", ") || "view only"}</strong>
      </p>
      {error && <p className="error">{error}</p>}

      {group.is_owner && (
        <div className="filters">
          <input value={newName} onChange={(e) => setNewName(e.target.value)} maxLength={80} />
          <button type="button" disabled={!newName.trim()} onClick={() => run(() => renameGroup(groupId, newName.trim()))}>
            Rename
          </button>
          <button
            type="button"
            onClick={async () => {
              if (!window.confirm("Delete this group and its products?")) return
              setError("")
              try {
                await deleteGroup(groupId)
                window.location.hash = "#/groups"
              } catch (err) {
                setError(err instanceof Error ? err.message : "Something went wrong")
              }
            }}
          >
            Delete group
          </button>
        </div>
      )}

      <h3>Members</h3>
      {group.members.length === 0 && <p>No members yet.</p>}
      {group.members.length > 0 && (
        <table>
          <thead>
            <tr>
              <th>User</th>
              <th>Create</th>
              <th>Edit</th>
              <th>Assign</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {group.members.map((m) => (
              <tr key={m.user_id}>
                <td>{m.username}</td>
                {(["can_create", "can_edit", "can_assign"] as const).map((key) => (
                  <td key={key}>
                    <input
                      type="checkbox"
                      className="check"
                      checked={m[key]}
                      disabled={!group.is_owner}
                      onChange={(e) => run(() => updateMember(groupId, m.user_id, { ...permsOf(m), [key]: e.target.checked }))}
                    />
                  </td>
                ))}
                <td className="actions">
                  {group.is_owner && (
                    <button type="button" onClick={() => run(() => removeMember(groupId, m.user_id))}>
                      Remove
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {group.is_owner && (
        <form
          className="filters"
          onSubmit={(e) => {
            e.preventDefault()
            const username = memberName.trim()
            setMemberName("")
            run(() => addMember(groupId, username, memberPerms))
          }}
        >
          <input value={memberName} onChange={(e) => setMemberName(e.target.value)} placeholder="Username to add" required />
          {(["can_create", "can_edit", "can_assign"] as const).map((key) => (
            <label key={key}>
              <input
                type="checkbox"
                className="check"
                checked={memberPerms[key]}
                onChange={(e) => setMemberPerms({ ...memberPerms, [key]: e.target.checked })}
              />{" "}
              {key.replace("can_", "")}
            </label>
          ))}
          <button type="submit">Add member</button>
        </form>
      )}

      <h3>Group products</h3>
      {products.length === 0 && <p>No products in this group yet.</p>}
      {products.length > 0 && (
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Category</th>
              <th>Price</th>
              <th>Stock</th>
              <th>Assigned to</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {products.map((p) => (
              <tr key={p.id}>
                <td>{p.name}</td>
                <td>{p.category}</td>
                <td>{Number(p.price).toFixed(2)}</td>
                <td>{p.stock}</td>
                <td>
                  {can("assign") ? (
                    <select
                      value={p.assignee_id ?? ""}
                      onChange={(e) => run(() => assignGroupProduct(groupId, p.id, e.target.value ? Number(e.target.value) : null))}
                    >
                      <option value="">Nobody</option>
                      {people.map((person) => (
                        <option key={person.id} value={person.id}>
                          {person.name}
                        </option>
                      ))}
                    </select>
                  ) : (
                    (p.assignee_username ?? "-")
                  )}
                </td>
                <td className="actions">
                  {can("edit") && (
                    <button type="button" onClick={() => startEdit(p)}>
                      Edit
                    </button>
                  )}
                  {group.is_owner && (
                    <button
                      type="button"
                      onClick={() => {
                        if (window.confirm(`Delete "${p.name}"?`)) run(() => deleteGroupProduct(groupId, p.id))
                      }}
                    >
                      Delete
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {(can("create") || (editingId !== null && can("edit"))) && (
        <form className="filters" onSubmit={submitProduct}>
          <strong>{editingId === null ? "Add product:" : "Edit product:"}</strong>
          <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="Name" required />
          <input value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })} placeholder="Category" required />
          <input value={form.price} onChange={(e) => setForm({ ...form, price: e.target.value })} placeholder="Price" required />
          <input type="number" min="0" value={form.stock} onChange={(e) => setForm({ ...form, stock: e.target.value })} placeholder="Stock" required />
          <button type="submit">{editingId === null ? "Add" : "Save"}</button>
          {editingId !== null && (
            <button
              type="button"
              onClick={() => {
                setEditingId(null)
                setForm(EMPTY_PRODUCT)
              }}
            >
              Cancel
            </button>
          )}
        </form>
      )}
    </section>
  )
}
