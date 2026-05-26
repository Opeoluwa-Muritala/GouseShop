import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import { AuthModal } from "./components/AuthModal";
import { CartDrawer } from "./components/CartDrawer";
import { Header } from "./components/Header";
import { MobileNav } from "./components/MobileNav";
import { Toast } from "./components/Toast";
import { fallbackProducts } from "./data/fallbackProducts";
import { api } from "./lib/api";
import { ProductDetailPage } from "./pages/ProductDetailPage";
import { ShopPage } from "./pages/ShopPage";
import "./styles/styles.css";

function App() {
  const [products, setProducts] = useState([]);
  const [cart, setCart] = useState(null);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [authOpen, setAuthOpen] = useState(false);
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState("all");
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadProducts();
    loadCart();
  }, []);

  async function loadProducts() {
    setLoading(true);
    try {
      const data = await api("/products/?limit=50");
      setProducts(data.items?.length ? data.items : fallbackProducts);
    } catch {
      setProducts(fallbackProducts);
    } finally {
      setLoading(false);
    }
  }

  async function loadCart() {
    try {
      setCart(await api("/cart/"));
    } catch {
      setCart({ items: [], currency: "NGN" });
    }
  }

  const productByVariant = useMemo(() => {
    const map = new Map();
    products.forEach((product) => product.variants?.forEach((variant) => map.set(variant.id, product)));
    return map;
  }, [products]);

  const visibleProducts = products.filter((product) => {
    const matchesQuery = `${product.name} ${product.description || ""}`.toLowerCase().includes(query.toLowerCase());
    const matchesFilter =
      filter === "all" ||
      (filter === "new" && product.is_new_arrival) ||
      (filter === "featured" && product.is_featured) ||
      (filter === "sale" && product.is_sale) ||
      (filter === "men" && product.gender === "men") ||
      (filter === "women" && product.gender === "women");
    return matchesQuery && matchesFilter;
  });

  async function addToCart(product, variantId) {
    const variant = product.variants?.find((item) => item.id === variantId) || product.variants?.[0];
    if (!variant) {
      setStatus("This piece needs a variant before it can be added.");
      return;
    }
    try {
      const nextCart = await api("/cart/items", {
        method: "POST",
        body: JSON.stringify({ variant_id: variant.id, quantity: 1 }),
      });
      setCart(nextCart);
      setDrawerOpen(true);
      setStatus(`${product.name} added to bag.`);
    } catch (error) {
      setStatus(error.message);
    }
  }

  async function updateCartItem(item, quantity) {
    try {
      if (quantity === 0) {
        await api(`/cart/items/${item.id}`, { method: "DELETE" });
        await loadCart();
        return;
      }
      setCart(await api(`/cart/items/${item.id}`, { method: "PATCH", body: JSON.stringify({ quantity }) }));
    } catch (error) {
      setStatus(error.message);
    }
  }

  async function createOrderAndPay(provider) {
    try {
      const order = await api("/orders/", { method: "POST", body: "{}" });
      const payment = await api("/payments/initiate", {
        method: "POST",
        body: JSON.stringify({ order_id: order.id, provider, country: "NG", currency: order.currency || "NGN" }),
      });
      if (payment.provider_checkout_url) window.location.href = payment.provider_checkout_url;
    } catch (error) {
      setStatus(error.message);
    }
  }

  const cartCount = cart?.items?.reduce((sum, item) => sum + item.quantity, 0) || 0;
  const cartTotal = cart?.items?.reduce((sum, item) => sum + item.price_snapshot * item.quantity, 0) || 0;

  return (
    <>
      <Header
        cartCount={cartCount}
        setAuthOpen={setAuthOpen}
        setDrawerOpen={setDrawerOpen}
        setFilter={setFilter}
        setMobileNavOpen={setMobileNavOpen}
        goHome={() => setSelectedProduct(null)}
      />
      <main>
        {!selectedProduct ? (
          <ShopPage
            loading={loading}
            products={visibleProducts}
            query={query}
            setQuery={setQuery}
            filter={filter}
            setFilter={setFilter}
            onSelectProduct={setSelectedProduct}
            onAddToCart={addToCart}
          />
        ) : (
          <ProductDetailPage product={selectedProduct} onBack={() => setSelectedProduct(null)} onAddToCart={addToCart} />
        )}
      </main>
      <CartDrawer
        open={drawerOpen}
        setOpen={setDrawerOpen}
        cart={cart}
        productByVariant={productByVariant}
        cartTotal={cartTotal}
        updateCartItem={updateCartItem}
        createOrderAndPay={createOrderAndPay}
        openAuth={() => setAuthOpen(true)}
      />
      <AuthModal open={authOpen} setOpen={setAuthOpen} setStatus={setStatus} reloadCart={loadCart} />
      <MobileNav open={mobileNavOpen} setOpen={setMobileNavOpen} setFilter={setFilter} />
      {status && <Toast message={status} onClose={() => setStatus("")} />}
    </>
  );
}

createRoot(document.getElementById("root")).render(<App />);
