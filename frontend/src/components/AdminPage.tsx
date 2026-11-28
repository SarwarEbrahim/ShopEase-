import { useEffect, useState } from "react"
import { getSecurity, getStats } from "../api"
import type { SecurityOverview, Stats } from "../types"
import AdminAudit from "./AdminAudit"
import AdminGroups from "./AdminGroups"
import AdminProducts from "./AdminProducts"
import AdminUsers from "./AdminUsers"

type Tab = "overview" | "users" | "products" | "groups" | "activity"

const TABS: { id: Tab; label: string }[] = [
  { id: "overview", label: "Overview" },
  { id: "users", label: "Users" },
  { id: "products", label: "Products" },
  { id: "groups", label: "Groups" },
  { id: "activity", label: "Activity log" },
]

function Overview() {
  const [stats, setStats] = useState<Stats | null>(null)
  const [security, setSecurity] = useState<SecurityOverview | null>(null)
  const [error, setError] = useState("")

  useEffect(() => {
    Promise.all([getStats(), getSecurity()])
      .then(([s, sec]) => {
        setStats(s)
        setSecurity(sec)
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Something went wrong"))
  }, [])

  if (error) return <p className="error">{error}</p>
  if (!stats || !security) return <p>Loading...</p>

  const cards: [string, number][] = [
    ["Users", stats.total_users],
    ["Banned users", stats.banned_users],
    ["Admins", stats.admins],
    ["Products", stats.total_products],
    ["Groups", stats.total_groups],
    ["New users (7 days)", stats.new_users_7d],
    ["New products (7 days)", stats.new_products_7d],
    ["Failed logins (24 h)", stats.failed_logins_24h],
  ]

  return (
    <section>
      <div className="cards">
        {cards.map(([label, value]) => (
          <div className="card" key={label}>
            <div className="card-value">{value}</div>
            <div className="card-label">{label}</div>
          </div>
        ))}
      </div>

      <h3>Security: failed logins in the last 24 hours</h3>
      <div className="two-col">
        <div>
          <h4>By IP address</h4>
          {security.by_ip.length === 0 ? (
            <p>None.</p>
          ) : (
            <table>
              <tbody>
                {security.by_ip.map((r) => (
                  <tr key={r.key}>
                    <td>{r.key}</td>
                    <td>{r.count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
        <div>
          <h4>By account</h4>
          {security.by_account.length === 0 ? (
            <p>None.</p>
          ) : (
            <table>
              <tbody>
                {security.by_account.map((r) => (
                  <tr key={r.key}>
                    <td>{r.key}</td>
                    <td>{r.count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </section>
  )
}

export default function AdminPage() {
  const [tab, setTab] = useState<Tab>("overview")

  return (
    <section>
      <h2>Admin dashboard</h2>
      <div className="tabs">
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            className={t.id === tab ? "tab active-tab" : "tab"}
            onClick={() => setTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === "overview" && <Overview />}
      {tab === "users" && <AdminUsers />}
      {tab === "products" && <AdminProducts />}
      {tab === "groups" && <AdminGroups />}
      {tab === "activity" && <AdminAudit />}
    </section>
  )
}
