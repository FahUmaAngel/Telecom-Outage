import { MapContainer, TileLayer, Marker, Popup, useMap, LayersControl, LayerGroup } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { useEffect, useState, useMemo } from "react";
import { useTheme } from "../../context/ThemeContext";
import { useLanguage } from "../../context/LanguageContext";
import Link from "next/link";
import MarkerClusterGroup from "react-leaflet-cluster";
import { Layers, Map as MapIcon, Flame } from "lucide-react";

// Marker Cluster CSS
import 'react-leaflet-cluster/dist/assets/MarkerCluster.css';
import 'react-leaflet-cluster/dist/assets/MarkerCluster.Default.css';

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
    telenor: "#007bff",
    unknown: "#94a3b8"
};

const cityCoords = {
    // ... same as before
    "Stockholm": [59.3293, 18.0686],
    "Göteborg": [57.7089, 11.9746],
    "Malmö": [55.6050, 13.0038],
    "Uppsala": [59.8586, 17.6389],
    "Västerås": [59.6100, 16.5448],
    "Örebro": [59.2753, 15.2134],
    "Linköping": [58.4108, 15.6214],
    "Helsingborg": [56.0465, 12.6945],
    "Jönköping": [57.7826, 14.1618],
    "Norrköping": [58.5877, 16.1819],
    "Stockholms län": [59.3293, 18.0686],
    "Västra Götalands län": [58.0, 13.0],
    "Skåne län": [55.9, 13.5],
    "Uppsala län": [59.8586, 17.6389],
    "Östergötlands län": [58.4108, 15.6214],
    "Jönköpings län": [57.7826, 14.1618],
    "Kronobergs län": [56.8777, 14.8091],
    "Kalmar län": [56.6634, 16.3567],
    "Gotlands län": [57.6348, 18.2948],
    "Blekinge län": [56.1612, 15.5869],
    "Hallands län": [56.8945, 12.8421],
    "Värmlands län": [59.4021, 13.5115],
    "Örebro län": [59.2753, 15.2134],
    "Västmanlands län": [59.6100, 16.5448],
    "Dalarnas län": [60.6749, 15.0784],
    "Gävleborgs län": [61.0, 16.0],
    "Västernorrlands län": [62.6315, 17.9386],
    "Jämtlands län": [63.1792, 14.6357],
    "Västerbottens län": [64.7507, 18.0542],
    "Norrbottens län": [66.8309, 20.3987],
    "Södermanlands län": [59.0333, 16.75]
};

const hotspotIcon = new L.DivIcon({
    html: `<div style="background-color: #faad14; width: 16px; height: 16px; border-radius: 50%; border: 2px solid white; box-shadow: 0 0 15px #faad14; animation: pulse 2s infinite"></div>`,
    className: "hotspot-marker-icon",
    iconSize: [16, 16],
});

