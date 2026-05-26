import { Search, SlidersHorizontal } from "lucide-react";

export function ShopControls({ query, setQuery, filter, setFilter }) {
  const filters = [
    ["all", "All"],
    ["new", "New"],
    ["featured", "Featured"],
    ["women", "Women"],
    ["men", "Men"],
    ["children", "Children"],
    ["sale", "Sale"],
  ];

  return (
    <section className="shop-controls">
      <label className="search-box">
        <Search size={17} />
        <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search dresses, sets, linen" />
      </label>
      <div className="filter-tabs" aria-label="Product filters">
        <SlidersHorizontal size={16} />
        {filters.map(([value, label]) => (
          <button key={value} className={filter === value ? "active" : ""} onClick={() => setFilter(value)}>
            {label}
          </button>
        ))}
      </div>
    </section>
  );
}
