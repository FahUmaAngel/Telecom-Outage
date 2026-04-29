"use client";

import { createContext, useContext, useState, useEffect, useMemo, useCallback } from "react";
import PropTypes from "prop-types";

const LanguageContext = createContext();

export const LanguageProvider = ({ children }) => {
    const [lang, setLang] = useState("sv"); // Default to match server

    useEffect(() => {
        const storedLang = localStorage.getItem("lang");
        if (storedLang && storedLang !== "sv") {
            setLang(storedLang);
        }
    }, []);

    const toggleLanguage = useCallback(() => {
        setLang(prev => {
            const newLang = prev === "sv" ? "en" : "sv";
            localStorage.setItem("lang", newLang);
            return newLang;
        });
    }, []);

    const t = useCallback((bilingualObj) => {
        if (!bilingualObj) return "";
        return bilingualObj[lang] || bilingualObj["sv"] || "";
    }, [lang]);

    const value = useMemo(() => ({ lang, toggleLanguage, t }), [lang, toggleLanguage, t]);

    return (
        <LanguageContext.Provider value={value}>
            {children}
        </LanguageContext.Provider>
    );
};

LanguageProvider.propTypes = {
    children: PropTypes.node.isRequired
};

export const useLanguage = () => {
    const context = useContext(LanguageContext);
    if (!context) {
        throw new Error("useLanguage must be used within a LanguageProvider");
    }
    return context;
};
