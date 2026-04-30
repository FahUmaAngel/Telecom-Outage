"use client";

import { useState, useEffect } from "react";
import { useTheme } from "../../context/ThemeContext";
import { useLanguage } from "../../context/LanguageContext";

export default function Header() {
  const { theme, toggleTheme } = useTheme();
  const { lang, toggleLanguage } = useLanguage();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setTimeout(() => setMounted(true), 0);
  }, []);

  const darkLabel = lang === "sv" ? "MÖRKT" : "DARK";
  const lightLabel = lang === "sv" ? "LJUST" : "LIGHT";
  const themeToggleLabel = theme === "light" ? darkLabel : lightLabel;

  // Use a stable initial state for hydration, then update after mount
  let currentPlaceholder = "Search...";
  if (mounted) {
    currentPlaceholder = lang === "sv" ? "Sök..." : "Search...";
  }

  const currentThemeLabel = mounted ? themeToggleLabel : "...";
  
  let languageDisplay = "SV";
  if (mounted) {
    languageDisplay = lang === "sv" ? "SV" : "EN";
  }

  return (
    <header className="header glass animate-fade-in">
      <div className="logo font-heading">
        <span className="text-gradient">Telecom</span> Outage
      </div>

      <div className="search-container">
        <div className="search-icon-css"></div>
        <input
          type="text"
          placeholder={currentPlaceholder}
        />
      </div>

      <div className="actions">
        <button onClick={toggleLanguage} className="action-btn">
          {languageDisplay}
        </button>
        <button onClick={toggleTheme} className="action-btn theme-btn">
          {currentThemeLabel}
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

        @media (max-width: 768px) {
          .header { padding: 0 16px; }
          .search-container { display: none; }
        }
      `}</style>
    </header>
  );
}
