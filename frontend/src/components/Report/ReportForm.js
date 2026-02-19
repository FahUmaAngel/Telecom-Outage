"use client";

import { useState, useEffect } from "react";
import { useLanguage } from "../../context/LanguageContext";
import { useToast } from "../../context/ToastContext";
import { api } from "../../lib/api";
import {
    Wifi,
    Smartphone,
    Home,
    MapPin,
    Info,
    CheckCircle2,
    ChevronRight,
    ChevronLeft,
    AlertCircle,
    Activity
} from "lucide-react";

export default function ReportForm({ operators }) {
    const { lang } = useLanguage();
    const { addToast } = useToast();
    const [step, setStep] = useState(1);
    const [loading, setLoading] = useState(false);
    const [locationLoading, setLocationLoading] = useState(false);
    const [locationError, setLocationError] = useState(null);
    const [success, setSuccess] = useState(false);

    const [formData, setFormData] = useState({
        operator_name: "",
        service_type: "Mobile",
        impact: "No Service",
        location_name: "",
        title: "",
        description: "",
        latitude: null,
        longitude: null
    });

    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    const nextStep = () => {
        if (step === 1 && !formData.operator_name) {
            addToast(lang === "sv" ? "Vänligen välj en operatör" : "Please select an operator", "warning", 3000);
            return;
        }
        if (step === 2 && !formData.latitude && !formData.location_name) {
            addToast(lang === "sv" ? "Vänligen ange en plats" : "Please provide a location", "warning", 3000);
            return;
        }
        setStep(prev => prev + 1);
    };

    const prevStep = () => setStep(prev => prev - 1);

    const getLocation = () => {
        setLocationLoading(true);
        setLocationError(null);

        if (!navigator.geolocation) {
            setLocationError(lang === "sv" ? "Geolocation stöds inte" : "Geolocation not supported");
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
                addToast(lang === "sv" ? "Plats hämtad!" : "Location captured!", "success", 2000);
            },
            (error) => {
                setLocationError(lang === "sv" ? "Kunde inte hämta plats" : "Unable to retrieve location");
                setLocationLoading(false);
            }
        );
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!formData.title) {
            addToast(lang === "sv" ? "Vänligen ange en titel" : "Please provide a title", "error", 3000);
            return;
        }

        setLoading(true);
        try {
            // Prepare data for backend (ensuring it matches expected schema)
            const submissionData = {
                operator_name: formData.operator_name,
                title: `${formData.service_type}: ${formData.title}`,
                description: `Impact: ${formData.impact}. Location: ${formData.location_name}. ${formData.description}`,
                latitude: formData.latitude || 59.3293, // Fallback to Stockholm if missing but title provided
                longitude: formData.longitude || 18.0686
            };

            await api.reports.create(submissionData);
            setSuccess(true);
            addToast(lang === "sv" ? "Tack för din rapport!" : "Thank you for your report!", "success", 5000);
        } catch (error) {
            console.error("Submission error:", error);
            addToast(lang === "sv" ? "Kunde inte skicka rapporten" : "Failed to submit report", "error", 5000);
        } finally {
            setLoading(false);
        }
    };

    if (success) {
        return (
            <div className="success-screen glass animate-scale-up">
                <div className="success-icon">
                    <CheckCircle2 size={64} color="var(--status-success)" />
                </div>
                <h2>{lang === "sv" ? "Rapporten Skickad" : "Report Submitted"}</h2>
                <p>{lang === "sv" ? "Ditt bidrag hjälper andra att hålla sig informerade. Vi undersöker saken." : "Your contribution helps others stay informed. We are looking into it."}</p>
                <button onClick={() => window.location.reload()} className="premium-btn">
                    {lang === "sv" ? "Skicka en till rapport" : "Submit another report"}
                </button>
            </div>
        );
    }

    return (
        <div className="report-wizard glass">
            {/* Progress Header */}
            <div className="wizard-header">
                <div className="progress-bar">
                    <div className="progress-fill" style={{ width: `${(step / 3) * 100}%` }}></div>
                </div>
                <div className="steps-indicator">
                    {[1, 2, 3].map(s => (
                        <div key={s} className={`step-dot ${step >= s ? 'active' : ''}`}>
                            {step > s ? <CheckCircle2 size={16} /> : s}
                        </div>
                    ))}
                </div>
            </div>

            <form onSubmit={handleSubmit} className="wizard-content">
                {step === 1 && (
                    <div className="step-fade-in">
                        <h3 className="step-title">
                            <Activity className="text-accent" />
                            {lang === "sv" ? "Vad är problemet?" : "What's the issue?"}
                        </h3>

                        <div className="form-group">
                            <label>{lang === "sv" ? "Operatör" : "Operator"}</label>
                            <div className="pill-selector">
                                {operators.map(op => (
                                    <button
                                        key={op.id}
                                        type="button"
                                        className={formData.operator_name === op.name ? "active" : ""}
                                        onClick={() => setFormData(prev => ({ ...prev, operator_name: op.name }))}
                                    >
                                        {op.name}
                                    </button>
                                ))}
                            </div>
                        </div>

                        <div className="form-group">
                            <label>{lang === "sv" ? "Tjänst" : "Service"}</label>
                            <div className="service-grid">
                                {[
                                    { id: 'Mobile', icon: Smartphone, label: lang === "sv" ? "Mobil" : "Mobile" },
                                    { id: 'Fiber', icon: Wifi, label: "Fiber" },
                                    { id: 'Home', icon: Home, label: lang === "sv" ? "Hem" : "Home" }
                                ].map(item => (
                                    <button
                                        key={item.id}
                                        type="button"
                                        className={`service-card ${formData.service_type === item.id ? 'active' : ''}`}
                                        onClick={() => setFormData(prev => ({ ...prev, service_type: item.id }))}
                                    >
                                        <item.icon size={24} />
                                        <span>{item.label}</span>
                                    </button>
                                ))}
                            </div>
                        </div>

                        <div className="form-group">
                            <label>{lang === "sv" ? "Impact" : "Impact"}</label>
                            <select name="impact" value={formData.impact} onChange={handleInputChange} className="premium-select">
                                <option value="No Service">{lang === "sv" ? "Ingen tjänst" : "No Service"}</option>
                                <option value="Slow Connection">{lang === "sv" ? "Långsam anslutning" : "Slow Connection"}</option>
                                <option value="Intermittent">{lang === "sv" ? "Ostabil anslutning" : "Intermittent Issues"}</option>
                            </select>
                        </div>
                    </div>
                )}

                {step === 2 && (
                    <div className="step-fade-in">
                        <h3 className="step-title">
                            <MapPin className="text-accent" />
                            {lang === "sv" ? "Var är du?" : "Where are you?"}
                        </h3>

                        <div className="location-box glass">
                            <button
                                type="button"
                                onClick={getLocation}
                                disabled={locationLoading}
                                className={`geo-btn ${formData.latitude ? 'success' : ''}`}
                            >
                                {locationLoading ? <div className="spinner-sm" /> : <MapPin size={20} />}
                                {formData.latitude ? (lang === "sv" ? "Platshämtad" : "Location Captured") : (lang === "sv" ? "Dela min plats" : "Share My Location")}
                            </button>
                            {locationError && <p className="label-error"><AlertCircle size={14} /> {locationError}</p>}
                        </div>

                        <div className="divider"><span>{lang === "sv" ? "ELLER" : "OR"}</span></div>

                        <div className="form-group">
                            <label>{lang === "sv" ? "Stad / Område" : "City / Area"}</label>
                            <input
                                type="text"
                                name="location_name"
                                value={formData.location_name}
                                onChange={handleInputChange}
                                placeholder={lang === "sv" ? "T.ex. Stockholm, Södermalm" : "e.g. London, Soho"}
                                className="premium-input"
                            />
                        </div>
                    </div>
                )}

                {step === 3 && (
                    <div className="step-fade-in">
                        <h3 className="step-title">
                            <Info className="text-accent" />
                            {lang === "sv" ? "Berätta mer" : "Tell us more"}
                        </h3>

                        <div className="form-group">
                            <label>{lang === "sv" ? "Kort rubrik" : "Short Title"}</label>
                            <input
                                type="text"
                                name="title"
                                value={formData.title}
                                onChange={handleInputChange}
                                placeholder={lang === "sv" ? "T.ex. Inget internet sedan kl 10" : "e.g. No internet since 10 AM"}
                                className="premium-input"
                                required
                            />
                        </div>

                        <div className="form-group">
                            <label>{lang === "sv" ? "Beskrivning" : "Details"}</label>
                            <textarea
                                name="description"
                                value={formData.description}
                                onChange={handleInputChange}
                                placeholder={lang === "sv" ? "Eventuella detaljer..." : "Any specific details..."}
                                className="premium-textarea"
                                rows={4}
                            />
                        </div>
                    </div>
                )}

                <div className="wizard-footer">
                    {step > 1 && (
                        <button type="button" onClick={prevStep} className="back-btn">
                            <ChevronLeft size={20} />
                            {lang === "sv" ? "Bakåt" : "Back"}
                        </button>
                    )}

                    {step < 3 ? (
                        <button type="button" onClick={nextStep} className="next-btn">
                            {lang === "sv" ? "Nästa" : "Next"}
                            <ChevronRight size={20} />
                        </button>
                    ) : (
                        <button type="submit" disabled={loading} className="submit-btn-premium">
                            {loading ? (lang === "sv" ? "Skickar..." : "Submitting...") : (lang === "sv" ? "Skicka Rapport" : "Submit Report")}
                            <CheckCircle2 size={20} />
                        </button>
                    )}
                </div>
            </form>

            <style jsx>{`
                .report-wizard {
                    padding: 32px;
                    border-radius: 24px;
                    max-width: 500px;
                    margin: 0 auto;
                }
                .wizard-header { margin-bottom: 32px; }
                .progress-bar { 
                    height: 4px; 
                    background: var(--surface-light); 
                    border-radius: 2px; 
                    margin-bottom: 24px;
                    overflow: hidden;
                }
                .progress-fill { 
                    height: 100%; 
                    background: var(--accent-primary); 
                    transition: width 0.4s cubic-bezier(0.4, 0, 0.2, 1);
                }
                .steps-indicator { display: flex; justify-content: space-between; }
                .step-dot {
                    width: 32px;
                    height: 32px;
                    border-radius: 50%;
                    background: var(--surface-color);
                    border: 1px solid var(--border-color);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 0.8rem;
                    font-weight: 700;
                    color: var(--text-muted);
                    transition: all 0.3s;
                }
                .step-dot.active {
                    background: var(--accent-primary);
                    border-color: var(--accent-primary);
                    color: white;
                    box-shadow: 0 0 15px var(--accent-glow);
                }

                .step-title {
                    display: flex;
                    align-items: center;
                    gap: 12px;
                    font-size: 1.4rem;
                    margin-bottom: 24px;
                    color: var(--text-primary);
                }
                .text-accent { color: var(--accent-primary); }

                .pill-selector { display: flex; flex-wrap: wrap; gap: 10px; }
                .pill-selector button {
                    padding: 8px 16px;
                    border-radius: 20px;
                    border: 1px solid var(--border-color);
                    background: transparent;
                    color: var(--text-secondary);
                    cursor: pointer;
                    transition: 0.2s;
                    font-size: 0.9rem;
                }
                .pill-selector button.active {
                    background: var(--accent-primary);
                    border-color: var(--accent-primary);
                    color: white;
                }

                .service-grid {
                    display: grid;
                    grid-template-columns: repeat(3, 1fr);
                    gap: 12px;
                }
                .service-card {
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    gap: 8px;
                    padding: 20px 10px;
                    border-radius: 16px;
                    background: var(--surface-color);
                    border: 1px solid var(--border-color);
                    color: var(--text-muted);
                    cursor: pointer;
                    transition: 0.3s;
                }
                .service-card.active {
                    background: var(--accent-glow);
                    border-color: var(--accent-primary);
                    color: var(--accent-primary);
                }

                .geo-btn {
                    width: 100%;
                    padding: 16px;
                    border-radius: 12px;
                    border: 2px dashed var(--border-color);
                    background: transparent;
                    color: var(--text-primary);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    gap: 12px;
                    cursor: pointer;
                    font-weight: 700;
                    transition: 0.3s;
                }
                .geo-btn:hover { border-color: var(--accent-primary); color: var(--accent-primary); }
                .geo-btn.success { border-color: var(--status-success); color: var(--status-success); background: rgba(82, 196, 26, 0.05); }

                .divider { text-align: center; margin: 24px 0; position: relative; }
                .divider::before { content: ''; position: absolute; left: 0; top: 50%; width: 100%; height: 1px; background: var(--border-color); z-index: 1; }
                .divider span { position: relative; z-index: 2; background: var(--bg-color); padding: 0 12px; font-size: 0.7rem; font-weight: 800; color: var(--text-muted); }

                .premium-input, .premium-select, .premium-textarea {
                    width: 100%;
                    padding: 12px 16px;
                    border-radius: 12px;
                    border: 1px solid var(--border-color);
                    background: var(--surface-color);
                    color: var(--text-primary);
                    font-size: 1rem;
                    transition: 0.3s;
                }
                .premium-input:focus { border-color: var(--accent-primary); outline: none; box-shadow: 0 0 0 4px var(--accent-glow); }

                .wizard-footer {
                    display: flex;
                    justify-content: space-between;
                    margin-top: 40px;
                    gap: 12px;
                }
                .back-btn {
                    padding: 12px 20px;
                    border-radius: 12px;
                    border: 1px solid var(--border-color);
                    background: transparent;
                    color: var(--text-secondary);
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    gap: 8px;
                }
                .next-btn, .submit-btn-premium {
                    flex: 1;
                    padding: 12px 24px;
                    border-radius: 12px;
                    background: var(--accent-primary);
                    color: white;
                    border: none;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    gap: 8px;
                    font-weight: 700;
                    transition: 0.3s;
                }
                .submit-btn-premium { background: var(--status-success); }
                .next-btn:hover, .submit-btn-premium:hover { filter: brightness(1.1); transform: translateY(-2px); }

                .success-screen {
                    text-align: center;
                    padding: 60px 40px;
                    border-radius: 32px;
                }
                .success-icon { margin-bottom: 24px; }
                .success-screen h2 { font-size: 2rem; margin-bottom: 16px; }
                .success-screen p { color: var(--text-secondary); margin-bottom: 32px; }
                .premium-btn {
                    padding: 14px 28px;
                    background: var(--accent-primary);
                    color: white;
                    border-radius: 14px;
                    border: none;
                    font-weight: 700;
                    cursor: pointer;
                }

                .step-fade-in {
                    animation: fadeIn 0.4s ease-out;
                }
                @keyframes fadeIn {
                    from { opacity: 0; transform: translateY(10px); }
                    to { opacity: 1; transform: translateY(0); }
                }
            `}</style>
        </div>
    );
}
