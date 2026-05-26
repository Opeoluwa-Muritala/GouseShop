import { Menu, Search, ShoppingBag, User } from "lucide-react";

export function Header({ cartCount, setAuthOpen, setDrawerOpen, setFilter, setMobileNavOpen, goHome }) {
  return (
    <header className="site-header">
      <div className="announce">New ceremonial pieces now available. Worldwide delivery from Lagos.</div>
      <nav className="nav">
        <button className="icon-button mobile-only" onClick={() => setMobileNavOpen(true)} aria-label="Open menu">
          <Menu size={20} />
        </button>
        <button className="brand" onClick={goHome}>GouseShop</button>
        <div className="nav-links">
          {["new", "women", "men", "sale"].map((item) => (
            <button key={item} onClick={() => setFilter(item)}>{item}</button>
          ))}
        </div>
        <div className="nav-actions">
          <button className="icon-button" aria-label="Search">
            <Search size={18} />
          </button>
          <button className="icon-button" onClick={() => setAuthOpen(true)} aria-label="Account">
            <User size={18} />
          </button>
          <button className="bag-button" onClick={() => setDrawerOpen(true)}>
            <ShoppingBag size={18} />
            <span>{cartCount}</span>
          </button>
        </div>
      </nav>
    </header>
  );
}
