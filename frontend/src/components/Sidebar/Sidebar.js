"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useLanguage } from "../../context/LanguageContext";
import PropTypes from "prop-types";

export default function Sidebar({ isOpen, onClose }) {
  Sidebar.propTypes = {
    isOpen: PropTypes.bool.isRequired,
    onClose: PropTypes.func.isRequired,
  };
  const pathname = usePathname();
  const { lang } = useLanguage();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const resolvedLang = mounted ? lang : "sv";

  const sections = [
    {
      key: "overview",
      label_sv: "Överblick",
      label_en: "Overview",
      items: [
        { label_sv: "Översikt", label_en: "Dashboard", path: "/" },
        { label_sv: "Live-karta", label_en: "Live Map", path: "/map" },
        { label_sv: "Regioner", label_en: "Regions", path: "/regions" },
      ],
    },
    {
      key: "tools",
      label_sv: "Verktyg",
      label_en: "Tools",
      items: [
        { label_sv: "Analys", label_en: "Analytics", path: "/analytics" },
        { label_sv: "Prestanda", label_en: "Performance", path: "/prestanda" },
        { label_sv: "Rapporter", label_en: "Reports", path: "/reports" },
        { label_sv: "Rapportera fel", label_en: "Report Outage", path: "/report" },
      ],
    },
    {
      key: "research",
      label_sv: "Forskning",
      label_en: "Research",
      items: [
        { label_sv: "Statistik", label_en: "Statistics", path: "/statistics" },
        { label_sv: "SLA-efterlevnad", label_en: "SLA Compliance", path: "/sla-compliance" },
        { label_sv: "Värdepoäng", label_en: "Value Score", path: "/value-score" },
        { label_sv: "Metodik", label_en: "Methodology", path: "/methodology" },
      ],
    },
    {
      key: "system",
      label_sv: "System",
      label_en: "System",
      items: [
        { label_sv: "Admin", label_en: "Admin", path: "/admin" },
      ],
    },
  ];

  return (
    <aside className={`sidebar animate-fade-in${isOpen ? " sidebar--open" : ""}`}>
      <nav className="nav-menu">
        {sections.map((section, sIdx) => (
          <div key={section.key} className={`nav-section${sIdx === 0 ? " first-section" : ""}`}>
            <div className="section-label">
              {resolvedLang === "sv" ? section.label_sv : section.label_en}
            </div>
            {section.items.map((item) => (
              <Link
                key={item.path}
                href={item.path}
                onClick={onClose}
                className={`nav-item ${section.key === "research" ? "research-item" : ""} ${pathname === item.path ? "active" : ""}`}
              >
                <span className="label">{resolvedLang === "sv" ? item.label_sv : item.label_en}</span>
              </Link>
            ))}
          </div>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div className="status-indicator">
          <div className="system-dot"></div>
          <span className="status-text">{resolvedLang === "sv" ? "System Aktivt" : "System Live"}</span>
        </div>
      </div>

      <style jsx>{`
        .sidebar {
          position: fixed;
          top: var(--header-height);
          left: 0;
          bottom: 0;
          width: var(--sidebar-width);
          padding: 16px 10px;
          display: flex;
          flex-direction: column;
          justify-content: space-between;
          border-right: 1px solid var(--border-color);
          background: var(--surface-color);
          z-index: 900;
          overflow-y: auto;
        }
        .nav-menu {
          display: flex;
          flex-direction: column;
        }
        .nav-section {
          display: flex;
          flex-direction: column;
          margin-top: 24px;
        }
        .nav-section.first-section {
          margin-top: 0;
        }
        .section-label {
          padding: 0 10px 6px 10px;
          margin-bottom: 2px;
          font-size: 0.6rem;
          font-weight: 800;
          letter-spacing: 0.14em;
          text-transform: uppercase;
          color: var(--text-muted);
          opacity: 0.5;
          border-bottom: 1px solid var(--border-color);
        }
        .nav-item {
          display: flex;
          align-items: center;
          padding: 8px 10px;
          border-radius: 6px;
          color: var(--text-secondary);
          transition: background 0.15s, color 0.15s;
          font-weight: 500;
          font-size: 0.875rem;
          text-decoration: none;
          position: relative;
        }
        .nav-item:hover {
          background: var(--surface-hover);
          color: var(--text-primary);
        }
        .nav-item.active {
          background: rgba(99, 102, 241, 0.08);
          color: var(--accent-primary);
          font-weight: 600;
        }
        .nav-item.active::before {
          content: "";
          position: absolute;
          left: 0;
          top: 25%;
          bottom: 25%;
          width: 3px;
          border-radius: 0 3px 3px 0;
          background: var(--accent-primary);
        }
        .label {
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }
        .research-item.active {
          background: rgba(163, 31, 208, 0.08);
          color: #A31FD0;
        }
        .research-item.active::before {
          background: #A31FD0;
        }
        .status-indicator {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 0.7rem;
          color: var(--text-muted);
          padding: 10px 10px;
          border-top: 1px solid var(--border-color);
          text-transform: uppercase;
          font-weight: 700;
          letter-spacing: 0.06em;
          margin-top: 8px;
        }
        .system-dot {
          width: 6px;
          height: 6px;
          background: var(--status-success);
          border-radius: 50%;
          flex-shrink: 0;
          box-shadow: 0 0 4px var(--status-success);
        }

        @media (max-width: 768px) {
          .sidebar {
            transform: translateX(-100%);
            transition: transform 0.25s ease;
            z-index: 900;
          }
          .sidebar--open {
            transform: translateX(0);
          }
        }
      `}</style>
    </aside>
  );
}
