// frontend/src/components/DropdownMenu.tsx
import { useEffect, useRef, useState } from 'react';

interface DropdownMenuProps {
  label: string;
  icon: string;
  children: React.ReactNode;
}

export function DropdownMenu({ label, icon, children }: DropdownMenuProps) {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div className="nav-dropdown" ref={dropdownRef}>
      <button
        className={`nav-dropdown-trigger ${isOpen ? 'active' : ''}`}
        onClick={() => setIsOpen(!isOpen)}
      >
        {icon} {label} <span className="dropdown-arrow">▼</span>
      </button>
      {isOpen && (
        <div className="nav-dropdown-menu">
          {children}
        </div>
      )}
    </div>
  );
}

export default DropdownMenu;
