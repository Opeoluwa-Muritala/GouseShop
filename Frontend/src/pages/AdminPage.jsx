import { useEffect, useState } from "react";
import { api } from "../lib/api";
import { money } from "../lib/format";

const ORDER_STATUSES = [
  "pending_payment",
  "paid",
  "processing",
  "shipped",
  "delivered",
  "cancelled",
  "refunded",
];

export function AdminPage({ onClose, currentUser }) {
  const [orders, setOrders] = useState([]);
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [fabrics, setFabrics] = useState([]);
  const [statusMessage, setStatusMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const [productForm, setProductForm] = useState({
    name: "",
    slug: "",
    description: "",
    price: "",
    category_id: "",
    fabric_id: "",
    gender: "",
    status: "active",
    is_featured: false,
    is_bestseller: false,
    is_sale: false,
    is_new_arrival: false,
    is_coming_soon: false,
    is_preorder: false,
  });

  useEffect(() => {
    loadAdminData();
  }, []);

  async function loadAdminData() {
    setBusy(true);
    try {
      await Promise.all([loadOrders(), loadProducts(), loadCategories(), loadFabrics()]);
    } catch (error) {
      setStatusMessage(error.message);
    } finally {
      setBusy(false);
    }
  }

  async function loadOrders() {
    const list = await api("/orders/admin/list");
    setOrders(list);
  }

  async function loadProducts() {
    const response = await api("/products/?limit=100&offset=0");
    setProducts(response.items || []);
  }

  async function loadCategories() {
    setCategories(await api("/categories/"));
  }

  async function loadFabrics() {
    setFabrics(await api("/fabrics/"));
  }

  function setField(name, value) {
    setProductForm((current) => ({ ...current, [name]: value }));
  }

  async function handleCreateProduct(event) {
    event.preventDefault();
    if (!productForm.name || !productForm.slug || !productForm.price) {
      setStatusMessage("Name, slug, and price are required.");
      return;
    }
    const payload = {
      ...productForm,
      price: Number(productForm.price),
      category_id: productForm.category_id ? Number(productForm.category_id) : undefined,
      fabric_id: productForm.fabric_id ? Number(productForm.fabric_id) : undefined,
    };
    setBusy(true);
    try {
      await api("/products/admin", { method: "POST", body: JSON.stringify(payload) });
      setStatusMessage("Product created successfully.");
      setProductForm({
        name: "",
        slug: "",
        description: "",
        price: "",
        category_id: "",
        fabric_id: "",
        gender: "",
        status: "active",
        is_featured: false,
        is_bestseller: false,
        is_sale: false,
        is_new_arrival: false,
        is_coming_soon: false,
        is_preorder: false,
      });
      await loadProducts();
    } catch (error) {
      setStatusMessage(error.message);
    } finally {
      setBusy(false);
    }
  }

  async function handleDeleteProduct(slug) {
    if (!window.confirm(`Delete product ${slug}?`)) return;
    try {
      await api(`/products/admin/${slug}`, { method: "DELETE" });
      setStatusMessage(`Deleted ${slug}.`);
      await loadProducts();
    } catch (error) {
      setStatusMessage(error.message);
    }
  }

  async function handleUpdateOrderStatus(orderId, status) {
    setBusy(true);
    try {
      const updated = await api(`/orders/admin/${orderId}/status`, {
        method: "PATCH",
        body: JSON.stringify({ status }),
      });
      setOrders((current) => current.map((order) => (order.id === updated.id ? updated : order)));
      setStatusMessage(`Order ${orderId} set to ${status}.`);
    } catch (error) {
      setStatusMessage(error.message);
    } finally {
      setBusy(false);
    }
  }

  if (!currentUser?.role || currentUser.role !== "admin") {
    return (
      <section className="admin-page">
        <div className="admin-panel">
          <div className="admin-header">
            <h2>Admin access required</h2>
            <button className="secondary-action" onClick={onClose}>Return to shop</button>
          </div>
          <p>Only admin users can view this page.</p>
        </div>
      </section>
    );
  }

  return (
    <section className="admin-page">
      <div className="admin-panel">
        <div className="admin-header">
          <div>
            <p className="eyebrow">Admin dashboard</p>
            <h2>Welcome back, {currentUser.email}</h2>
          </div>
          <button className="secondary-action" onClick={onClose}>Return to shop</button>
        </div>

        <div className="admin-grid">
          <div className="admin-card">
            <h3>Create new product</h3>
            <form className="admin-form" onSubmit={handleCreateProduct}>
              <label>
                Name
                <input value={productForm.name} onChange={(event) => setField("name", event.target.value)} required />
              </label>
              <label>
                Slug
                <input value={productForm.slug} onChange={(event) => setField("slug", event.target.value)} required />
              </label>
              <label>
                Price
                <input value={productForm.price} onChange={(event) => setField("price", event.target.value)} type="number" min="0" required />
              </label>
              <label>
                Description
                <textarea value={productForm.description} onChange={(event) => setField("description", event.target.value)} />
              </label>
              <label>
                Category
                <select value={productForm.category_id} onChange={(event) => setField("category_id", event.target.value)}>
                  <option value="">Unassigned</option>
                  {categories.map((category) => (
                    <option key={category.id} value={category.id}>{category.name}</option>
                  ))}
                </select>
              </label>
              <label>
                Fabric
                <select value={productForm.fabric_id} onChange={(event) => setField("fabric_id", event.target.value)}>
                  <option value="">Unassigned</option>
                  {fabrics.map((fabric) => (
                    <option key={fabric.id} value={fabric.id}>{fabric.name}</option>
                  ))}
                </select>
              </label>
              <label>
                Gender
                <select value={productForm.gender} onChange={(event) => setField("gender", event.target.value)}>
                  <option value="">Any</option>
                  <option value="women">Women</option>
                  <option value="men">Men</option>
                  <option value="kids">Kids</option>
                  <option value="unisex">Unisex</option>
                </select>
              </label>
              <label>
                Status
                <select value={productForm.status} onChange={(event) => setField("status", event.target.value)}>
                  <option value="active">Active</option>
                  <option value="draft">Draft</option>
                  <option value="archived">Archived</option>
                  <option value="coming_soon">Coming soon</option>
                  <option value="pre_order">Pre-order</option>
                </select>
              </label>
              <div className="admin-checkbox-row">
                <label>
                  <input type="checkbox" checked={productForm.is_featured} onChange={(event) => setField("is_featured", event.target.checked)} />
                  Featured
                </label>
                <label>
                  <input type="checkbox" checked={productForm.is_bestseller} onChange={(event) => setField("is_bestseller", event.target.checked)} />
                  Bestseller
                </label>
              </div>
              <div className="admin-checkbox-row">
                <label>
                  <input type="checkbox" checked={productForm.is_sale} onChange={(event) => setField("is_sale", event.target.checked)} />
                  Sale
                </label>
                <label>
                  <input type="checkbox" checked={productForm.is_new_arrival} onChange={(event) => setField("is_new_arrival", event.target.checked)} />
                  New arrival
                </label>
              </div>
              <div className="admin-checkbox-row">
                <label>
                  <input type="checkbox" checked={productForm.is_coming_soon} onChange={(event) => setField("is_coming_soon", event.target.checked)} />
                  Coming soon
                </label>
                <label>
                  <input type="checkbox" checked={productForm.is_preorder} onChange={(event) => setField("is_preorder", event.target.checked)} />
                  Pre-order
                </label>
              </div>
              <button className="primary-action" type="submit" disabled={busy}>{busy ? "Saving…" : "Create product"}</button>
            </form>
          </div>

          <div className="admin-card">
            <h3>Orders</h3>
            <div className="admin-table-wrapper">
              <table className="admin-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Status</th>
                    <th>Total</th>
                    <th>Items</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {orders.map((order) => (
                    <tr key={order.id}>
                      <td>{order.id}</td>
                      <td>{order.status}</td>
                      <td>{money(order.total)}</td>
                      <td>{order.items.length}</td>
                      <td>
                        <select defaultValue={order.status} onChange={(event) => handleUpdateOrderStatus(order.id, event.target.value)}>
                          {ORDER_STATUSES.map((status) => (
                            <option key={status} value={status}>{status}</option>
                          ))}
                        </select>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="admin-card">
            <h3>Products</h3>
            <div className="admin-table-wrapper admin-product-list">
              {products.length ? (
                <table className="admin-table">
                  <thead>
                    <tr>
                      <th>Slug</th>
                      <th>Name</th>
                      <th>Price</th>
                      <th>Status</th>
                      <th>Delete</th>
                    </tr>
                  </thead>
                  <tbody>
                    {products.map((product) => (
                      <tr key={product.id}>
                        <td>{product.slug}</td>
                        <td>{product.name}</td>
                        <td>{money(product.price)}</td>
                        <td>{product.status}</td>
                        <td>
                          <button className="secondary-action" type="button" onClick={() => handleDeleteProduct(product.slug)}>
                            Delete
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <p>No products available yet.</p>
              )}
            </div>
          </div>
        </div>

        {statusMessage ? <p className="status-message">{statusMessage}</p> : null}
      </div>
    </section>
  );
}
