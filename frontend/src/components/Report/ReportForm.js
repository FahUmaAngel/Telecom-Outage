"use client";

import { useState, useEffect } from "react";
import { useLanguage } from "../../context/LanguageContext";
import { useToast } from "../../context/ToastContext";

export default function ReportForm({ operators }) {
    const { lang } = useLanguage();
    const { addToast } = useToast();

    const [formData, setFormData] = useState({
        operator_name: "",
        title: "",
        description: "",
        latitude: null,
        longitude: null
    });

    const [loading, setLoading] = useState(false);
    const [locationLoading, setLocationLoading] = useState(false);
    const [locationError, setLocationError] = useState(null);

    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    const getLocation = () => {
        setLocationLoading(true);
        setLocationError(null);

        if (!navigator.geolocation) {
            setLocationError(lang === "sv" ? "Geolocation stöds inte av din webbläsare" : "Geolocation is not supported by your browser");
            setLocationLoading(false);
            return;
        }

        navigator.geolocation.getCurrentPosition(
            (position) => {
                setFormData(prev => ({
                    ...prev,
                    latitude: position.coords.latitude,
                    longitude: position.coords.longitude
                }));
                setLocationLoading(false);
                addToast(
                    lang === "sv" ? "Plats hämtad!" : "Location captured!",
                    "success",
                    3000
                );
            },
            (error) => {
                setLocationError(
                    lang === "sv"
                        ? "Kunde inte hämta din plats. Kontrollera dina webbläsarinställningar."
                        : "Unable to retrieve your location. Check your browser settings."
                );
                setLocationLoading(false);
            }
        );
    };

    const handleSubmit = async (e) => {
        e.preventDefault();

        if (!formData.title.trim()) {
            addToast(
                lang === "sv" ? "Vänligen ange en titel" : "Please provide a title",
                "error",
                4000
            );
            return;
        }

        if (!formData.latitude || !formData.longitude) {
            addToast(
                lang === "sv" ? "Vänligen hämta din plats" : "Please capture your location",
                "error",
                4000
            );
            return;
        }

        setLoading(true);

        try {
            const response = await fetch("http://localhost:8000/api/v1/reports", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(formData)
            });

            if (!response.ok) throw new Error("Failed to submit report");

            addToast(
                lang === "sv" ? "Rapport skickad! Tack för ditt bidrag." : "Report submitted! Thank you for your contribution.",
                "success",
                5000
            );

            // Reset form
            setFormData({
                operator_name: "",
                title: "",
                description: "",
                latitude: null,
                longitude: null
            });
        } catch (error) {
            console.error("Error submitting report:", error);
            addToast(
                lang === "sv" ? "Kunde inte skicka rapport. Försök igen." : "Failed to submit report. Please try again.",
                "error",
                5000
            );
        } finally {
            setLoading(false);
        }
    };

    return (
        <form className="report-form" onSubmit={handleSubmit}>
            <div className="form-group">
                <label htmlFor="operator_name">
                    {lang === "sv" ? "Operatör (valfritt)" : "Operator (optional)"}
                </label>
                <select
                    id="operator_name"
                    name="operator_name"
                    value={formData.operator_name}
                    onChange={handleInputChange}
                    className="form-select"
                >
                    <option value="">{lang === "sv" ? "Välj operatör" : "Select operator"}</option>
                    {operators.map(op => (
                        <option key={op.id} value={op.name}>{op.name}</option>
                    ))}
                </select>
            </div>

            <div className="form-group">
                <label htmlFor="title">
                    {lang === "sv" ? "Titel" : "Title"} <span className="required">*</span>
                </label>
                <input
                    type="text"
                    id="title"
                    name="title"
                    value={formData.title}
                    onChange={handleInputChange}
                    placeholder={lang === "sv" ? "T.ex. Inget internet i mitt område" : "e.g. No internet in my area"}
                    className="form-input"
                    required
                />
            </div>

            <div className="form-group">
                <label htmlFor="description">
                    {lang === "sv" ? "Beskrivning (valfritt)" : "Description (optional)"}
                </label>
                <textarea
                    id="description"
                    name="description"
                    value={formData.description}
                    onChange={handleInputChange}
                    placeholder={lang === "sv" ? "Beskriv problemet..." : "Describe the issue..."}
                    className="form-textarea"
                    rows="4"
                />
            </div>

            <div className="form-group">
                <label>
                    {lang === "sv" ? "Plats" : "Location"} <span className="required">*</span>
                </label>
                <button
                    type="button"
                    onClick={getLocation}
                    disabled={locationLoading}
                    className="location-btn"
                >
                    {locationLoading
                        ? (lang === "sv" ? "Hämtar..." : "Fetching...")
                        : (formData.latitude
                            ? (lang === "sv" ? "✓ Plats hämtad" : "✓ Location captured")
                            : (lang === "sv" ? "Använd min plats" : "Use my location")
                        )
                    }
                </button>
                {locationError && <p className="error-text">{locationError}</p>}
                {formData.latitude && (
                    <p className="location-coords">
                        {formData.latitude.toFixed(4)}, {formData.longitude.toFixed(4)}
                    </p>
                )}
            </div>

            <button type="submit" disabled={loading} className="submit-btn">
                {loading
                    ? (lang === "sv" ? "Skickar..." : "Submitting...")
                    : (lang === "sv" ? "Skicka rapport" : "Submit Report")
                }
            </button>

            <style jsx>{`
                .report-form {
                    max-width: 600px;
                    margin: 0 auto;
                }
                .form-group {
                    margin-bottom: 20px;
                }
                label {
                    display: block;
                    margin-bottom: 6px;
                    font-weight: 700;
                    color: var(--text-primary);
                    font-size: 0.85rem;
                    text-transform: uppercase;
                    letter-spacing: 0.05em;
                }
                .required {
                    color: var(--status-critical);
                }
                .form-input,
                .form-select,
                .form-textarea {
                    width: 100%;
                    padding: 10px 14px;
                    border: 1px solid var(--border-color);
                    border-radius: 6px;
                    background: var(--surface-color);
                    color: var(--text-primary);
                    font-family: inherit;
                    font-size: 0.95rem;
                    transition: var(--transition-base);
                }
                .form-input:focus,
                .form-select:focus,
                .form-textarea:focus {
                    outline: none;
                    border-color: var(--accent-primary);
                    box-shadow: 0 0 0 3px var(--accent-glow);
                }
                .form-textarea {
                    resize: vertical;
                    min-height: 100px;
                }
                .location-btn {
                    width: 100%;
                    padding: 10px 14px;
                    background: var(--surface-hover);
                    border: 1px solid var(--border-color);
                    border-radius: 6px;
                    color: var(--text-primary);
                    font-weight: 700;
                    font-size: 0.85rem;
                    text-transform: uppercase;
                    cursor: pointer;
                    transition: var(--transition-base);
                }
                .location-btn:hover:not(:disabled) {
                    border-color: var(--accent-primary);
                    color: var(--accent-primary);
                }
                .location-btn:disabled {
                    opacity: 0.5;
                    cursor: not-allowed;
                }
                .location-coords {
                    margin-top: 6px;
                    font-size: 0.8rem;
                    color: var(--text-muted);
                    font-family: monospace;
                }
                .error-text {
                    margin-top: 6px;
                    color: var(--status-critical);
                    font-size: 0.8rem;
                }
                .submit-btn {
                    width: 100%;
                    padding: 12px 24px;
                    background: var(--accent-primary);
                    color: white;
                    border: none;
                    border-radius: 6px;
                    font-weight: 700;
                    font-size: 0.9rem;
                    text-transform: uppercase;
                    letter-spacing: 0.05em;
                    cursor: pointer;
                    transition: var(--transition-base);
                    margin-top: 12px;
                }
                .submit-btn:hover:not(:disabled) {
                    filter: brightness(1.1);
                    transform: translateY(-1px);
                }
                .submit-btn:disabled {
                    opacity: 0.5;
                    cursor: not-allowed;
                }
            `}</style>
        </form>
    );
}
