"use client";

import { Search, Filter, X, ChevronDown } from "lucide-react";
import { useState } from "react";
import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

function cn(...inputs) {
    return twMerge(clsx(inputs));
}

export default function FilterBar({
    operators = [],
    onFilterChange,
    initialFilters = {
        search: "",
        operators: [],
        severities: [],
        status: "active"
    }
}) {
    const [filters, setFilters] = useState(initialFilters);
    const [isExpanded, setIsExpanded] = useState(false);

    const severities = ["Critical", "Medium", "Minor"];
    const statuses = [
        { id: "all", label: "All" },
        { id: "active", label: "Active" },
        { id: "resolved", label: "Resolved" }
    ];

    const updateFilter = (key, value) => {
        const newFilters = { ...filters, [key]: value };
        setFilters(newFilters);
        onFilterChange?.(newFilters);
    };

    const toggleMultiSelect = (key, val) => {
        const current = filters[key];
        const next = current.includes(val)
            ? current.filter(i => i !== val)
            : [...current, val];
        updateFilter(key, next);
    };

    const clearFilters = () => {
        const reset = {
            search: "",
            operators: [],
            severities: [],
            status: "active"
        };
        setFilters(reset);
        onFilterChange?.(reset);
    };

    const activeCount =
        filters.operators.length +
        filters.severities.length +
        (filters.search ? 1 : 0) +
        (filters.status !== "all" ? 1 : 0);

    return (
        <div className="filter-bar-wrapper">
            <div className={cn("filter-bar-container glass", isExpanded && "expanded")}>
                <div className="search-section">
                    <Search className="search-icon" size={18} />
                    <input
                        type="text"
                        placeholder="Search area or incident..."
                        value={filters.search}
                        onChange={(e) => updateFilter("search", e.target.value)}
                        className="search-input"
                    />
                </div>

                <div className="divider" />

                <div className="controls-section">
                    <button
                        className={cn("filter-toggle-btn", activeCount > 0 && "has-active")}
                        onClick={() => setIsExpanded(!isExpanded)}
                    >
                        <Filter size={16} />
                        <span>Filters </span>
                        {activeCount > 0 && <span className="badge">{activeCount}</span>}
                        <ChevronDown size={14} className={cn("chevron", isExpanded && "up")} />
                    </button>

                    {activeCount > 0 && (
                        <button className="clear-btn" onClick={clearFilters}>
                            <X size={14} />
                        </button>
                    )}
                </div>
            </div>

            {isExpanded && (
                <div className="filter-dropdown glass animate-slide-down">
                    <div className="filter-grid">
                        <div className="filter-group">
                            <label>Status</label>
                            <div className="chip-group">
                                {statuses.map(s => (
                                    <button
                                        key={s.id}
                                        className={cn("chip", filters.status === s.id && "selected")}
                                        onClick={() => updateFilter("status", s.id)}
                                    >
                                        {s.label}
                                    </button>
                                ))}
                            </div>
                        </div>

                        <div className="filter-group">
                            <label>Operators</label>
                            <div className="chip-group">
                                {operators.map(op => (
                                    <button
                                        key={op.id}
                                        className={cn("chip", filters.operators.includes(op.name) && "selected")}
                                        onClick={() => toggleMultiSelect("operators", op.name)}
                                    >
                                        {op.name}
                                    </button>
                                ))}
                            </div>
                        </div>

                        <div className="filter-group">
                            <label>Severity</label>
                            <div className="chip-group">
                                {severities.map(s => (
                                    <button
                                        key={s}
                                        className={cn("chip", filters.severities.includes(s) && "selected")}
                                        onClick={() => toggleMultiSelect("severities", s)}
                                    >
                                        {s}
                                    </button>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>
            )}

            <style jsx>{`
                .filter-bar-wrapper {
                    position: sticky;
                    top: 80px;
                    z-index: 100;
                    margin-bottom: 24px;
                }
                .filter-bar-container {
                    display: flex;
                    align-items: center;
                    padding: 8px 16px;
                    border-radius: 40px;
                    border: 1px solid var(--border-color);
                    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                }
                .filter-bar-container.expanded {
                    border-bottom-left-radius: 0;
                    border-bottom-right-radius: 0;
                }
                .search-section {
                    flex: 1;
                    display: flex;
                    align-items: center;
                    gap: 12px;
                    padding-left: 8px;
                }
                .search-icon { color: var(--text-muted); }
                .search-input {
                    background: transparent;
                    border: none;
                    outline: none;
                    color: var(--text-primary);
                    font-size: 0.95rem;
                    width: 100%;
                }
                .divider {
                    width: 1px;
                    height: 24px;
                    background: var(--border-color);
                    margin: 0 16px;
                }
                .controls-section {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                }
                .filter-toggle-btn {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    padding: 8px 16px;
                    border-radius: 20px;
                    background: transparent;
                    border: 1px solid transparent;
                    color: var(--text-primary);
                    font-weight: 700;
                    font-size: 0.85rem;
                    cursor: pointer;
                    transition: var(--transition-base);
                }
                .filter-toggle-btn:hover { background: var(--surface-hover); }
                .filter-toggle-btn.has-active { border-color: var(--accent-primary); color: var(--accent-primary); }
                
                .badge {
                    background: var(--accent-primary);
                    color: white;
                    font-size: 0.65rem;
                    width: 16px;
                    height: 16px;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }
                .chevron { transition: transform 0.3s; }
                .chevron.up { transform: rotate(180deg); }
                
                .clear-btn {
                    padding: 8px;
                    border-radius: 50%;
                    background: var(--surface-hover);
                    border: none;
                    color: var(--text-muted);
                    cursor: pointer;
                }
                .clear-btn:hover { color: var(--status-critical); }

                .filter-dropdown {
                    padding: 24px;
                    border: 1px solid var(--border-color);
                    border-top: none;
                    border-bottom-left-radius: var(--radius-lg);
                    border-bottom-right-radius: var(--radius-lg);
                    margin-top: -1px;
                }
                .filter-grid {
                    display: grid;
                    grid-template-columns: repeat(3, 1fr);
                    gap: 32px;
                }
                .filter-group label {
                    display: block;
                    font-size: 0.7rem;
                    text-transform: uppercase;
                    font-weight: 800;
                    color: var(--text-muted);
                    margin-bottom: 12px;
                    letter-spacing: 0.05em;
                }
                .chip-group { display: flex; gap: 8px; flex-wrap: wrap; }
                .chip {
                    padding: 6px 14px;
                    border-radius: 20px;
                    font-size: 0.8rem;
                    font-weight: 700;
                    background: var(--surface-color);
                    border: 1px solid var(--border-color);
                    color: var(--text-secondary);
                    cursor: pointer;
                    transition: var(--transition-base);
                }
                .chip:hover { border-color: var(--text-muted); }
                .chip.selected {
                    background: var(--accent-primary);
                    border-color: var(--accent-primary);
                    color: white;
                }

                @media (max-width: 900px) {
                    .filter-grid { grid-template-columns: 1fr; gap: 24px; }
                }
            `}</style>
        </div>
    );
}
