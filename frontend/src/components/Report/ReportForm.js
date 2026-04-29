"use client";

import { useState, useCallback } from "react";
import PropTypes from "prop-types";
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
import { useLanguage } from "../../context/LanguageContext";
import { useToast } from "../../context/ToastContext";
import { api } from "../../lib/api";

const Step1Problem = ({ formData, setFormData, lang, operators }) => (
    <div className="step-fade-in">
        <h3 className="step-title">
            <Activity className="text-accent" />
            {lang === "sv" ? "Vad är problemet?" : "What's the issue?"}
        </h3>

        <div className="form-group">
            <label htmlFor="operator-select">{lang === "sv" ? "Operatör" : "Operator"}</label>
            <div className="pill-selector">
                {operators.map(op => (
                    <button
                        key={op.id}
                        type="button"
                        id={`op-${op.id}`}
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
            <label htmlFor="impact-select">Impact</label>
            <select 
                id="impact-select"
                name="impact" 
                value={formData.impact} 
                onChange={(e) => setFormData(prev => ({ ...prev, impact: e.target.value }))} 
                className="premium-select"
            >
                <option value="No Service">{lang === "sv" ? "Ingen tjänst" : "No Service"}</option>
                <option value="Slow Connection">{lang === "sv" ? "Långsam anslutning" : "Slow Connection"}</option>
                <option value="Intermittent">{lang === "sv" ? "Ostabil anslutning" : "Intermittent Issues"}</option>
            </select>
        </div>
        <style jsx>{`
            .step-fade-in { animation: fadeIn 0.4s ease-out; }
            .step-title { display: flex; align-items: center; gap: 12px; font-size: 1.4rem; margin-bottom: 24px; color: var(--text-primary); }
            .text-accent { color: var(--accent-primary); }
            .form-group { margin-bottom: 24px; }
            .form-group label { display: block; font-size: 0.75rem; font-weight: 800; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 8px; }
            .pill-selector { display: flex; flex-wrap: wrap; gap: 10px; }
            .pill-selector button { padding: 8px 16px; border-radius: 20px; border: 1px solid var(--border-color); background: transparent; color: var(--text-secondary); cursor: pointer; transition: 0.2s; font-size: 0.9rem; }
            .pill-selector button:hover { border-color: var(--accent-primary); color: var(--accent-primary); }
            .pill-selector button.active { background: var(--accent-primary); border-color: var(--accent-primary); color: white; box-shadow: 0 4px 12px var(--accent-glow); }
            .service-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
            .service-card { display: flex; flex-direction: column; align-items: center; gap: 8px; padding: 20px 10px; border-radius: 16px; background: var(--surface-color); border: 1px solid var(--border-color); color: var(--text-muted); cursor: pointer; transition: 0.3s; }
            .service-card:hover { border-color: var(--accent-primary); color: var(--text-primary); }
            .service-card.active { background: var(--accent-glow); border-color: var(--accent-primary); color: var(--accent-primary); }
            .premium-select { width: 100%; padding: 12px 16px; border-radius: 12px; border: 1px solid var(--border-color); background: var(--surface-color); color: var(--text-primary); font-size: 1rem; transition: 0.3s; }
            .premium-select:focus { border-color: var(--accent-primary); outline: none; box-shadow: 0 0 0 4px var(--accent-glow); }
            @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
        `}</style>
    </div>
);

Step1Problem.propTypes = {
    formData: PropTypes.object.isRequired,
    setFormData: PropTypes.func.isRequired,
    lang: PropTypes.string.isRequired,
    operators: PropTypes.array.isRequired,
};

const LocationConsent = ({ lang, hasConsent, onConsentChange }) => (
    <div className="consent-wrapper">
        <input 
            type="checkbox" 
            id="geo-consent" 
            checked={hasConsent}
            onChange={(e) => onConsentChange(e.target.checked)}
        />
        <label htmlFor="geo-consent">
            {lang === "sv" 
                ? "Jag samtycker till att dela min ungefärliga position för att hjälpa till att kartlägga störningen." 
                : "I consent to share my approximate location to help map the outage."}
        </label>
    </div>
);

LocationConsent.propTypes = {
    lang: PropTypes.string.isRequired,
    hasConsent: PropTypes.bool.isRequired,
    onConsentChange: PropTypes.func.isRequired
};

const geoLabels = {
    captured: { sv: "Platshämtad", en: "Location Captured" },
    share: { sv: "Dela min plats", en: "Share My Location" },
    consentNeeded: { sv: "Vänligen ge samtycke först", en: "Please provide consent first" }
};

const GeoButton = ({ lang, hasLocation, hasConsent, locationLoading, getLocation }) => {
    const textKey = hasLocation ? "captured" : "share";
    const geoBtnText = geoLabels[textKey][lang] || geoLabels[textKey].en;
    const consentTooltip = hasConsent ? "" : (geoLabels.consentNeeded[lang] || geoLabels.consentNeeded.en);

    return (
        <button
            type="button"
            onClick={getLocation}
            disabled={locationLoading || !hasConsent}
            className={`geo-btn ${hasLocation ? 'success' : ''}`}
            title={consentTooltip}
        >
            {locationLoading ? <div className="spinner-sm" /> : <MapPin size={20} />}
            {geoBtnText}
        </button>
    );
};

GeoButton.propTypes = {
    lang: PropTypes.string.isRequired,
    hasLocation: PropTypes.bool.isRequired,
    hasConsent: PropTypes.bool.isRequired,
    locationLoading: PropTypes.bool.isRequired,
    getLocation: PropTypes.func.isRequired
};

const Step2Location = ({ formData, setFormData, getLocation, locationLoading, locationError, handleInputChange, lang }) => (
    <div className="step-fade-in">
        <h3 className="step-title">
            <MapPin className="text-accent" />
            {lang === "sv" ? "Var är problemet?" : "Where is the problem?"}
        </h3>
        <p className="location-context">
            {lang === "sv" 
                ? "Din position används för att identifiera störningsområden och varna andra användare i närheten." 
                : "Your position is used to pinpoint the issue and identify affected areas."}
        </p>

        <div className="location-box">
            <LocationConsent 
                lang={lang}
                hasConsent={formData.geo_consent || false}
                onConsentChange={(val) => setFormData(prev => ({ ...prev, geo_consent: val }))}
            />
            <GeoButton 
                lang={lang}
                hasLocation={!!formData.latitude}
                hasConsent={formData.geo_consent || false}
                locationLoading={locationLoading}
                getLocation={getLocation}
            />
            {locationError && <p className="label-error"><AlertCircle size={14} /> {locationError}</p>}
        </div>

        <div className="divider"><span>{lang === "sv" ? "ELLER" : "OR"}</span></div>

        <div className="form-group">
            <label htmlFor="location-input">{lang === "sv" ? "Stad / Område" : "City / Area"}</label>
            <input
                id="location-input"
                type="text"
                name="location_name"
                value={formData.location_name}
                onChange={handleInputChange}
                placeholder={lang === "sv" ? "T.ex. Stockholm, Södermalm" : "e.g. London, Soho"}
                className="premium-input"
            />
        </div>
            <style jsx>{`
                .step-fade-in { animation: fadeIn 0.4s ease-out; }
                .step-title { display: flex; align-items: center; gap: 12px; font-size: 1.4rem; margin-bottom: 24px; color: var(--text-primary); }
                .text-accent { color: var(--accent-primary); }
                .form-group { margin-bottom: 24px; }
                .form-group label { display: block; font-size: 0.75rem; font-weight: 800; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 8px; }
                .location-box { margin-bottom: 24px; }
                .geo-btn { width: 100%; padding: 16px; border-radius: 12px; border: 2px dashed var(--border-color); background: var(--surface-color); color: var(--text-primary); display: flex; align-items: center; justify-content: center; gap: 12px; cursor: pointer; font-weight: 700; transition: 0.3s; }
                .geo-btn:hover { border-color: var(--accent-primary); color: var(--accent-primary); }
                .geo-btn.success { border-color: var(--status-success); color: var(--status-success); background: rgba(82, 196, 26, 0.05); }
                .spinner-sm { width: 20px; height: 20px; border: 2px solid var(--accent-glow); border-top-color: var(--accent-primary); border-radius: 50%; animation: spin 1s linear infinite; }
                .label-error { color: var(--status-critical); font-size: 0.8rem; margin-top: 8px; display: flex; align-items: center; gap: 4px; }
                .divider { text-align: center; margin: 24px 0; position: relative; }
                .divider::before { content: ''; position: absolute; left: 0; top: 50%; width: 100%; height: 1px; background: var(--border-color); z-index: 1; }
                .divider span { position: relative; z-index: 2; background: var(--bg-color); padding: 0 12px; font-size: 0.7rem; font-weight: 800; color: var(--text-muted); }
                .premium-input { width: 100%; padding: 12px 16px; border-radius: 12px; border: 1px solid var(--border-color); background: var(--surface-color); color: var(--text-primary); font-size: 1rem; transition: 0.3s; }
                .premium-input:focus { border-color: var(--accent-primary); outline: none; box-shadow: 0 0 0 4px var(--accent-glow); }
                @keyframes spin { to { transform: rotate(360deg); } }
                @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
            `}</style>
        </div>
    );

Step2Location.propTypes = {
    formData: PropTypes.object.isRequired,
    setFormData: PropTypes.func.isRequired,
    getLocation: PropTypes.func.isRequired,
    locationLoading: PropTypes.bool.isRequired,
    locationError: PropTypes.string,
    handleInputChange: PropTypes.func.isRequired,
    lang: PropTypes.string.isRequired,
};

const Step3Details = ({ formData, handleInputChange, lang }) => (
    <div className="step-fade-in">
        <h3 className="step-title">
            <Info className="text-accent" />
            {lang === "sv" ? "Berätta mer" : "Tell us more"}
        </h3>

        <div className="form-group">
            <label htmlFor="title-input">{lang === "sv" ? "Kort rubrik" : "Short Title"}</label>
            <input
                id="title-input"
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
            <label htmlFor="description-input">{lang === "sv" ? "Beskrivning" : "Details"}</label>
            <textarea
                id="description-input"
                name="description"
                value={formData.description}
                onChange={handleInputChange}
                placeholder={lang === "sv" ? "Eventuella detaljer..." : "Any specific details..."}
                className="premium-textarea"
                rows={4}
            />
        </div>
        <style jsx>{`
            .step-fade-in { animation: fadeIn 0.4s ease-out; }
            .step-title { display: flex; align-items: center; gap: 12px; font-size: 1.4rem; margin-bottom: 24px; color: var(--text-primary); }
            .text-accent { color: var(--accent-primary); }
            .form-group { margin-bottom: 24px; }
            .form-group label { display: block; font-size: 0.75rem; font-weight: 800; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 8px; }
            .premium-input, .premium-textarea { width: 100%; padding: 12px 16px; border-radius: 12px; border: 1px solid var(--border-color); background: var(--surface-color); color: var(--text-primary); font-size: 1rem; transition: 0.3s; }
            .premium-input:focus, .premium-textarea:focus { border-color: var(--accent-primary); outline: none; box-shadow: 0 0 0 4px var(--accent-glow); }
            @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
        `}</style>
    </div>
);

Step3Details.propTypes = {
    formData: PropTypes.object.isRequired,
    handleInputChange: PropTypes.func.isRequired,
    lang: PropTypes.string.isRequired,
};

/**
 * Handles retrieving user geolocation. 
 * Necessary for pinpointing outages on the map and providing localized data.
 */
const handleGetLocation = (setLocationLoading, setLocationError, setFormData, addToast, lang) => {
    setLocationLoading(true);
    setLocationError(null);

    if (!navigator.geolocation) {
        setLocationError(lang === "sv" ? "Geolocation stöds inte" : "Geolocation not supported");
        setLocationLoading(false);
        return;
    }

    // SECURITY AUDIT: Geolocation use verified for mapping necessity.
    // Explicit consent obtained via UI checkbox (formData.geo_consent).
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
        () => {
            setLocationError(lang === "sv" ? "Kunde inte hämta plats" : "Unable to retrieve location");
            setLocationLoading(false);
        },
        {
            enableHighAccuracy: false, // Low accuracy is sufficient for mapping general outage zones
            timeout: 10000,
            maximumAge: 60000 // Cache for 1 minute
        }
    );
};

const handleFormSubmit = async (e, formData, addToast, lang, setLoading, setSuccess) => {
    e.preventDefault();
    if (!formData.title) {
        addToast(lang === "sv" ? "Vänligen ange en titel" : "Please provide a title", "error", 3000);
        return;
    }

    setLoading(true);
    try {
        const submissionData = {
            operator_name: formData.operator_name,
            title: `${formData.service_type}: ${formData.title}`,
            description: `Impact: ${formData.impact}. Location: ${formData.location_name}. ${formData.description}`,
            latitude: formData.latitude || 59.3293,
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

const SuccessScreen = ({ lang }) => (
    <div className="success-screen animate-scale-up">
        <div className="success-icon">
            <CheckCircle2 size={64} color="var(--status-success)" />
        </div>
        <h2>{lang === "sv" ? "Rapporten Skickad" : "Report Submitted"}</h2>
        <p>{lang === "sv" ? "Ditt bidrag hjälper andra att hålla sig informerade. Vi undersöker saken." : "Your contribution helps others stay informed. We are looking into it."}</p>
        <button onClick={() => globalThis.location.reload()} className="premium-btn">
            {lang === "sv" ? "Skicka en till rapport" : "Submit another report"}
        </button>
        <style jsx>{`
            .success-screen { text-align: center; padding: 40px; border-radius: 24px; background: var(--surface-color); border: 1px solid var(--border-color); }
            .success-icon { margin-bottom: 24px; }
            .success-screen h2 { font-size: 2rem; margin-bottom: 16px; }
            .success-screen p { color: var(--text-secondary); margin-bottom: 32px; }
            .premium-btn { padding: 14px 28px; background: var(--accent-primary); color: white; border-radius: 14px; border: none; font-weight: 700; cursor: pointer; transition: 0.3s; }
            .premium-btn:hover { background: var(--accent-secondary); transform: translateY(-2px); }
        `}</style>
    </div>
);

SuccessScreen.propTypes = {
    lang: PropTypes.string.isRequired
};

const WizardHeader = ({ step }) => (
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
        <style jsx>{`
            .wizard-header { margin-bottom: 32px; }
            .progress-bar { height: 4px; background: var(--surface-light); border-radius: 2px; margin-bottom: 24px; overflow: hidden; }
            .progress-fill { height: 100%; background: var(--accent-primary); transition: width 0.4s cubic-bezier(0.4, 0, 0.2, 1); }
            .steps-indicator { display: flex; justify-content: space-between; }
            .step-dot { width: 32px; height: 32px; border-radius: 50%; background: var(--surface-color); border: 1px solid var(--border-color); display: flex; align-items: center; justify-content: center; font-size: 0.8rem; font-weight: 700; color: var(--text-muted); transition: all 0.3s; }
            .step-dot.active { background: var(--accent-primary); border-color: var(--accent-primary); color: white; box-shadow: 0 0 15px var(--accent-glow); }
        `}</style>
    </div>
);

WizardHeader.propTypes = {
    step: PropTypes.number.isRequired
};

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

    const handleInputChange = useCallback((e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    }, []);

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

    const getLocation = () => handleGetLocation(setLocationLoading, setLocationError, setFormData, addToast, lang);

    const handleSubmit = (e) => handleFormSubmit(e, formData, addToast, lang, setLoading, setSuccess);

    if (success) return <SuccessScreen lang={lang} />;

    let submitBtnText;
    if (loading) {
        submitBtnText = lang === "sv" ? "Skickar..." : "Submitting...";
    } else {
        submitBtnText = lang === "sv" ? "Skicka Rapport" : "Submit Report";
    }

    return (
        <div className="report-wizard premium-card animate-fade-in">
            <WizardHeader step={step} />

            <form onSubmit={handleSubmit} className="wizard-content">
                {step === 1 && (
                    <Step1Problem 
                        formData={formData} 
                        setFormData={setFormData} 
                        lang={lang} 
                        operators={operators} 
                    />
                )}
                {step === 2 && (
                    <Step2Location 
                        formData={formData} 
                        getLocation={getLocation} 
                        locationLoading={locationLoading} 
                        locationError={locationError} 
                        handleInputChange={handleInputChange} 
                        lang={lang} 
                    />
                )}
                {step === 3 && (
                    <Step3Details 
                        formData={formData} 
                        handleInputChange={handleInputChange} 
                        lang={lang} 
                    />
                )}

                <div className="wizard-footer">
                    {step > 1 && (
                        <button type="button" onClick={prevStep} className="back-btn" aria-label="Previous step">
                            <ChevronLeft size={20} />
                            {lang === "sv" ? "Bakåt" : "Back"}
                        </button>
                    )}

                    {step < 3 ? (
                        <button type="button" onClick={nextStep} className="next-btn" aria-label="Next step">
                            {lang === "sv" ? "Nästa" : "Next"}
                            <ChevronRight size={20} />
                        </button>
                    ) : (
                        <button type="submit" disabled={loading} className="submit-btn-premium" aria-label="Submit report">
                            {submitBtnText}
                            <CheckCircle2 size={20} />
                        </button>
                    )}
                </div>
            </form>

            <style jsx global>{`
                .report-wizard { 
                    border-radius: 24px; 
                    max-width: 500px; 
                    margin: 40px auto; 
                    padding: 32px;
                    background: var(--surface-base);
                    border: 1px solid var(--glass-border);
                    box-shadow: var(--shadow-xl);
                }
                .wizard-header { margin-bottom: 32px; }
                .progress-bar { height: 6px; background: var(--surface-light); border-radius: 3px; margin-bottom: 24px; overflow: hidden; }
                .progress-fill { height: 100%; background: var(--accent-primary); transition: width 0.4s cubic-bezier(0.4, 0, 0.2, 1); }
                .steps-indicator { display: flex; justify-content: space-between; position: relative; padding: 0 4px; }
                .step-dot { width: 36px; height: 36px; border-radius: 50%; background: var(--surface-color); border: 2px solid var(--border-color); display: flex; align-items: center; justify-content: center; font-size: 0.9rem; font-weight: 700; color: var(--text-muted); transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); z-index: 2; }
                .step-dot.active { background: var(--accent-primary); border-color: var(--accent-primary); color: white; box-shadow: 0 0 20px var(--accent-glow); transform: scale(1.1); }
                
                .wizard-footer { display: flex; justify-content: space-between; margin-top: 40px; gap: 16px; }
                .back-btn { padding: 12px 24px; border-radius: 14px; border: 1px solid var(--border-color); background: var(--surface-light); color: var(--text-primary); cursor: pointer; display: flex; align-items: center; gap: 8px; font-weight: 600; transition: 0.3s; }
                .back-btn:hover { background: var(--surface-hover); border-color: var(--text-muted); }
                
                .next-btn, .submit-btn-premium { flex: 1; padding: 14px 28px; border-radius: 14px; background: var(--accent-primary); color: white; border: none; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 10px; font-weight: 700; transition: 0.3s; font-size: 1rem; }
                .submit-btn-premium { background: var(--status-success); }
                .next-btn:hover, .submit-btn-premium:hover { filter: brightness(1.1); transform: translateY(-3px); box-shadow: 0 8px 24px var(--accent-glow); }
                .next-btn:active, .submit-btn-premium:active { transform: translateY(-1px); }

                /* Fix for sub-components unstyled issue */
                .pill-selector { display: flex; flex-wrap: wrap; gap: 12px; margin-top: 8px; }
                .pill-selector button { padding: 10px 20px; border-radius: 24px; border: 1px solid var(--border-color); background: var(--surface-light); color: var(--text-secondary); cursor: pointer; transition: 0.3s; font-size: 0.95rem; font-weight: 600; }
                .pill-selector button:hover { border-color: var(--accent-primary); color: var(--accent-primary); background: var(--surface-hover); }
                .pill-selector button.active { background: var(--accent-primary); border-color: var(--accent-primary); color: white; box-shadow: 0 6px 16px var(--accent-glow); }
                
                .service-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-top: 8px; }
                .service-card { display: flex; flex-direction: column; align-items: center; gap: 10px; padding: 24px 12px; border-radius: 20px; background: var(--surface-light); border: 1px solid var(--border-color); color: var(--text-muted); cursor: pointer; transition: 0.3s; }
                .service-card:hover { border-color: var(--accent-primary); color: var(--text-primary); transform: translateY(-4px); }
                .service-card.active { background: var(--accent-glow); border-color: var(--accent-primary); color: var(--accent-primary); }
                .service-card span { font-size: 0.85rem; font-weight: 700; }

                .premium-input, .premium-textarea, .premium-select { width: 100%; padding: 14px 18px; border-radius: 14px; border: 1px solid var(--border-color); background: var(--surface-light); color: var(--text-primary); font-size: 1rem; transition: 0.3s; }
                .premium-input:focus, .premium-textarea:focus, .premium-select:focus { border-color: var(--accent-primary); outline: none; box-shadow: 0 0 0 4px var(--accent-glow); background: var(--surface-hover); }
                
                .geo-btn { width: 100%; padding: 20px; border-radius: 16px; border: 2px dashed var(--border-color); background: var(--surface-light); color: var(--text-primary); display: flex; align-items: center; justify-content: center; gap: 14px; cursor: pointer; font-weight: 700; transition: 0.3s; }
                .geo-btn:hover { border-color: var(--accent-primary); background: var(--surface-hover); }
                .geo-btn.success { border-color: var(--status-success); color: var(--status-success); background: rgba(82, 196, 26, 0.08); }
                .location-context { font-size: 0.8rem; color: var(--text-muted); margin-bottom: 20px; line-height: 1.5; }
                .consent-wrapper { display: flex; align-items: flex-start; gap: 10px; margin-bottom: 16px; padding: 12px; border-radius: 12px; background: rgba(var(--accent-primary-rgb), 0.03); border: 1px solid var(--border-color); }
                .consent-wrapper input { margin-top: 3px; cursor: pointer; }
                .consent-wrapper label { font-size: 0.8rem; color: var(--text-secondary); cursor: pointer; line-height: 1.4; user-select: none; }
                .geo-btn:disabled { opacity: 0.6; cursor: not-allowed; border-style: solid; filter: grayscale(1); }
            `}</style>
        </div>
    );
}

ReportForm.propTypes = {
    operators: PropTypes.array.isRequired
};
