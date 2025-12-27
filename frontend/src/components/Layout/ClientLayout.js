"use client";

import Header from "../Header/Header";
import Sidebar from "../Sidebar/Sidebar";
import { ThemeProvider } from "../../context/ThemeContext";
import { LanguageProvider } from "../../context/LanguageContext";
import { ToastProvider } from "../../context/ToastContext";
import ToastContainer from "../Toast/ToastContainer";

export default function ClientLayout({ children }) {
    return (
        <ThemeProvider>
            <LanguageProvider>
                <ToastProvider>
                    <Header />
                    <div className="layout-container">
                        <Sidebar />
                        <main className="main-content">
                            {children}
                        </main>
                    </div>
                    <ToastContainer />
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
      `}</style>
        </ThemeProvider>
    );
}
