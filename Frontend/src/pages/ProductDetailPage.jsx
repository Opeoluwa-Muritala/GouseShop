import { ArrowLeft, Check, ShoppingBag } from "lucide-react";
import { useState } from "react";
import { getImage, money } from "../lib/format";

export function ProductDetailPage({ product, onBack, onAddToCart }) {
  const [variantId, setVariantId] = useState(product.variants?.[0]?.id);

  return (
    <section className="detail-page">
      <button className="back-button" onClick={onBack}>
        <ArrowLeft size={18} />
        Back to shop
      </button>
      <div className="detail-layout">
        <div className="detail-media">
          <img src={getImage(product)} alt={product.name} />
        </div>
        <div className="detail-info">
          <p className="eyebrow">{product.is_bestseller ? "Bestseller" : "GouseShop atelier"}</p>
          <h1>{product.name}</h1>
          <p className="detail-price">{money(product.price)}</p>
          <p className="detail-description">{product.description || "An easy statement piece designed for repeat wears."}</p>
          <div className="variant-list">
            {product.variants?.map((variant) => (
              <button key={variant.id} className={variantId === variant.id ? "selected" : ""} onClick={() => setVariantId(variant.id)}>
                <span style={{ background: variant.color_hex || "#111" }} />
                {variant.size || "One size"} / {variant.color || "Default"}
              </button>
            ))}
          </div>
          <button className="primary-action" onClick={() => onAddToCart(product, variantId)}>
            <ShoppingBag size={18} />
            Add to bag
          </button>
          <div className="promise-grid">
            {["Secure checkout", "Cloudinary-backed imagery", "Paystack-ready payments"].map((item) => (
              <div key={item}>
                <Check size={16} />
                {item}
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
