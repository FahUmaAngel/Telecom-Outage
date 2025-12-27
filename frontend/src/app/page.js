"use client";

import { useEffect, useState, useMemo, useRef } from "react";
import dynamic from "next/dynamic";
import { api } from "../lib/api";
import { useLanguage } from "../context/LanguageContext";
import { useToast } from "../context/ToastContext";
import Link from "next/link";

// Dynamically import Map to avoid SSR errors with Leaflet
const Map = dynamic(() => import("../components/Map/Map"), {
  ssr: false,
  loading: () => <div className="map-placeholder glass">Loading Map...</div>,
});

const HistoricalTrend = dynamic(() => import("../components/Analytics/HistoricalTrend"), {
  ssr: false,
});

const OperatorComparison = dynamic(() => import("../components/Analytics/OperatorComparison"), {
  ssr: false,
});

export default function Home() {
  const { lang, t } = useLanguage();
  const { addToast } = useToast();
  const [outages, setOutages] = useState([]);
  const [hotspots, setHotspots] = useState([]);
  const [loading, setLoading] = useState(true);
  const [trendData, setTrendData] = useState(null);
  const [mttrData, setMttrData] = useState([]);
  const [reliabilityData, setReliabilityData] = useState([]);
  const previousOutageIds = useRef(new Set());
  const [stats, setStats] = useState([
    { label_sv: "Aktiva Avbrott", label_en: "Active Outages", value: "0", trend_sv: "Laddar...", trend_en: "Loading...", color: "var(--status-critical)", key: "active_outages" },
    { label_sv: "Genomsnittlig reparationstid", label_en: "Mean Time to Repair", value: "0h", trend_sv: "Beräknar...", trend_en: "Calculating...", color: "var(--accent-primary)", key: "mttr" },
    { label_sv: "Användarrapporter", label_en: "User Reports", value: "0", trend_sv: "Hämtar...", trend_en: "Fetching...", color: "var(--status-warning)", key: "reports" },
    { label_sv: "Nätverkstillförlitlighet", label_en: "Network Reliability", value: "100%", trend_sv: "Stabil", trend_en: "Stable", color: "var(--status-success)", key: "reliability" },
  ]);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        const [outagesData, reportsData, hotspotsData, mttrData, reliabilityData, historyData] = await Promise.all([
          api.outages.list(),
          api.reports.list(),
          api.reports.hotspots(),
          api.outages.mttr(),
          api.outages.reliability(),
          api.outages.history(),
        ]);

        setOutages(outagesData);
        setHotspots(hotspotsData);
        setTrendData(historyData);
        setMttrData(mttrData);
        setReliabilityData(reliabilityData);
        const activeCount = outagesData.filter(o => o.status !== "resolved").length;

        // Calculate aggregate MTTR
        const validMttr = mttrData.filter(d => d.outage_count > 0);
        const avgMttr = validMttr.length > 0
          ? (validMttr.reduce((acc, curr) => acc + curr.average_mttr_hours, 0) / validMttr.length).toFixed(1)
          : "0";

        // Calculate aggregate Reliability
        const totalDowntime = reliabilityData.reduce((acc, curr) => acc + curr.total_downtime_hours, 0);
        const reliabilityScore = Math.max(0, 100 - (totalDowntime / 100)).toFixed(1);

        setStats(prev => prev.map(s => {
          if (s.key === "active_outages") return {
            ...s,
            value: activeCount.toString(),
            trend_sv: `${outagesData.length} totalt registrerade`,
            trend_en: `${outagesData.length} total recorded`
          };
          if (s.key === "mttr") return {
            ...s,
            value: `${avgMttr}h`,
            trend_sv: `Snitt över ${validMttr.length} operatörer`,
            trend_en: `Avg across ${validMttr.length} operators`
          };
          if (s.key === "reports") return {
            ...s,
            value: reportsData.length.toString(),
            trend_sv: `${hotspotsData.length} aktiva hotspots`,
            trend_en: `${hotspotsData.length} active hotspots`
          };
          if (s.key === "reliability") return {
            ...s,
            value: `${reliabilityScore}%`,
            trend_sv: "Senaste 30 dagarna",
            trend_en: "Last 30 days"
          };
          return s;
        }));

        // Detect new outages and show toast
        if (previousOutageIds.current.size > 0) {
          const newOutages = outagesData.filter(o => !previousOutageIds.current.has(o.id));
          if (newOutages.length > 0) {
            const message = lang === "sv"
              ? `${newOutages.length} ny${newOutages.length > 1 ? 'a' : 't'} avbrott upptäckt!`
              : `${newOutages.length} new outage${newOutages.length > 1 ? 's' : ''} detected!`;
            addToast(message, 'warning', 6000);
          }
        }

        // Update previous outage IDs
        previousOutageIds.current = new Set(outagesData.map(o => o.id));

        setLoading(false);
      } catch (err) {
        console.error("Failed to fetch dashboard data:", err);
      }
    };

    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, 60000); // Refresh every 1m
    return () => clearInterval(interval);
  }, []);

  const activeOutages = useMemo(() => outages.filter(o => o.status !== "resolved"), [outages]);

  if (loading) {
    return (
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
          @keyframes spin {
            to { transform: rotate(360deg); }
          }
        `}</style>
      </div>
    );
  }

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

      <div className="stats-grid">
        {stats.map((stat, i) => (
          <div key={i} className="premium-card stat-card">
            <div className="stat-content">
              <span className="stat-label">{lang === "sv" ? stat.label_sv : stat.label_en}</span>
              <h2 className="stat-value">{stat.value}</h2>
              <span className="stat-meta">{lang === "sv" ? stat.trend_sv : stat.trend_en}</span>
            </div>
          </div>
        ))}
      </div>

      <div className="dashboard-main-grid">
        <div className="premium-card chart-view">
          <div className="card-header">
            <h3 className="section-title">{lang === "sv" ? "Regional Distribution" : "Incident Map"}</h3>
            <div className="map-legend">
              <span className="legend-item"><span className="dot" style={{ backgroundColor: 'var(--status-critical)' }}></span> {lang === "sv" ? "Avbrott" : "Outages"}</span>
              <span className="legend-item"><span className="dot" style={{ backgroundColor: 'var(--status-warning)' }}></span> {lang === "sv" ? "Hotspots" : "Hotspots"}</span>
            </div>
          </div>
          <div className="map-area">
            <Map outages={activeOutages} hotspots={hotspots} simple={true} />
          </div>
        </div>

        <div className="premium-card list-view">
          <div className="card-header">
            <h3 className="section-title">{lang === "sv" ? "Händelseflöde" : "Event Stream"}</h3>
            <Link href="/reports" className="view-link">{lang === "sv" ? "Visa alla" : "View all"}</Link>
          </div>
          <div className="event-list custom-scrollbar">
            {outages.slice(0, 10).map((outage) => (
              <Link href={`/outages/${outage.id}`} key={outage.id} className="event-item">
                <div className="event-content">
                  <div className="status-indicator-line" style={{ backgroundColor: outage.status === 'resolved' ? 'var(--status-success)' : 'var(--status-critical)' }}></div>
                  <div className="event-text">
                    <span className="event-title">{t(outage.title)}</span>
                    <div className="event-meta">
                      <span>{outage.operator_name}</span>
                      <span className="sep">•</span>
                      <span>{outage.location || "Sweden"}</span>
                      {outage.affected_services?.length > 0 && (
                        <>
                          <span className="sep">•</span>
                          <div className="dash-tags">
                            {outage.affected_services.slice(0, 2).map((s, i) => (
                              <span key={i} className="dash-tag">{s}</span>
                            ))}
                          </div>
                        </>
                      )}
                    </div>
                  </div>
                  <span className="event-badge" style={{ color: outage.status === 'resolved' ? 'var(--status-success)' : 'var(--status-critical)' }}>
                    {outage.status}
                  </span>
                </div>
              </Link>
            ))}
          </div>
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

        .event-badge {
          font-size: 0.7rem;
          font-weight: 700;
          text-transform: uppercase;
          letter-spacing: 0.05em;
        }

        .view-link {
          font-size: 0.8rem;
          font-weight: 700;
          color: var(--accent-primary);
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
