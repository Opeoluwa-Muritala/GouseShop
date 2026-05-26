import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import { AuthModal } from "./components/AuthModal";
import { CartDrawer } from "./components/CartDrawer";
import { Header } from "./components/Header";
import { MobileNav } from "./components/MobileNav";
import { Toast } from "./components/Toast";
import { fallbackProducts } from "./data/fallbackProducts";
import { api } from "./lib/api";
import { openPaystackSdk, paystackAccessCode, paystackCheckoutUrl } from "./lib/paystack";
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
  const [categories, setCategories] = useState([]);
  const [apiState, setApiState] = useState("connecting");
  const [pagination, setPagination] = useState({ limit: 24, offset: 0, total: 0 });
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(true);
  const [checkoutBusy, setCheckoutBusy] = useState(false);

  useEffect(() => {
    loadCategories();
    loadCart();
  }, []);

  useEffect(() => {
    loadProducts(0);
  }, [filter, query]);

  function productParams(nextOffset) {
    const params = new URLSearchParams({
      limit: String(pagination.limit),
      offset: String(nextOffset),
    });

    if (query.trim()) params.set("q", query.trim());
    if (filter === "new") params.set("new_arrival", "true");
    if (filter === "sale") params.set("sale", "true");
    if (filter === "women") params.set("gender", "women");
    if (filter === "men") params.set("gender", "men");
    if (filter === "children") params.set("gender", "kids");
    if (filter === "featured") params.set("featured", "true");
    if (filter.startsWith("category:")) params.set("category", filter.replace("category:", ""));

    return params.toString();
  }

  async function loadProducts(nextOffset = pagination.offset) {
    setLoading(true);
    try {
      const data = await api(`/products/?${productParams(nextOffset)}`);
      setProducts(data.items || []);
      setApiState(data.items?.length ? "live" : "empty");
      setPagination((current) => ({
        ...current,
        offset: data.offset ?? nextOffset,
        total: data.total ?? data.items?.length ?? 0,
      }));
    } catch {
      setProducts(fallbackProducts);
      setApiState("offline");
      setStatus("Backend is offline or blocked. Showing preview catalog.");
      setPagination((current) => ({ ...current, offset: 0, total: fallbackProducts.length }));
    } finally {
      setLoading(false);
    }
  }

  async function loadCategories() {
    try {
      setCategories(await api("/categories/"));
    } catch {
      setCategories([]);
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

  function selectFilter(nextFilter) {
    setSelectedProduct(null);
    setFilter(nextFilter);
    setPagination((current) => ({ ...current, offset: 0 }));
    requestAnimationFrame(() => document.getElementById("shop")?.scrollIntoView({ behavior: "smooth", block: "start" }));
  }

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
    if (checkoutBusy) return;
    setCheckoutBusy(true);
    try {
      const order = await api("/orders/", { method: "POST", body: "{}" });
      await loadCart();
      const payment = await api("/payments/initiate", {
        method: "POST",
        body: JSON.stringify({ order_id: order.id, provider, country: "NG", currency: order.currency || "NGN" }),
      });
      if (provider === "paystack") {
        try {
          await openPaystackSdk(paystackAccessCode(payment));
          setDrawerOpen(false);
          return;
        } catch {
          const checkoutUrl = paystackCheckoutUrl(payment);
          if (checkoutUrl) {
            window.location.href = checkoutUrl;
            return;
          }
          throw new Error("Paystack checkout could not be opened.");
        }
      }
      if (payment.provider_checkout_url) window.location.href = payment.provider_checkout_url;
    } catch (error) {
      setStatus(error.message);
    } finally {
      setCheckoutBusy(false);
    }
  }

  const cartCount = cart?.items?.reduce((sum, item) => sum + item.quantity, 0) || 0;
  const cartTotal = cart?.items?.reduce((sum, item) => sum + item.price_snapshot * item.quantity, 0) || 0;

  return (
    <>
      <Header
        cartCount={cartCount}
        filter={filter}
        setAuthOpen={setAuthOpen}
        setDrawerOpen={setDrawerOpen}
        setFilter={selectFilter}
        setMobileNavOpen={setMobileNavOpen}
        goHome={() => setSelectedProduct(null)}
      />
      <main>
        {!selectedProduct ? (
          <ShopPage
            loading={loading}
            products={products}
            query={query}
            setQuery={setQuery}
            filter={filter}
            setFilter={selectFilter}
            categories={categories}
            pagination={pagination}
            onPageChange={loadProducts}
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
        checkoutBusy={checkoutBusy}
        openAuth={() => setAuthOpen(true)}
      />
      <AuthModal open={authOpen} setOpen={setAuthOpen} setStatus={setStatus} reloadCart={loadCart} />
      <MobileNav open={mobileNavOpen} setOpen={setMobileNavOpen} setFilter={selectFilter} categories={categories} />
      {status && <Toast message={status} onClose={() => setStatus("")} />}
    </>
  );
}

createRoot(document.getElementById("root")).render(<App />);
