"use client";

import { useEffect, useState, useMemo, useRef, useCallback } from "react";
import dynamic from "next/dynamic";
import PropTypes from "prop-types";
import Link from "next/link";
import { Info } from "lucide-react";
import { api } from "../lib/api";
import { useLanguage } from "../context/LanguageContext";
import { useToast } from "../context/ToastContext";
import FilterBar from "../components/Common/FilterBar";

// Dynamically import TacticalMap to avoid SSR errors with Leaflet
const TacticalMap = dynamic(() => import("../components/Map/Map"), {
  ssr: false,
  loading: () => <div className="map-placeholder glass">Loading Map...</div>,
});

const HistoricalTrend = dynamic(() => import("../components/Analytics/HistoricalTrend"), {
  ssr: false,
});

const OperatorComparison = dynamic(() => import("../components/Analytics/OperatorComparison"), {
  ssr: false,
});

const getOutageText = (value, lang) => {
  if (!value) return "";
  if (typeof value === "string") return value;
  return value[lang] || value.sv || value.en || "";
};

const StatsDashboard = ({ stats, lang }) => (
  <div className="stats-grid">
    {stats.map((stat) => (
      <Link href={stat.link || "#"} key={stat.key} className="premium-card stat-card interactive">
        <div className="stat-content">
          <span className="stat-label">{lang === "sv" ? stat.label_sv : stat.label_en}</span>
          <h2 className="stat-value">{stat.value}</h2>
          <span className="stat-meta">{lang === "sv" ? stat.trend_sv : stat.trend_en}</span>
        </div>
      </Link>
    ))}
    <style jsx>{`
      .stats-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 20px;
        margin-bottom: 32px;
      }
      .stat-card {
        padding: 24px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        text-decoration: none;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
      }
      .stat-card.interactive:hover {
        transform: translateY(-4px);
        box-shadow: var(--shadow-lg);
        border-color: var(--accent-primary);
      }
      .stat-label {
        font-size: 0.75rem;
        font-weight: 700;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 8px;
      }
      .stat-value {
        font-size: 1.75rem;
        font-weight: 700;
        margin-bottom: 4px;
        color: var(--text-primary);
      }
      .stat-meta {
        font-size: 0.75rem;
        color: var(--text-muted);
      }
      @media (max-width: 1400px) {
        .stats-grid { grid-template-columns: repeat(2, 1fr); }
      }
      @media (max-width: 768px) {
        .stats-grid { grid-template-columns: 1fr; }
      }
    `}</style>
  </div>
);

StatsDashboard.propTypes = {
  stats: PropTypes.arrayOf(
    PropTypes.shape({
      key: PropTypes.string.isRequired,
      label_sv: PropTypes.string.isRequired,
      label_en: PropTypes.string.isRequired,
      value: PropTypes.string.isRequired,
      trend_sv: PropTypes.string.isRequired,
      trend_en: PropTypes.string.isRequired,
      link: PropTypes.string,
    })
  ).isRequired,
  lang: PropTypes.string.isRequired,
};

const LoadingState = ({ lang }) => (
  <div className="loading-state glass">
    <div className="spinner"></div>
    <p>{lang === "sv" ? "Laddar dashboard..." : "Loading dashboard..."}</p>
    <style jsx>{`
      .loading-state {
        height: 80vh;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 20px;
      }
      .spinner {
        width: 50px;
        height: 50px;
        border: 3px solid var(--surface-light);
        border-top-color: var(--accent-primary);
        border-radius: 50%;
        animation: spin 1s linear infinite;
      }
      @keyframes spin { to { transform: rotate(360deg); } }
    `}</style>
  </div>
);

LoadingState.propTypes = {
  lang: PropTypes.string.isRequired,
};

