"use client";

import { MapContainer, TileLayer, Marker, Popup, useMap } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { useEffect, useState, useMemo } from "react";
import { useTheme } from "../../context/ThemeContext";
import { useLanguage } from "../../context/LanguageContext";
import Link from "next/link";

if (typeof window !== "undefined") {
    require("leaflet.heat");
}

// Fix for default marker icons in Leaflet with React
const DefaultIcon = L.icon({
    iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
    shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
    iconSize: [25, 41],
    iconAnchor: [12, 41],
});
L.Marker.prototype.options.icon = DefaultIcon;

// Custom icons for operators
const createCustomIcon = (color) => new L.DivIcon({
    html: `<div style="background-color: ${color}; width: 12px; height: 12px; border-radius: 50%; border: 2px solid white; box-shadow: 0 0 10px ${color}"></div>`,
    className: "custom-marker-icon",
    iconSize: [12, 12],
});

const operatorColors = {
    telia: "#0070f3",
    tre: "#ff4d4f",
    lycamobile: "#52c41a",
    unknown: "#94a3b8"
};

const cityCoords = {
    "Stockholm": [59.3293, 18.0686],
    "Göteborg": [57.7089, 11.9746],
    "Malmö": [55.6050, 13.0038],
    "Uppsala": [59.8586, 17.6389],
    "Västerås": [59.6100, 16.5448],
    "Örebro": [59.2753, 15.2134],
    "Linköping": [58.4108, 15.6214],
    "Helsingborg": [56.0465, 12.6945],
    "Jönköping": [57.7826, 14.1618],
    "Norrköping": [58.5877, 16.1819]
};

const hotspotIcon = new L.DivIcon({
    html: `<div style="background-color: #faad14; width: 16px; height: 16px; border-radius: 50%; border: 3px solid white; box-shadow: 0 0 15px #faad14; animation: pulse 2s infinite"></div>`,
    className: "hotspot-marker-icon",
    iconSize: [16, 16],
});

function HeatmapLayer({ points = [] }) {
    const map = useMap();

    useEffect(() => {
        const container = map.getContainer();
        if (!map || points.length === 0 || !L.heatLayer || !container || container.clientHeight === 0) return;

        const heatLayer = L.heatLayer(points, {
            radius: 35,
            blur: 15,
            maxZoom: 10,
            gradient: { 0.1: 'blue', 0.2: 'cyan', 0.4: 'lime', 0.6: 'yellow', 1: 'red' }
        }).addTo(map);

        return () => {
            if (map && heatLayer) {
                map.removeLayer(heatLayer);
            }
        };
    }, [map, points]);

    return null;
}

function ResizeFix() {
    const map = useMap();
    useEffect(() => {
        // Initial invalidation
        const timer = setTimeout(() => {
            map.invalidateSize();
        }, 100);

        // ResizeObserver for container changes
        const observer = new ResizeObserver(() => {
            map.invalidateSize();
        });

        const container = map.getContainer();
        if (container) {
            observer.observe(container);
        }

        return () => {
            clearTimeout(timer);
            observer.disconnect();
        };
    }, [map]);
    return null;
}

