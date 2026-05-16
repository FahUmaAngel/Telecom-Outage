"use client";

import { useSearchParams, useRouter } from "next/navigation";
import { useLanguage } from "../../context/LanguageContext";
import { api } from "../../lib/api";
import { useEffect, useState, Suspense } from "react";
import Link from "next/link";
import { AlertCircle, ChevronLeft } from "lucide-react";

const LoadingState = () => (
    <div style={{ height: "70vh", display: "grid", placeItems: "center" }}>
        <div className="spinner" />
        <style jsx>{`
            .spinner {
                width: 40px;
                height: 40px;
                border: 3px solid var(--surface-light);
                border-top-color: var(--accent-primary);
                border-radius: 50%;
                animation: spin 1s linear infinite;
            }
            @keyframes spin { to { transform: rotate(360deg); } }
        `}</style>
    </div>
);

const ErrorState = ({ message, onBack, lang }) => (
    <div className="glass" style={{ padding: 40, marginTop: 30, textAlign: "center" }}>
        <AlertCircle size={44} style={{ color: "var(--status-critical)", opacity: 0.9 }} />
        <h2 style={{ marginTop: 14 }}>{message}</h2>
        <button onClick={onBack} className="btn">
            {lang === "sv" ? "Gå tillbaka" : "Go back"}
        </button>
        <style jsx>{`
            .btn {
                margin-top: 14px;
                padding: 10px 18px;
                background: var(--accent-primary);
                color: white;
                border: none;
                border-radius: 10px;
                font-weight: 800;
                cursor: pointer;
            }
        `}</style>
    </div>
);

function OutageDetailContent() {
    const { lang } = useLanguage();
    const router = useRouter();
    const searchParams = useSearchParams();
    const id = searchParams.get("id");

    const [outage, setOutage] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        let mounted = true;
        async function load() {
            if (!id) {
                setLoading(false);
                setError(lang === "sv" ? "Saknar outage-id" : "Missing outage id");
                return;
            }
            setLoading(true);
            setError(null);
            try {
                const data = await api.outages.get(id);
                if (!mounted) return;
                setOutage(data);
            } catch (err) {
                if (!mounted) return;
                setError(err?.message || (lang === "sv" ? "Kunde inte hämta driftstörning" : "Failed to load outage"));
            } finally {
                if (mounted) setLoading(false);
            }
        }
        load();
        return () => { mounted = false; };
    }, [id, lang]);

    const onBack = () => router.back();

    if (loading) return <LoadingState />;
    if (error || !outage) return <ErrorState message={error || "Not found"} onBack={onBack} lang={lang} />;

    return (
        <div style={{ padding: 32, maxWidth: 1200, margin: "0 auto" }} className="animate-fade-in">
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 18 }}>
                <button onClick={onBack} className="back">
                    <ChevronLeft size={18} />
                    {lang === "sv" ? "Tillbaka" : "Back"}
                </button>
                <Link href="/" className="home">{lang === "sv" ? "Översikt" : "Overview"}</Link>
            </div>

            <div className="premium-card" style={{ padding: 22 }}>
                <div style={{ display: "flex", justifyContent: "space-between", gap: 12, flexWrap: "wrap" }}>
                    <div style={{ fontWeight: 900, letterSpacing: "0.04em", color: "var(--accent-primary)" }}>
                        {outage.operator_name}
                    </div>
                    <div style={{ fontFamily: "monospace", fontWeight: 800 }}>
                        {outage.status}
                    </div>
                </div>
                <h1 style={{ marginTop: 10 }}>
                    {typeof outage.title === "string" ? outage.title : (outage.title?.[lang] || outage.title?.sv || outage.title?.en || outage.incident_id)}
                </h1>
                <p style={{ color: "var(--text-secondary)", lineHeight: 1.6 }}>
                    {typeof outage.description === "string" ? outage.description : (outage.description?.[lang] || outage.description?.sv || outage.description?.en || "")}
                </p>
            </div>

            <style jsx>{`
                .back {
                    display: inline-flex;
                    align-items: center;
                    gap: 8px;
                    border: 1px solid var(--border-color);
                    background: transparent;
                    color: var(--text-primary);
                    padding: 10px 14px;
                    border-radius: 10px;
                    font-weight: 900;
                    cursor: pointer;
                }
                .home {
                    color: var(--text-muted);
                    text-decoration: none;
                    font-weight: 900;
                }
            `}</style>
        </div>
    );
}

export default function OutageDetailByQueryPage() {
    return (
        <Suspense fallback={<LoadingState />}>
            <OutageDetailContent />
        </Suspense>
    );
}

