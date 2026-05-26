import { X } from "lucide-react";

export function MobileNav({ open, setOpen, setFilter }) {
  if (!open) return null;
  return (
    <div className="mobile-nav">
      <button className="icon-button" onClick={() => setOpen(false)}><X size={19} /></button>
      {["all", "new", "women", "men", "sale"].map((item) => (
        <button key={item} onClick={() => { setFilter(item); setOpen(false); }}>{item}</button>
      ))}
    </div>
  );
}