const OutageList = ({ outages, lang, onOutageClick }) => (
  <div className="event-list custom-scrollbar">
    {outages.length > 0 ? (
      outages.slice(0, 15).map((outage) => (
        <Link 
          href={`/outages/${outage.id}`} 
          key={outage.id} 
          className="event-item"
          onClick={onOutageClick ? () => onOutageClick(outage) : undefined}
        >
          <div className="event-content">
            <div className="status-indicator-line" style={{ backgroundColor: outage.status.toLowerCase() === 'resolved' ? 'var(--status-success)' : 'var(--status-critical)' }}></div>
            <div className="event-text">
              <span className="event-title">{getOutageText(outage.title, lang)}</span>
              <div className="event-meta">
                <span>{outage.operator_name}</span>
                <span className="sep">•</span>
                <span>{outage.location || "Sweden"}</span>
                {outage.affected_services?.length > 0 && (
                  <>
                    <span className="sep">•</span>
                    <div className="dash-tags">
                      {outage.affected_services.slice(0, 2).map((s) => (
                        <span key={`${outage.id}-${s}`} className="dash-tag">{s}</span>
                      ))}
                    </div>
                  </>
                )}
              </div>
            </div>
            <span className="event-badge" style={{ color: outage.status.toLowerCase() === 'resolved' ? 'var(--status-success)' : 'var(--status-critical)' }}>
              {outage.status}
            </span>
          </div>
        </Link>
      ))
    ) : (
      <div className="empty-events">
        <Info size={24} />
        <p>{lang === "sv" ? "Inga matchande incidenter" : "No matching incidents"}</p>
      </div>
    )}
    <style jsx>{`
        .event-list {
          flex: 1;
          overflow-y: auto;
          display: flex;
          flex-direction: column;
          gap: 8px;
        }
        .event-item {
          display: block;
          border-bottom: 1px solid var(--border-color);
          text-decoration: none;
        }
        .event-item:last-child {
          border-bottom: none;
        }
        .event-content {
          padding: 12px 0;
          display: flex;
          align-items: center;
          gap: 16px;
          transition: var(--transition-base);
        }
        .event-item:hover .event-content {
          padding-left: 8px;
          background: var(--surface-hover);
        }
        .status-indicator-line {
          width: 3px;
          height: 32px;
          border-radius: 2px;
          flex-shrink: 0;
        }
        .event-text {
          flex: 1;
          display: flex;
          flex-direction: column;
          gap: 2px;
        }
        .event-title {
          font-weight: 600;
          font-size: 0.9rem;
          color: var(--text-primary);
        }
        .event-meta {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 0.75rem;
          color: var(--text-muted);
        }
        .sep { color: var(--text-muted); opacity: 0.5; }
        .event-badge {
          font-size: 0.7rem;
          font-weight: 700;
          text-transform: uppercase;
          letter-spacing: 0.05em;
        }
        .dash-tags { display: flex; gap: 4px; }
        .dash-tag {
           font-size: 0.65rem;
           background: var(--surface-hover);
           padding: 1px 5px;
           border-radius: 4px;
           color: var(--text-secondary);
           border: 1px solid var(--border-color);
           font-weight: 600;
        }
        .empty-events {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          height: 100%;
          gap: 12px;
          color: var(--text-muted);
          opacity: 0.7;
        }
    `}</style>
  </div>
);

OutageList.propTypes = {
  outages: PropTypes.array.isRequired,
  lang: PropTypes.string.isRequired,
  onOutageClick: PropTypes.func,
};

