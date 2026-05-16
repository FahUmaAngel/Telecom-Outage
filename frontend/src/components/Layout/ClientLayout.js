"use client";

import { useState } from "react";
import Header from "../Header/Header";
import Sidebar from "../Sidebar/Sidebar";
import { ThemeProvider } from "../../context/ThemeContext";
import { LanguageProvider } from "../../context/LanguageContext";
import { ToastProvider } from "../../context/ToastContext";
import ToastContainer from "../Toast/ToastContainer";
import ScrollToTop from "../Common/ScrollToTop";
import PropTypes from "prop-types";

export default function ClientLayout({ children }) {
    const [sidebarOpen, setSidebarOpen] = useState(false);

    return (
        <ThemeProvider>
            <LanguageProvider>
                <ToastProvider>
                    <Header onMenuClick={() => setSidebarOpen(o => !o)} />
                    <div className="layout-container">
                        <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
                        {sidebarOpen && (
                            <button
                                className="sidebar-overlay"
                                aria-label="Close menu"
                                onClick={() => setSidebarOpen(false)}
                            />
                        )}
                        <main className="main-content">
                            {children}
                        </main>
                    </div>
                    <ToastContainer />
                    <ScrollToTop />
                </ToastProvider>
            </LanguageProvider>

            <style jsx>{`
                .layout-container {
                    display: flex;
                    margin-top: var(--header-height);
                }
                .main-content {
                    margin-left: var(--sidebar-width);
                    flex: 1;
                    padding: 40px;
                    min-height: calc(100vh - var(--header-height));
                    max-width: 1600px;
                    width: calc(100% - var(--sidebar-width));
                }
                .sidebar-overlay {
                    display: none;
                }
                @media (max-width: 768px) {
                    .main-content {
                        margin-left: 0;
                        width: 100%;
                        padding: 20px 16px;
                    }
                    .sidebar-overlay {
                        display: block;
                        position: fixed;
                        inset: 0;
                        background: rgba(0, 0, 0, 0.5);
                        z-index: 850;
                    }
                }
            `}</style>
        </ThemeProvider>
    );
}

ClientLayout.propTypes = {
    children: PropTypes.node.isRequired,
};
