"use client";

import { useState, useEffect } from "react";

export default function ScrollToTop() {
    const [isVisible, setIsVisible] = useState(false);

    // Show button when page is scrolled up to 300px
    const toggleVisibility = () => {
        if (window.pageYOffset > 300) {
            setIsVisible(true);
        } else {
            setIsVisible(false);
        }
    };

    // Set the top cordinate to 0
    // make scrolling smooth
    const scrollToTop = () => {
        window.scrollTo({
            top: 0,
            behavior: "smooth",
        });
    };

    useEffect(() => {
        window.addEventListener("scroll", toggleVisibility);
        return () => window.removeEventListener("scroll", toggleVisibility);
    }, []);

    return (
        <div className={`scroll-to-top ${isVisible ? "visible" : ""}`} onClick={scrollToTop}>
            <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
            >
                <path d="M18 15l-6-6-6 6" />
            </svg>

            <style jsx>{`
                .scroll-to-top {
                    position: fixed;
                    bottom: 32px;
                    right: 32px;
                    width: 48px;
                    height: 48px;
                    background: var(--glass-bg);
                    backdrop-filter: blur(12px);
                    -webkit-backdrop-filter: blur(12px);
                    border: 1px solid var(--accent-primary);
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: var(--accent-primary);
                    cursor: pointer;
                    box-shadow: 0 4px 12px rgba(79, 70, 229, 0.15);
                    z-index: 1000;
                    opacity: 0;
                    visibility: hidden;
                    transform: translateY(20px) scale(0.8);
                    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
                }

                .scroll-to-top.visible {
                    opacity: 1;
                    visibility: visible;
                    transform: translateY(0) scale(1);
                }

                .scroll-to-top:hover {
                    background: var(--accent-primary);
                    color: white;
                    transform: translateY(-4px) scale(1.1);
                    box-shadow: 0 8px 24px rgba(79, 70, 229, 0.3);
                }

                .scroll-to-top svg {
                    width: 20px;
                    height: 20px;
                    transition: transform 0.3s ease;
                }

                .scroll-to-top:hover svg {
                    transform: translateY(-2px);
                }

                @media (max-width: 768px) {
                    .scroll-to-top {
                        bottom: 24px;
                        right: 24px;
                        width: 44px;
                        height: 44px;
                    }
                }
            `}</style>
        </div>
    );
}
