import { Minus, Plus, ShoppingBag, X } from "lucide-react";
import { fallbackProducts } from "../data/fallbackProducts";
import { getImage, money } from "../lib/format";

export function CartDrawer({ open, setOpen, cart, productByVariant, cartTotal, updateCartItem, createOrderAndPay, openAuth }) {
  return (
    <aside className={`drawer ${open ? "open" : ""}`} aria-hidden={!open}>
      <div className="drawer-panel">
        <div className="drawer-header">
          <h2>Shopping bag</h2>
          <button className="icon-button" onClick={() => setOpen(false)} aria-label="Close bag">
            <X size={19} />
          </button>
        </div>
        <div className="drawer-items">
          {!cart?.items?.length ? (
            <p className="empty">Your bag is ready for something excellent.</p>
          ) : (
            cart.items.map((item) => {
              const product = productByVariant.get(item.variant_id);
              return (
                <div className="cart-row" key={item.id}>
                  <img src={product ? getImage(product) : fallbackProducts[0].images[0].secure_url} alt={product?.name || "Cart item"} />
                  <div>
                    <h3>{product?.name || `Variant #${item.variant_id}`}</h3>
                    <p>{money(item.price_snapshot)} each</p>
                    <div className="qty">
                      <button onClick={() => updateCartItem(item, Math.max(0, item.quantity - 1))}><Minus size={14} /></button>
                      <span>{item.quantity}</span>
                      <button onClick={() => updateCartItem(item, item.quantity + 1)}><Plus size={14} /></button>
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>
        <div className="drawer-footer">
          <div className="subtotal">
            <span>Subtotal</span>
            <strong>{money(cartTotal)}</strong>
          </div>
          <button className="primary-action" onClick={() => createOrderAndPay("paystack")}>
            <ShoppingBag size={18} />
            Checkout with Paystack
          </button>
          <button className="secondary-action" onClick={openAuth}>Sign in before checkout</button>
        </div>
      </div>
      <button className="drawer-scrim" onClick={() => setOpen(false)} aria-label="Close overlay" />
    </aside>
  );
}
