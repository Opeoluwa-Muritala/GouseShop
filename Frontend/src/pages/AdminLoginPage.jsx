import { useState } from "react";
import { api } from "../lib/api";

export function AdminLoginPage({ onSuccess, onNavigateHome }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");

  async function handleSubmit(event) {
    event.preventDefault();
    setBusy(true);
    setMessage("");
    try {
      const data = await api("/admin/login", { method: "POST", body: JSON.stringify({ email, password }) });
      if (data.access_token) {
        onSuccess();
      }
    } catch (error) {
      setMessage(error.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="auth-page">
      <div className="auth-card">
        <div className="drawer-header">
          <h2>Admin login</h2>
          <button className="text-link" type="button" onClick={onNavigateHome}>
            Back to shop
          </button>
        </div>
        <form className="admin-form" onSubmit={handleSubmit}>
          <label>
            Email
            <input type="email" value={email} onChange={(event) => setEmail(event.target.value)} required />
          </label>
          <label>
            Password
            <input type="password" value={password} onChange={(event) => setPassword(event.target.value)} required />
          </label>
          <button className="primary-action" type="submit" disabled={busy}>
            {busy ? "Signing in…" : "Sign in"}
          </button>
        </form>
        {message ? <p className="status-message">{message}</p> : null}
      </div>
    </section>
  );
}
