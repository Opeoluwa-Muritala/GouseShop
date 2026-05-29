import { ProductCard } from "../components/ProductCard";
import { SafeImage } from "../components/SafeImage";
import { ShopControls } from "../components/ShopControls";

export function ShopPage({
  loading,
  products,
  query,
  setQuery,
  filter,
  setFilter,
  categories,
  pagination,
  onPageChange,
  onSelectProduct,
  onAddToCart,
}) {
  return (
    <>
      <Hero setFilter={setFilter} />
      <ShopControls query={query} setQuery={setQuery} filter={filter} setFilter={setFilter} />
      <section className="product-grid-section" id="shop">
        <div className="section-heading">
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
        <Pagination pagination={pagination} loading={loading} onPageChange={onPageChange} />
      </section>
      <EditorialBand />
    </>
  );
}

function Pagination({ pagination, loading, onPageChange }) {
  const { limit, offset, total } = pagination;
  const currentPage = Math.floor(offset / limit) + 1;
  const totalPages = Math.max(1, Math.ceil(total / limit));
  const canGoBack = offset > 0 && !loading;
  const canGoNext = offset + limit < total && !loading;

  return (
    <nav className="pagination" aria-label="Product pagination">
      <button disabled={!canGoBack} onClick={() => onPageChange(Math.max(0, offset - limit))}>
        Previous
      </button>
      <span>
        Page {currentPage} of {totalPages}
      </span>
      <button disabled={!canGoNext} onClick={() => onPageChange(offset + limit)}>
        Next
      </button>
    </nav>
  );
}

function CategoryRail({ categories }) {
  if (!categories?.length) return null;
  return (
    <section className="category-rail">
      {categories.map((category) => (
        <a key={category.id} href="#shop">
          {category.name}
        </a>
      ))}
    </section>
  );
}

function Hero({ setFilter }) {
  return (
    <section className="hero">
      <SafeImage
        src="https://images.pexels.com/photos/994523/pexels-photo-994523.jpeg?auto=compress&cs=tinysrgb&w=1800"
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
      <SafeImage src="https://images.pexels.com/photos/1536619/pexels-photo-1536619.jpeg?auto=compress&cs=tinysrgb&w=1200" alt="Runway-inspired styling" />
    </section>
  );
}
