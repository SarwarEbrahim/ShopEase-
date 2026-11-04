import { useState } from "react"
import ProductDetail from "./components/ProductDetail"
import ProductList from "./components/ProductList"

// Which screen is showing.
type View = { name: "list" } | { name: "detail"; id: number }

export default function App() {
  const [view, setView] = useState<View>({ name: "list" })

  return (
    <main>
      <h1>ShopEase</h1>

      {view.name === "list" && <ProductList onView={(id) => setView({ name: "detail", id })} />}

      {view.name === "detail" && (
        <ProductDetail id={view.id} onBack={() => setView({ name: "list" })} />
      )}
    </main>
  )
}
