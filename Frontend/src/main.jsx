import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import { AuthModal } from "./components/AuthModal";
import { CartDrawer } from "./components/CartDrawer";
import { Header } from "./components/Header";
import { MobileNav } from "./components/MobileNav";
import { Toast } from "./components/Toast";
import { fallbackProducts } from "./data/fallbackProducts";
import { api } from "./lib/api";
import { openPaystackSdk, paystackAccessCode, paystackCheckoutUrl, preloadPaystackSdk } from "./lib/paystack";
import { ProductDetailPage } from "./pages/ProductDetailPage";
import { ShopPage } from "./pages/ShopPage";
import { AdminPage } from "./pages/AdminPage";
import { AdminLoginPage } from "./pages/AdminLoginPage";
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
  const [currentUser, setCurrentUser] = useState(null);
  const [adminOpen, setAdminOpen] = useState(false);
  const [path, setPath] = useState(window.location.pathname);

  useEffect(() => {
    loadCategories();
    loadCart();
    loadCurrentUser();
    preloadPaystackSdk();
  }, []);

  useEffect(() => {
    const onPopState = () => setPath(window.location.pathname);
    window.addEventListener("popstate", onPopState);
    return () => window.removeEventListener("popstate", onPopState);
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

  async function loadCurrentUser() {
    try {
      setCurrentUser(await api("/auth/me"));
    } catch {
      setCurrentUser(null);
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
      setStatus("Preparing Paystack checkout...");
      const order = await api("/orders/", { method: "POST", body: "{}" });
      await loadCart();
      const payment = await api("/payments/initiate", {
        method: "POST",
        body: JSON.stringify({ order_id: order.id, provider }),
      });
      if (provider === "paystack") {
        const accessCode = paystackAccessCode(payment);
        const checkoutUrl = paystackCheckoutUrl(payment);
        try {
          await openPaystackSdk(accessCode);
          setDrawerOpen(false);
          setStatus("Paystack checkout opened.");
          return;
        } catch (sdkError) {
          if (checkoutUrl) {
            setStatus("Opening Paystack checkout page...");
            window.location.href = checkoutUrl;
            return;
          }
          throw new Error(sdkError.message || "Paystack checkout could not be opened.");
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
  const isAdminPath = path === "/admin";
  const isAdminLoginPath = path === "/admin/login";

  function navigateTo(nextPath) {
    window.history.pushState({}, "", nextPath);
    setPath(nextPath);
    setAdminOpen(nextPath === "/admin");
  }

  if (isAdminLoginPath) {
    return (
      <>
        <AdminLoginPage
          onSuccess={() => {
            loadCurrentUser();
            setAdminOpen(true);
            navigateTo("/admin");
          }}
          onNavigateHome={() => navigateTo("/")}
        />
      </>
    );
  }

  if (isAdminPath || adminOpen) {
    return (
      <>
        <Header
          cartCount={cartCount}
          filter={filter}
          setAuthOpen={setAuthOpen}
          setDrawerOpen={setDrawerOpen}
          setFilter={selectFilter}
          setMobileNavOpen={setMobileNavOpen}
          goHome={() => {
            setSelectedProduct(null);
            setAdminOpen(false);
            navigateTo("/");
          }}
          focusSearch={() => document.querySelector(".search-box input")?.focus()}
          isAdmin={currentUser?.role === "admin"}
          openAdmin={() => {
            setAdminOpen(true);
            navigateTo(currentUser?.role === "admin" ? "/admin" : "/admin/login");
          }}
        />
        <main>
          <AdminPage
            onClose={() => {
              setAdminOpen(false);
              navigateTo("/");
            }}
            currentUser={currentUser}
          />
        </main>
      </>
    );
  }

  return (
    <>
      <Header
        cartCount={cartCount}
        filter={filter}
        setAuthOpen={setAuthOpen}
        setDrawerOpen={setDrawerOpen}
        setFilter={selectFilter}
        setMobileNavOpen={setMobileNavOpen}
        goHome={() => {
          setSelectedProduct(null);
          setAdminOpen(false);
        }}
        focusSearch={() => document.querySelector(".search-box input")?.focus()}
        isAdmin={currentUser?.role === "admin"}
        openAdmin={() => setAdminOpen(true)}
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
      <AuthModal open={authOpen} setOpen={setAuthOpen} setStatus={setStatus} reloadCart={loadCart} onSuccess={loadCurrentUser} />
      <MobileNav
        open={mobileNavOpen}
        setOpen={setMobileNavOpen}
        setFilter={selectFilter}
        categories={categories}
        query={query}
        setQuery={setQuery}
      />
      {status && <Toast message={status} onClose={() => setStatus("")} />}
    </>
  );
}

createRoot(document.getElementById("root")).render(<App />);
