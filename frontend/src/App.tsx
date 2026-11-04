import { useState } from "react"
import ProductDetail from "./components/ProductDetail"
import ProductForm from "./components/ProductForm"
import ProductList from "./components/ProductList"

// Which screen is showing. The form has an `id` only when editing.
type View =
  | { name: "list" }
  | { name: "detail"; id: number }
  | { name: "form"; id?: number }

export default function App() {
  const [view, setView] = useState<View>({ name: "list" })
  const showList = () => setView({ name: "list" })

  return (
    <main>
      <h1>ShopEase</h1>

      {view.name === "list" && (
        <ProductList
          onView={(id) => setView({ name: "detail", id })}
          onAdd={() => setView({ name: "form" })}
          onEdit={(id) => setView({ name: "form", id })}
        />
      )}

      {view.name === "detail" && (
        <ProductDetail
          id={view.id}
          onBack={showList}
          onEdit={(id) => setView({ name: "form", id })}
        />
      )}

      {view.name === "form" && (
        <ProductForm id={view.id} onDone={showList} onCancel={showList} />
      )}
    </main>
  )
}
