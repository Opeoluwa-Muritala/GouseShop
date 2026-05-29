import { Menu, Search, ShoppingBag, User, ShieldCheck } from "lucide-react";

export function Header({ cartCount, filter, setAuthOpen, setDrawerOpen, setFilter, setMobileNavOpen, goHome, focusSearch, openAdmin }) {
  const links = [
    ["new", "New"],
    ["women", "Women"],
    ["men", "Men"],
    ["children", "Children"],
    ["sale", "Sale"],
  ];

  return (
    <header className="site-header">
      <div className="announce">New ceremonial pieces now available. Worldwide delivery from Lagos.</div>
      <nav className="nav">
        <button className="icon-button mobile-only" onClick={() => setMobileNavOpen(true)} aria-label="Open menu">
          <Menu size={20} />
        </button>
        <button className="brand" onClick={goHome}>GouseShop</button>
        <div className="nav-links">
          {links.map(([value, label]) => (
            <button key={value} className={filter === value ? "active" : ""} onClick={() => setFilter(value)}>{label}</button>
          ))}
          <button className="icon-button" onClick={focusSearch} aria-label="Search">
            <Search size={18} />
          </button>
          <button className="icon-button" onClick={openAdmin} aria-label="Admin login">
            <ShieldCheck size={18} />
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