export default function Map({ outages = [], hotspots = [], simple = false }) {
    const { theme } = useTheme();
    const { lang, t } = useLanguage();
    const [mounted, setMounted] = useState(false);

    useEffect(() => {
        setMounted(true);
    }, []);

    const heatPoints = useMemo(() => {
        if (simple) return []; // Disable heatmap in simple mode
        return hotspots
            .filter(h => h && h.latitude && h.longitude)
            .map(h => [h.latitude, h.longitude, (h.report_count || 1) * 0.5]);
    }, [hotspots, simple]);

    if (!mounted) return null;

    const tileUrl = theme === "dark"
        ? "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
        : "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png";

    const swedenCenter = [62.19, 17.56];

    return (
        <div className={`map-wrapper ${simple ? 'map-simple' : ''}`} style={{ height: "100%", width: "100%" }}>
            <MapContainer
                center={swedenCenter}
                zoom={5}
                style={{ height: "100%", width: "100%", borderRadius: "12px" }}
                scrollWheelZoom={true}
                dragging={true}
                zoomControl={true}
                doubleClickZoom={true}
                attributionControl={true}
            >
                <TileLayer
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
                    url={tileUrl}
                />
                {!simple && <ResizeFix />}
                {!simple && <HeatmapLayer points={heatPoints} />}

                {/* Official Outages */}
                {outages.map((outage) => {
                    let lat = outage.latitude;
                    let lng = outage.longitude;

                    // Fallback to city coordinates if missing
                    if (!lat && outage.location && cityCoords[outage.location]) {
                        [lat, lng] = cityCoords[outage.location];
                    }

                    if (!lat || !lng) return null;

                    return (
                        <Marker
                            key={`outage-${outage.id}`}
                            position={[lat, lng]}
                            icon={createCustomIcon(operatorColors[outage.operator_name.toLowerCase()] || operatorColors.unknown)}
                        >
                            <Popup className="premium-popup">
                                <div className="popup-content">
                                    <h3 className="font-heading">{t(outage.title)}</h3>
                                    <p className="operator"><strong>Operator:</strong> {outage.operator_name}</p>
                                    <p className="status"><strong>Status:</strong> {outage.status}</p>
                                    <p className="severity"><strong>Severity:</strong> {outage.severity}</p>
                                    {outage.location && <p className="location"><strong>Location:</strong> {outage.location}</p>}
                                    <div className="popup-actions">
                                        <Link href={`/outages/${outage.id}`} className="detail-link">
                                            {lang === "sv" ? "Visa detaljer →" : "View details →"}
                                        </Link>
                                    </div>
                                </div>
                            </Popup>
                        </Marker>
                    );
                })}

                {/* Crowd Hotspots */}
                {hotspots.map((hotspot, idx) => (
                    <Marker
                        key={`hotspot-${idx}`}
                        position={[hotspot.latitude, hotspot.longitude]}
                        icon={hotspotIcon}
                    >
                        <Popup className="premium-popup">
                            <div className="popup-content">
                                <h3 className="font-heading" style={{ color: "#faad14" }}>
                                    {lang === "sv" ? "Möjligt Avbrott (Crowd)" : "Possible Outage (Crowd)"}
                                </h3>
                                <p><strong>Operator:</strong> {hotspot.operator_name}</p>
                                <p><strong>Reports:</strong> {hotspot.report_count}</p>
                                <p><strong>Type:</strong> {hotspot.type}</p>
                                {hotspot.source && <p><strong>Source:</strong> {hotspot.source}</p>}
                                <p className="detected-at">
                                    <small>{new Date(hotspot.detected_at).toLocaleString()}</small>
                                </p>
                            </div>
                        </Popup>
                    </Marker>
                ))}
            </MapContainer>

            <style jsx global>{`
        @keyframes pulse {
            0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(250, 173, 20, 0.7); }
            70% { transform: scale(1); box-shadow: 0 0 0 10px rgba(250, 173, 20, 0); }
            100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(250, 173, 20, 0); }
        }
        .leaflet-container {
          background: var(--bg-color) !important;
        }
        .premium-popup .leaflet-popup-content-wrapper {
          background: var(--glass-bg);
          backdrop-filter: blur(10px);
          border: 1px solid var(--glass-border);
          color: var(--text-primary);
          border-radius: 12px;
          padding: 8px;
        }
        .premium-popup .leaflet-popup-tip {
          background: var(--glass-bg);
          backdrop-filter: blur(10px);
        }
        .popup-content h3 {
          margin: 0 0 8px 0;
          font-size: 1rem;
          color: var(--accent-primary);
        }
        .popup-content p {
          margin: 4px 0;
          font-size: 0.85rem;
        }
        .detected-at {
          color: var(--text-muted);
          margin-top: 8px !important;
          border-top: 1px solid var(--glass-border);
          padding-top: 4px;
        }
        .popup-actions {
          margin-top: 12px;
          border-top: 1px solid var(--glass-border);
          padding-top: 8px;
        }
        .detail-link {
          color: var(--accent-primary);
          font-weight: 600;
          font-size: 0.85rem;
          text-decoration: none;
        }
        .detail-link:hover {
          text-decoration: underline;
        }
      `}</style>
        </div>
    );
}
