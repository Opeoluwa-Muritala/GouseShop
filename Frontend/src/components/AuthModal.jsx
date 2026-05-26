import { Loader2, User, X } from "lucide-react";
import { useState } from "react";
import { api } from "../lib/api";

export function AuthModal({ open, setOpen, setStatus, reloadCart }) {
  const [mode, setMode] = useState("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  if (!open) return null;

  async function submit(event) {
    event.preventDefault();
    setBusy(true);
    try {
      const path = mode === "login" ? "/auth/login" : "/auth/register";
      const data = await api(path, { method: "POST", body: JSON.stringify({ email, password }) });
      if (data.access_token) {
        localStorage.setItem("gouseshop_token", data.access_token);
        setStatus(mode === "register" ? "Account created. Your bag is saved." : "Signed in. Your bag is saved.");
        setOpen(false);
        reloadCart();
      } else {
        setStatus("Account created. Sign in to continue.");
        setMode("login");
      }
    } catch (error) {
      setStatus(error.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="modal-shell">
      <form className="auth-modal" onSubmit={submit}>
        <div className="drawer-header">
          <h2>{mode === "login" ? "Sign in" : "Create account"}</h2>
          <button type="button" className="icon-button" onClick={() => setOpen(false)}><X size={19} /></button>
        </div>
        <label>Email<input value={email} onChange={(event) => setEmail(event.target.value)} type="email" required /></label>
        <label>Password<input value={password} onChange={(event) => setPassword(event.target.value)} type="password" required /></label>
        <button className="primary-action" type="submit" disabled={busy}>
          {busy ? <Loader2 className="spin" size={18} /> : <User size={18} />}
          {mode === "login" ? "Sign in" : "Create account"}
        </button>
        <button type="button" className="text-link" onClick={() => setMode(mode === "login" ? "register" : "login")}>
          {mode === "login" ? "Need an account?" : "Already have an account?"}
        </button>
      </form>
    </div>
  );
}
