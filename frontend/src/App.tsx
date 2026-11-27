import { useEffect, useState } from "react"
import { AuthProvider, useAuth } from "./AuthContext"
import AdminUsers from "./components/AdminUsers"
import AuthPage from "./components/AuthPage"
import ProductDetail from "./components/ProductDetail"
import ProductForm from "./components/ProductForm"
import ProductList from "./components/ProductList"

// Which product screen is showing. The form has an `id` only when editing.
type ProductView =
  | { name: "list" }
  | { name: "detail"; id: number }
  | { name: "form"; id?: number }

function Products() {
  const [view, setView] = useState<ProductView>({ name: "list" })
  const showList = () => setView({ name: "list" })

  return (
    <>
      {view.name === "list" && (
        <ProductList
          onView={(id) => setView({ name: "detail", id })}
          onAdd={() => setView({ name: "form" })}
          onEdit={(id) => setView({ name: "form", id })}
        />
      )}
      {view.name === "detail" && (
        <ProductDetail id={view.id} onBack={showList} onEdit={(id) => setView({ name: "form", id })} />
      )}
      {view.name === "form" && <ProductForm id={view.id} onDone={showList} onCancel={showList} />}
    </>
  )
}

// The page is kept in the URL hash (#/products, #/admin, ...), so reloads and
// deep links keep working without any server-side routing.
function readPage(): string {
  return window.location.hash.replace(/^#\/?/, "")
}

function usePage(): string {
  const [page, setPage] = useState(readPage)
  useEffect(() => {
    const onChange = () => setPage(readPage())
    window.addEventListener("hashchange", onChange)
    return () => window.removeEventListener("hashchange", onChange)
  }, [])
  return page
}

function Shell() {
  const { user, loading, logout } = useAuth()
  const page = usePage()

  // Wait for the saved session to be checked, so a logged-in user never sees the login page flash.
  if (loading) {
    return (
      <main>
        <p>Loading...</p>
      </main>
    )
  }

  // Route guards. The server enforces the same rules; this only keeps the UI honest.
  let current = page
  if (!user && current !== "login" && current !== "signup") current = "login"
  if (user && (current === "login" || current === "signup" || current === "")) current = "products"

  return (
    <main>
      <nav className="nav">
        <h1>ShopEase</h1>
        <div className="nav-links">
          {user ? (
            <>
              <a href="#/products">Products</a>
              {user.role === "admin" && <a href="#/admin">Admin</a>}
              <span className="who">
                {user.username} <span className={`badge ${user.role}`}>{user.role}</span>
              </span>
              <button type="button" onClick={logout}>
                Log out
              </button>
            </>
          ) : (
            <>
              <a href="#/login">Log in</a>
              <a href="#/signup">Sign up</a>
            </>
          )}
        </div>
      </nav>

      {current === "login" && <AuthPage mode="login" />}
      {current === "signup" && <AuthPage mode="signup" />}
      {current === "products" && <Products />}
      {current === "admin" &&
        (user?.role === "admin" ? (
          <AdminUsers />
        ) : (
          <p className="error">403: you do not have access to this page.</p>
        ))}
      {!["login", "signup", "products", "admin"].includes(current) && <p>Page not found.</p>}
    </main>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <Shell />
    </AuthProvider>
  )
}
