import { ProductCard } from "../components/ProductCard";
import { ShopControls } from "../components/ShopControls";

export function ShopPage({ loading, products, query, setQuery, filter, setFilter, onSelectProduct, onAddToCart }) {
  return (
    <>
      <Hero setFilter={setFilter} />
      <ShopControls query={query} setQuery={setQuery} filter={filter} setFilter={setFilter} />
      <section className="product-grid-section" id="shop">
        <div className="section-heading">
          <p>{loading ? "Loading atelier" : `${products.length} pieces`}</p>
          <h2>Ready-to-wear with occasion energy</h2>
        </div>
        <div className="product-grid">
          {products.map((product, index) => (
            <ProductCard
              key={product.id}
              product={product}
              index={index}
              onSelect={onSelectProduct}
              onAdd={onAddToCart}
            />
          ))}
        </div>
      </section>
      <EditorialBand />
    </>
  );
}

function Hero({ setFilter }) {
  return (
    <section className="hero">
      <img
        src="https://images.unsplash.com/photo-1496747611176-843222e1e57c?auto=format&fit=crop&w=1800&q=85"
        alt="Fashion editorial collection"
      />
      <div className="hero-copy">
        <p>Spring occasion edit</p>
        <h1>Clothes with posture, ease, and a little drama.</h1>
        <div className="hero-actions">
          <a href="#shop" onClick={() => setFilter("new")}>Shop new arrivals</a>
          <a href="#shop" onClick={() => setFilter("featured")}>Explore the edit</a>
        </div>
      </div>
    </section>
  );
}

function EditorialBand() {
  return (
    <section className="editorial-band">
      <div>
        <p>Made for movement</p>
        <h2>The shop edit balances soft structure, high contrast, and polished everyday wear.</h2>
      </div>
      <img src="https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?auto=format&fit=crop&w=1200&q=85" alt="Runway-inspired styling" />
    </section>
  );
}
