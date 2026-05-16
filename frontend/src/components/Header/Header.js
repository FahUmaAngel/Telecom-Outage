"use client";

import { useEffect, useState } from "react";
import { useTheme } from "../../context/ThemeContext";
import { useLanguage } from "../../context/LanguageContext";
import PropTypes from "prop-types";

export default function Header({ onMenuClick }) {
    Header.propTypes = { onMenuClick: PropTypes.func.isRequired };
  const { theme, toggleTheme } = useTheme();
  const { lang, toggleLanguage } = useLanguage();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const resolvedLang = mounted ? lang : "sv";
  const resolvedTheme = mounted ? theme : "dark";
  const darkLabel = resolvedLang === "sv" ? "MORKT" : "DARK";
  const lightLabel = resolvedLang === "sv" ? "LJUST" : "LIGHT";
  const themeToggleLabel = resolvedTheme === "light" ? darkLabel : lightLabel;

  return (
    <header className="header glass animate-fade-in">
      <div className="logo-row">
        <button className="hamburger" onClick={onMenuClick} aria-label="Toggle menu">
          <span /><span /><span />
        </button>
        <div className="logo font-heading">
          <span className="text-gradient">Telecom</span> Outage
        </div>
      </div>

      <div className="search-container">
        <div className="search-icon-css"></div>
        <input
          type="text"
          placeholder={resolvedLang === "sv" ? "Sok..." : "Search..."}
        />
      </div>

      <div className="actions">
        <button onClick={toggleLanguage} className="action-btn">
          {resolvedLang === "sv" ? "SV" : "EN"}
        </button>
        <button onClick={toggleTheme} className="action-btn theme-btn">
          {themeToggleLabel}
        </button>
      </div>

      <style jsx>{`
        .header {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          height: var(--header-height);
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 0 32px;
          z-index: 1000;
          border-bottom: 1px solid var(--border-color);
        }
        .logo {
          font-size: 1.4rem;
          font-weight: 700;
        }
        .search-container {
          position: relative;
          width: 320px;
        }
        .search-icon-css {
          position: absolute;
          left: 14px;
          top: 50%;
          transform: translateY(-50%);
          width: 14px;
          height: 14px;
          border: 1.5px solid var(--text-muted);
          border-radius: 50%;
        }
        .search-icon-css::after {
          content: '';
          position: absolute;
          right: -4px;
          bottom: -4px;
          width: 6px;
          height: 1.5px;
          background: var(--text-muted);
          transform: rotate(45deg);
        }
        .search-container input {
          background: var(--surface-color);
          border: 1px solid var(--border-color);
          padding: 8px 16px 8px 38px;
          border-radius: var(--radius-md);
          width: 100%;
          color: var(--text-primary);
          outline: none;
          transition: var(--transition-base);
          font-size: 0.9rem;
        }
        .search-container input:focus {
          border-color: var(--accent-primary);
        }
        .actions {
          display: flex;
          gap: 12px;
        }
        .action-btn {
          padding: 6px 12px;
          font-weight: 600;
          font-size: 0.75rem;
          color: var(--text-secondary);
          background: var(--surface-color);
          border: 1px solid var(--border-color);
          border-radius: var(--radius-sm);
          min-width: 44px;
          text-transform: uppercase;
          letter-spacing: 0.05em;
        }
        .action-btn:hover {
          border-color: var(--text-primary);
          color: var(--text-primary);
          background: var(--surface-hover);
        }
        .theme-btn {
          min-width: 70px;
        }

        .logo-row { display: flex; align-items: center; gap: 10px; }
        .hamburger {
          display: none;
          flex-direction: column;
          justify-content: center;
          gap: 5px;
          width: 36px;
          height: 36px;
          background: none;
          border: none;
          cursor: pointer;
          padding: 6px;
          border-radius: var(--radius-sm);
        }
        .hamburger:hover { background: var(--surface-hover); }
        .hamburger span {
          display: block;
          height: 2px;
          background: var(--text-primary);
          border-radius: 2px;
          width: 100%;
        }
        @media (max-width: 768px) {
          .header { padding: 0 16px; }
          .search-container { display: none; }
          .hamburger { display: flex; }
        }
      `}</style>
    </header>
  );
}
