import { Search, X } from "lucide-react";

export function MobileNav({ open, setOpen, setFilter, categories = [], query, setQuery }) {
  if (!open) return null;

  function choose(value) {
    setFilter(value);
    setOpen(false);
  }

  return (
    <aside className="side-menu" aria-label="Shop menu">
      <div className="side-menu-panel">
        <div className="side-menu-header">
          <span>GouseShop</span>
          <button className="icon-button" onClick={() => setOpen(false)} aria-label="Close menu"><X size={19} /></button>
        </div>
        <label className="side-menu-search">
          <Search size={17} />
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search dresses, sets, linen"
          />
        </label>
        {categories.length > 0 && (
          <div className="side-menu-categories">
            <p>Categories</p>
            {categories.map((category) => (
              <button key={category.id} onClick={() => choose(`category:${category.slug}`)}>
                {category.name}
              </button>
            ))}
          </div>
        )}
      </div>
      <button className="side-menu-scrim" onClick={() => setOpen(false)} aria-label="Close menu" />
    </aside>
  );
}
