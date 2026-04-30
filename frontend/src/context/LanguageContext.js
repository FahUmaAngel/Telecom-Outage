"use client";

import { createContext, useContext, useState, useEffect, useMemo, useCallback } from "react";
import PropTypes from "prop-types";

const LanguageContext = createContext();

export const LanguageProvider = ({ children }) => {
    const [lang, setLang] = useState("sv");

    useEffect(() => {
        const stored = localStorage.getItem("lang");
        if (stored && stored !== lang) {
            setTimeout(() => setLang(stored), 0);
        }
    // eslint-disable-next-line react-hooks/exhaustive-deps
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

    const contextValue = useMemo(() => ({ 
        lang, 
        toggleLanguage, 
        t 
    }), [lang, toggleLanguage, t]);

    return (
        <LanguageContext.Provider value={contextValue}>
            {children}
        </LanguageContext.Provider>
    );
};

LanguageProvider.propTypes = {
    children: PropTypes.node.isRequired,
};

export const useLanguage = () => useContext(LanguageContext);
