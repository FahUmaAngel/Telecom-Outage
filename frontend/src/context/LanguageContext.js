"use client";

import { createContext, useContext, useState, useEffect } from "react";

const LanguageContext = createContext();

export const LanguageProvider = ({ children }) => {
    const [lang, setLang] = useState("sv"); // Default to match server

    useEffect(() => {
        const storedLang = localStorage.getItem("lang");
        if (storedLang && storedLang !== "sv") {
            setLang(storedLang);
        }
    }, []);

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