export default function Home() {
  const { lang } = useLanguage();
  const { addToast } = useToast();
  const [outages, setOutages] = useState([]);
  const [operators, setOperators] = useState([]);
  const [hotspots, setHotspots] = useState([]);
  const [loading, setLoading] = useState(true);
  const [trendData, setTrendData] = useState(null);
  const [mttrData, setMttrData] = useState([]);
  const [reliabilityData, setReliabilityData] = useState([]);
  const previousOutageIds = useRef(new Set());

  const [filters, setFilters] = useState({
    search: "",
    operators: [],
    severities: [],
    status: "active"
  });

  const [stats, setStats] = useState([
    { label_sv: "Aktiva Avbrott", label_en: "Active Outages", value: "0", trend_sv: "Laddar...", trend_en: "Loading...", color: "var(--status-critical)", key: "active_outages", link: "/reports?status=active" },
    { label_sv: "Genomsนิตrlig reparationstid", label_en: "Mean Time to Repair", value: "0h", trend_sv: "Beräknar...", trend_en: "Calculating...", color: "var(--accent-primary)", key: "mttr", link: "/analytics" },
    { label_sv: "Användarrapporter", label_en: "User Reports", value: "0", trend_sv: "Hämtar...", trend_en: "Fetching...", color: "var(--status-warning)", key: "reports", link: "/map" },
    { label_sv: "Nätverkstillförlitlighet", label_en: "Network Reliability", value: "100%", trend_sv: "Stabil", trend_en: "Stable", color: "var(--status-success)", key: "reliability", link: "/analytics" },
  ]);

  const updateStatsFromData = useCallback((data) => {
    const { outagesData, reportsData, hotspotsData, mttrData, reliabilityData } = data;
    
    const activeCount = outagesData.filter(o => o.status.toLowerCase() !== "resolved").length;
    const validMttr = mttrData.filter(d => d.outage_count > 0);
    const avgMttr = validMttr.length > 0
      ? (validMttr.reduce((acc, curr) => acc + curr.average_mttr_hours, 0) / validMttr.length).toFixed(1)
      : "0";
    const totalDowntime = reliabilityData.reduce((acc, curr) => acc + curr.total_downtime_hours, 0);
    const reliabilityScore = Math.max(0, 100 - (totalDowntime / 100)).toFixed(1);

    setStats(prev => prev.map(s => {
      const updated = { ...s };
      
      switch (s.key) {
        case "active_outages":
          updated.value = activeCount.toString();
          updated.trend_sv = `${outagesData.length} totalt registrerade`;
          updated.trend_en = `${outagesData.length} total recorded`;
          break;
        case "mttr": {
          const collectingText = lang === "sv" ? "Insamling..." : "Collecting...";
          const mttrVal = avgMttr === "0" ? collectingText : `${avgMttr}h`;
          updated.value = mttrVal;
          updated.trend_sv = validMttr.length > 0 ? `Snitt över ${validMttr.length} operatörer` : "Ingen data för lösta avbrott";
          updated.trend_en = validMttr.length > 0 ? `Avg across ${validMttr.length} operators` : "No resolved outages yet";
          break;
        }
        case "reports":
          updated.value = reportsData.length.toString();
          updated.trend_sv = `${hotspotsData.length} aktiva hotspots`;
          updated.trend_en = `${hotspotsData.length} active hotspots`;
          break;
        case "reliability":
          updated.value = `${reliabilityScore}%`;
          updated.trend_sv = "Senaste 30 dagarna";
          updated.trend_en = "Last 30 days";
          break;
      }
      return updated;
    }));

    if (previousOutageIds.current.size > 0) {
      const newOutages = outagesData.filter(o => !previousOutageIds.current.has(o.id));
      if (newOutages.length > 0) {
        const msgSv = `${newOutages.length} ny${newOutages.length > 1 ? 'a' : 't'} avbrott upptäckt!`;
        const msgEn = `${newOutages.length} new outage${newOutages.length > 1 ? 's' : ''} detected!`;
        addToast(lang === "sv" ? msgSv : msgEn, 'warning', 6000);
      }
    }
    previousOutageIds.current = new Set(outagesData.map(o => o.id));
  }, [lang, addToast]);

  const fetchDashboardData = useCallback(async () => {
    try {
      const [outagesData, reportsData, hotspotsData, mttrData, reliabilityData, historyData, operatorsData] = await Promise.all([
        api.outages.list(),
        api.reports.list(),
        api.reports.hotspots(),
        api.outages.mttr(),
        api.outages.reliability(),
        api.outages.history(),
        api.operators.list()
      ]);

      setOutages(outagesData);
      setOperators(operatorsData);
      setHotspots(hotspotsData);
      setTrendData(historyData);
      setMttrData(mttrData);
      setReliabilityData(reliabilityData);

      updateStatsFromData({
        outagesData, reportsData, hotspotsData, mttrData, reliabilityData
      });

      setLoading(false);
    } catch (err) {
      console.error("Failed to fetch dashboard data:", err);
    }
  }, [updateStatsFromData]);

  useEffect(() => {
    const timer = setTimeout(() => {
      fetchDashboardData();
    }, 0);
    const interval = setInterval(fetchDashboardData, 5 * 60 * 1000); // 5m
    return () => {
      clearTimeout(timer);
      clearInterval(interval);
    };
  }, [fetchDashboardData]);

  const filteredOutages = useMemo(() => {
    return outages.filter(o => {
      const titleText = getOutageText(o.title, lang);
      const severity = (o.severity || "").toLowerCase();
      const status = (o.status || "").toLowerCase();
      const matchesSearch = !filters.search ||
        titleText.toLowerCase().includes(filters.search.toLowerCase()) ||
        o.location?.toLowerCase().includes(filters.search.toLowerCase());

      const matchesOperator = filters.operators.length === 0 ||
        filters.operators.includes(o.operator_name);

      const matchesSeverity = filters.severities.length === 0 ||
        filters.severities.map(item => item.toLowerCase()).includes(severity);

      let matchesStatus = true;
      if (filters.status === "active") {
        matchesStatus = status !== "resolved";
      } else if (filters.status === "resolved") {
        matchesStatus = status === "resolved";
      }

      return matchesSearch && matchesOperator && matchesSeverity && matchesStatus;
    });
  }, [outages, filters, lang]);

  if (loading) return <LoadingState lang={lang} />;

  return (
    <div className="dashboard-container animate-fade-in">
      <header className="dashboard-header">
        <div className="header-text">
          <h1 className="text-gradient">
            {lang === "sv" ? "Nätverksöversikt" : "Network Overview"}
          </h1>
          <p className="subtitle">
            {lang === "sv"
              ? "Driftstatus för Sveriges telekomnätverk"
              : "Operational status for Sweden's telecom infrastructure"}
          </p>
        </div>
        <div className="system-status">
          <span className="status-dot"></span>
          {lang === "sv" ? "System Aktivt" : "System Live"}
        </div>
      </header>

      <StatsDashboard stats={stats} lang={lang} />

      <FilterBar
        operators={operators}
        onFilterChange={setFilters}
        initialFilters={filters}
      />

      <div className="dashboard-main-grid">
        <div className="premium-card chart-view">
          <div className="card-header">
            <h3 className="section-title">{lang === "sv" ? "Regional Distribution" : "Incident Map"}</h3>
            <div className="map-legend">
              <span className="legend-item"><span className="dot" style={{ backgroundColor: 'var(--status-critical)' }}></span> {lang === "sv" ? "Avbrott" : "Outages"}</span>
              <span className="legend-item"><span className="dot" style={{ backgroundColor: 'var(--status-warning)' }}></span> {lang === "sv" ? "Fokusområden" : "Hotspots"}</span>
            </div>
          </div>
          <div className="map-area">
            <TacticalMap outages={filteredOutages} hotspots={hotspots} simple={true} />
          </div>
        </div>

        <div className="premium-card list-view">
          <div className="card-header">
            <h3 className="section-title">{lang === "sv" ? "Händelseflöde" : "Event Stream"}</h3>
            <div className="count-badge">{filteredOutages.length}</div>
          </div>
          <OutageList outages={filteredOutages} lang={lang} />
        </div>
      </div>

      <div className="premium-card analysis-card">
        <h3 className="section-title">{lang === "sv" ? "Trendanalys (30 dagar)" : "Trend Analysis (30 days)"}</h3>
        <HistoricalTrend data={trendData} />
      </div>

      <div className="premium-card analysis-card">
        <h3 className="section-title">{lang === "sv" ? "Operatörsjämförelse" : "Operator Comparison"}</h3>
        <OperatorComparison mttrData={mttrData} reliabilityData={reliabilityData} />
      </div>

      <style jsx>{`
        .dashboard-container {
          padding: 32px;
          max-width: 1400px;
          margin: 0 auto;
        }

        .dashboard-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          margin-bottom: 40px;
          padding-bottom: 24px;
          border-bottom: 1px solid var(--border-color);
        }

        .dashboard-header h1 {
          font-size: 1.8rem;
          margin-bottom: 4px;
        }

        .subtitle {
          color: var(--text-muted);
          font-size: 0.95rem;
        }

        .system-status {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 0.75rem;
          font-weight: 700;
          color: var(--text-muted);
          text-transform: uppercase;
          letter-spacing: 0.05em;
        }

        .status-dot {
          width: 6px;
          height: 6px;
          background: var(--status-success);
          border-radius: 50%;
        }

        .dashboard-main-grid {
          display: grid;
          grid-template-columns: 2fr 1fr;
          gap: 32px;
          margin-bottom: 32px;
        }

        .chart-view, .list-view {
          height: 560px;
          display: flex;
          flex-direction: column;
        }

        .card-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 20px;
        }

        .section-title {
          font-size: 1.1rem;
          font-weight: 700;
        }

        .map-legend {
          display: flex;
          gap: 16px;
        }

        .legend-item {
          display: flex;
          align-items: center;
          gap: 6px;
          font-size: 0.75rem;
          color: var(--text-muted);
          font-weight: 600;
        }

        .legend-item .dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
        }

        .map-area {
          flex: 1;
          border-radius: var(--radius-md);
          overflow: hidden;
          border: 1px solid var(--border-color);
        }

        .analysis-card {
          margin-bottom: 32px;
        }

        @media (max-width: 1400px) {
          .stats-grid { grid-template-columns: repeat(2, 1fr); }
        }

        @media (max-width: 1100px) {
          .dashboard-main-grid { grid-template-columns: 1fr; }
          .chart-view, .list-view { height: auto; min-height: 400px; }
        }

        @media (max-width: 768px) {
          .dashboard-container { padding: 20px; }
          .dashboard-header { flex-direction: column; align-items: flex-start; gap: 16px; }
          .stats-grid { grid-template-columns: 1fr; }
          .dashboard-header h1 { font-size: 1.5rem; }
        }
      `}</style>
    </div>
  );
}
