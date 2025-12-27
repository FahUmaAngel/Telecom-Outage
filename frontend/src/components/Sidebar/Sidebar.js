"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useLanguage } from "../../context/LanguageContext";

export default function Sidebar() {
  const pathname = usePathname();
  const { lang } = useLanguage();

  const menuItems = [
    { label_sv: "Översikt", label_en: "Dashboard", path: "/" },
    { label_sv: "Live-karta", label_en: "Live Map", path: "/map" },
    { label_sv: "Rapportera", label_en: "Report Outage", path: "/report" },
    { label_sv: "Rapporter", label_en: "Reports", path: "/reports" },
    { label_sv: "Regioner", label_en: "Regions", path: "/regions" },
    { label_sv: "Analys", label_en: "Analytics", path: "/analytics" },
    { label_sv: "Admin", label_en: "Admin", path: "/admin" },
  ];

  return (
    <aside className="sidebar animate-fade-in">
      <nav className="nav-menu">
        {menuItems.map((item) => (
          <Link
            key={item.path}
            href={item.path}
            className={`nav-item ${pathname === item.path ? "active" : ""}`}
          >
            <span className="dot-marker"></span>
            <span className="label">{lang === "sv" ? item.label_sv : item.label_en}</span>
          </Link>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div className="status-indicator">
          <div className="system-dot"></div>
          <span className="status-text">{lang === "sv" ? "System Aktivt" : "System Live"}</span>
        </div>
      </div>

      <style jsx>{`
        .sidebar {
          position: fixed;
          top: var(--header-height);
          left: 0;
          bottom: 0;
          width: var(--sidebar-width);
          padding: 24px 12px;
          display: flex;
          flex-direction: column;
          justify-content: space-between;
          border-right: 1px solid var(--border-color);
          background: var(--surface-color);
          z-index: 900;
        }
        .nav-menu {
          display: flex;
          flex-direction: column;
          gap: 4px;
        }
        .nav-item {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 10px 16px;
          border-radius: var(--radius-sm);
          color: var(--text-secondary);
          transition: var(--transition-base);
          font-weight: 500;
          font-size: 0.9rem;
        }
        .nav-item:hover {
          background: var(--surface-hover);
          color: var(--text-primary);
        }
        .nav-item.active {
          background: var(--surface-hover);
          color: var(--accent-primary);
          font-weight: 700;
        }
        .dot-marker {
          width: 4px;
          height: 4px;
          background: var(--text-muted);
          border-radius: 50%;
          opacity: 0.5;
        }
        .nav-item.active .dot-marker {
          background: var(--accent-primary);
          opacity: 1;
          width: 5px;
          height: 5px;
        }
        .status-indicator {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 0.75rem;
          color: var(--text-muted);
          padding: 12px 16px;
          border-top: 1px solid var(--border-color);
          text-transform: uppercase;
          font-weight: 700;
          letter-spacing: 0.05em;
        }
        .system-dot {
          width: 6px;
          height: 6px;
          background: var(--status-success);
          border-radius: 50%;
        }

        @media (max-width: 768px) {
          .sidebar { display: none; }
        }
      `}</style>
    </aside>
  );
}
