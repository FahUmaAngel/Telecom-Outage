"use client";

import { createContext, useContext, useState } from "react";

const LanguageContext = createContext();

const getInitialLanguage = () => {
    if (typeof window === "undefined") {
        return "sv";
    }
    return localStorage.getItem("lang") || "sv";
};

export const LanguageProvider = ({ children }) => {
    const [lang, setLang] = useState(getInitialLanguage);

    const toggleLanguage = () => {
        const newLang = lang === "sv" ? "en" : "sv";
        setLang(newLang);
        localStorage.setItem("lang", newLang);
    };

    const t = (bilingualObj) => {
        if (!bilingualObj) return "";
        return bilingualObj[lang] || bilingualObj["sv"] || "";
    };

    return (
        <LanguageContext.Provider value={{ lang, toggleLanguage, t }}>
            {children}
        </LanguageContext.Provider>
    );
};

export const useLanguage = () => useContext(LanguageContext);
