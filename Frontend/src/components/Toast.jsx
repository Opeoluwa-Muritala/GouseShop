import { useEffect } from "react";

export function Toast({ message, onClose }) {
  useEffect(() => {
    const timer = setTimeout(onClose, 3600);
    return () => clearTimeout(timer);
  }, [onClose]);

  return <div className="toast">{message}</div>;
}
