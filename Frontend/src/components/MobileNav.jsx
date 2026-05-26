import { ArrowRight, X } from "lucide-react";

export function MobileNav({ open, setOpen, setFilter, categories = [] }) {
  const links = [
    ["all", "All"],
    ["new", "New"],
    ["women", "Women"],
    ["men", "Men"],
    ["children", "Children"],
    ["sale", "Sale"],
  ];

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
        <nav className="side-menu-nav" aria-label="Featured shop links">
          {links.map(([value, label]) => (
            <button key={value} onClick={() => choose(value)}>
              {label}
              <ArrowRight size={17} />
            </button>
          ))}
        </nav>
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
