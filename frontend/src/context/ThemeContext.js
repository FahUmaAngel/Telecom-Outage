"use client";

import { createContext, useContext, useEffect, useState, useMemo, useCallback } from "react";
import PropTypes from "prop-types";

const ThemeContext = createContext();

export const ThemeProvider = ({ children }) => {
    const [theme, setTheme] = useState("dark"); // Default to match server

    useEffect(() => {
        const storedTheme = localStorage.getItem("theme");
        if (storedTheme && storedTheme !== "dark") {
            setTheme(storedTheme);
        }
    }, []);

    useEffect(() => {
        document.documentElement.dataset.theme = theme;
    }, [theme]);

    const toggleTheme = useCallback(() => {
        setTheme(prev => {
            const newTheme = prev === "light" ? "dark" : "light";
            document.documentElement.dataset.theme = newTheme;
            localStorage.setItem("theme", newTheme);
            return newTheme;
        });
    }, []);

    const value = useMemo(() => ({ theme, toggleTheme }), [theme, toggleTheme]);

    return (
        <ThemeContext.Provider value={value}>
            {children}
        </ThemeContext.Provider>
    );
};

ThemeProvider.propTypes = {
    children: PropTypes.node.isRequired
};

export const useTheme = () => {
    const context = useContext(ThemeContext);
    if (!context) {
        throw new Error("useTheme must be used within a ThemeProvider");
    }
    return context;
};