function HeatmapLayer({ points = [] }) {
    const map = useMap();

    useEffect(() => {
        if (typeof window === "undefined") return;
        require("leaflet.heat");

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
        const timer = setTimeout(() => {
            map.invalidateSize();
        }, 100);
        const observer = new ResizeObserver(() => {
            map.invalidateSize();
        });
        const container = map.getContainer();
        if (container) observer.observe(container);
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
    const [viewMode, setViewMode] = useState("markers"); // "markers" or "heatmap"

    useEffect(() => {
        setMounted(true);
    }, []);

    const heatPoints = useMemo(() => {
        const points = [];
        // Add official outages to heatmap
        outages.forEach(o => {
            let lat = o.latitude, lng = o.longitude;
            if (!lat && o.location && cityCoords[o.location]) [lat, lng] = cityCoords[o.location];
            if (lat && lng) points.push([lat, lng, 0.8]);
        });
        // Add crowd hotspots to heatmap
        hotspots.forEach(h => {
            if (h.latitude && h.longitude) points.push([h.latitude, h.longitude, (h.report_count || 1) * 0.4]);
        });
        return points;
    }, [outages, hotspots]);

    if (!mounted) return null;

    const tileUrl = theme === "dark"
        ? "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
        : "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png";

    const swedenCenter = [62.19, 17.56];

    return (
        <div className={`map-wrapper ${simple ? 'map-simple' : ''}`} style={{ height: "100%", width: "100%", position: "relative" }}>
            <MapContainer
                center={swedenCenter}
                zoom={5}
                style={{ height: "100%", width: "100%", borderRadius: "12px" }}
                scrollWheelZoom={true}
                dragging={true}
                zoomControl={true}
            >
                <TileLayer
                    attribution='&copy; <a href="https://carto.com/attributions">CARTO</a>'
                    url={tileUrl}
                />
                {!simple && <ResizeFix />}

                {viewMode === "heatmap" ? (
                    <HeatmapLayer points={heatPoints} />
                ) : (
                    <MarkerClusterGroup
                        chunkedLoading
                        maxClusterRadius={50}
                        showCoverageOnHover={false}
                        spiderfyOnMaxZoom={true}
                    >
                        {/* Official Outages */}
                        {outages.map((outage) => {
                            let lat = outage.latitude;
                            let lng = outage.longitude;

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
                                            <div className="popup-header">
                                                <span className="op-tag" style={{ background: operatorColors[outage.operator_name.toLowerCase()] }}>
                                                    {outage.operator_name}
                                                </span>
                                                <h3 className="font-heading">{t(outage.title)}</h3>
                                            </div>
                                            <div className="popup-body">
                                                <p><strong>Status:</strong> {outage.status}</p>
                                                <p><strong>Severity:</strong> <span className={`severity-${outage.severity.toLowerCase()}`}>{outage.severity}</span></p>
                                            </div>
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
                                            {lang === "sv" ? "Hotspot (Crowd)" : "Hotspot (Crowd)"}
                                        </h3>
                                        <p><strong>Operator:</strong> {hotspot.operator_name}</p>
                                        <p><strong>Reports:</strong> {hotspot.report_count}</p>
                                        <p className="detected-at">
                                            <small>{new Date(hotspot.detected_at).toLocaleString()}</small>
                                        </p>
                                    </div>
                                </Popup>
                            </Marker>
                        ))}
                    </MarkerClusterGroup>
                )}
            </MapContainer>

            {/* Premium Mode Toggle UI */}
            {!simple && (
                <div className="map-mode-toggle glass">
                    <button
                        className={viewMode === "markers" ? "active" : ""}
                        onClick={() => setViewMode("markers")}
                        title="Marker View"
                    >
                        <MapIcon size={16} />
                        <span>Markers</span>
                    </button>
                    <button
                        className={viewMode === "heatmap" ? "active" : ""}
                        onClick={() => setViewMode("heatmap")}
                        title="Heatmap View"
                    >
                        <Flame size={16} />
                        <span>Heatmap</span>
                    </button>
                </div>
            )}

            <style jsx global>{`
                @keyframes pulse {
                    0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(250, 173, 20, 0.7); }
                    70% { transform: scale(1); box-shadow: 0 0 0 10px rgba(250, 173, 20, 0); }
                    100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(250, 173, 20, 0); }
                }

                .map-mode-toggle {
                    position: absolute;
                    bottom: 24px;
                    left: 24px;
                    z-index: 1000;
                    display: flex;
                    gap: 4px;
                    padding: 4px;
                    border-radius: 12px;
                    border: 1px solid var(--border-color);
                }
                .map-mode-toggle button {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    padding: 8px 16px;
                    border: none;
                    background: transparent;
                    color: var(--text-muted);
                    font-weight: 700;
                    font-size: 0.8rem;
                    cursor: pointer;
                    border-radius: 8px;
                    transition: var(--transition-base);
                }
                .map-mode-toggle button.active {
                    background: var(--accent-primary);
                    color: white;
                    box-shadow: 0 4px 12px var(--accent-glow);
                }
                
                .premium-popup .leaflet-popup-content-wrapper {
                    background: var(--surface-hover);
                    backdrop-filter: blur(12px);
                    border: 1px solid var(--border-color);
                    border-radius: 16px;
                    padding: 12px;
                    box-shadow: var(--shadow-xl);
                }
                .popup-header { margin-bottom: 12px; }
                .op-tag { 
                    font-size: 0.6rem; 
                    font-weight: 800; 
                    color: white; 
                    padding: 2px 8px; 
                    border-radius: 4px;
                    text-transform: uppercase;
                    margin-bottom: 4px;
                    display: inline-block;
                }
                .popup-content h3 { margin: 4px 0 0 0; font-size: 1rem; color: var(--text-primary); }
                .popup-body { margin: 12px 0; font-size: 0.85rem; color: var(--text-secondary); }
                .popup-body p { margin: 4px 0; }
                .popup-actions { border-top: 1px solid var(--border-color); padding-top: 10px; margin-top: 10px; }
                .detail-link { color: var(--accent-primary); font-weight: 700; text-decoration: none; font-size: 0.85rem; }
                
                /* Clustering Styles Override */
                .marker-cluster-small { background-color: rgba(var(--accent-primary-rgb), 0.6); }
                .marker-cluster-small div { background-color: rgba(var(--accent-primary-rgb), 0.8); color: white; }
                .marker-cluster-medium { background-color: rgba(var(--accent-primary-rgb), 0.7); }
                .marker-cluster-medium div { background-color: rgba(var(--accent-primary-rgb), 0.9); color: white; }
                .marker-cluster-large { background-color: rgba(var(--accent-primary-rgb), 0.8); }
                .marker-cluster-large div { background-color: var(--accent-primary); color: white; }
            `}</style>
        </div>
    );
}
