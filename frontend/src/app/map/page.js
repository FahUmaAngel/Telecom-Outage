"use client";

import dynamic from "next/dynamic";
import { useEffect, useState } from "react";
import { api } from "../../lib/api";
import { useLanguage } from "../../context/LanguageContext";

// Dynamic import for Map to avoid SSR issues with Leaflet
const Map = dynamic(() => import("../../components/Map/Map"), {
    ssr: false,
    loading: () => <div className="map-placeholder glass">Initializing Navigation Satellite...</div>
});

export default function MapPage() {
    const { lang } = useLanguage();
    const [outages, setOutages] = useState([]);
    const [hotspots, setHotspots] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const [outagesData, hotspotsData] = await Promise.all([
                    api.outages.list(),
                    api.reports.hotspots()
                ]);
                setOutages(outagesData);
                setHotspots(hotspotsData);
            } catch (err) {
                console.error("Failed to fetch map data:", err);
            } finally {
                setLoading(false);
            }
        };

        fetchData();

        // WebSocket Setup for Real-time Updates
        const wsUrl = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/ws";
        console.log("Connecting to WebSocket:", wsUrl);
        
        let socket;
        let reconnectTimeout;

        const connect = () => {
            socket = new WebSocket(wsUrl);

            socket.onopen = () => {
                console.log("✓ Connected to Outage WebSocket");
            };

            socket.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    if (data.type === "OUTAGE_UPDATE") {
                        console.log("⚡ Real-time update received! Refreshing data...");
                        fetchData();
                    }
                } catch (err) {
                    console.error("Error parsing WebSocket message:", err);
                }
            };

            socket.onclose = () => {
                console.log("WebSocket disconnected. Reconnecting in 5s...");
                reconnectTimeout = setTimeout(connect, 5000);
            };

            socket.onerror = (err) => {
                console.error("WebSocket error:", err);
                socket.close();
            };
        };

        connect();

        return () => {
            if (socket) socket.close();
            if (reconnectTimeout) clearTimeout(reconnectTimeout);
        };
    }, []);

    return (
        <div className="map-page animate-fade-in">
            <div className="page-header">
                <h1 className="font-heading">
                    {lang === "sv" ? "Live-karta" : "Live Outage Map"}
                </h1>
                <p className="subtitle">
                    {lang === "sv" ? "Realtidsövervakning av nätverksstatus i Sverige" : "Real-time visualization of network health across Sweden"}
                </p>
            </div>

            <div className="map-container-main">
                <Map outages={outages} hotspots={hotspots} />

                <div className="map-legend premium-card glass">
                    <h4 className="font-heading">Legend</h4>
                    <div className="legend-item">
                        <span className="dot" style={{ backgroundColor: "#0070f3" }}></span> Telia
                    </div>
                    <div className="legend-item">
                        <span className="dot" style={{ backgroundColor: "#ff4d4f" }}></span> Tre (3)
                    </div>
                    <div className="legend-item">
                        <span className="dot" style={{ backgroundColor: "#007bff" }}></span> Telenor
                    </div>
                </div>
            </div>

            <style jsx>{`
        .map-page {
          height: calc(100vh - var(--header-height) - 80px);
          display: flex;
          flex-direction: column;
        }
        .page-header {
          margin-bottom: 20px;
        }
        .map-container-main {
          flex: 1;
          position: relative;
          min-height: 500px;
        }
        .map-legend {
          position: absolute;
          bottom: 20px;
          right: 20px;
          z-index: 1000;
          padding: 15px;
          min-width: 140px;
        }
        .legend-item {
          display: flex;
          align-items: center;
          gap: 10px;
          margin-top: 8px;
          font-size: 0.9rem;
          color: var(--text-secondary);
        }
        .dot {
          width: 12px;
          height: 12px;
          border-radius: 50%;
        }
      `}</style>
        </div>
    );
}
