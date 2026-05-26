import { Plus } from "lucide-react";
import { getImage, money } from "../lib/format";
import { SafeImage } from "./SafeImage";

export function ProductCard({ product, index, onSelect, onAdd }) {
  return (
    <article className={index % 5 === 0 ? "product-card wide" : "product-card"}>
      <button className="product-image" onClick={() => onSelect(product)}>
        <SafeImage src={getImage(product)} alt={product.images?.[0]?.alt || product.name} />
        <span>{product.is_sale ? "Sale" : product.is_new_arrival ? "New" : product.is_featured ? "Edit" : "Atelier"}</span>
      </button>
      <div className="product-meta">
        <button onClick={() => onSelect(product)}>{product.name}</button>
        <p>{money(product.price)}</p>
      </div>
      <div className="product-submeta">
        <span>{product.gender || "unisex"}</span>
        <button onClick={() => onAdd(product)}>
          <Plus size={15} />
          Add
        </button>
      </div>
    </article>
  );
}
