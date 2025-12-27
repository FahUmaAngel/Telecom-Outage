"use client";

import { useToast } from '../../context/ToastContext';

export default function ToastContainer() {
    const { toasts, removeToast } = useToast();

    return (
        <div className="toast-container">
            {toasts.map(toast => (
                <div
                    key={toast.id}
                    className={`toast toast-${toast.type} animate-slide-in`}
                    onClick={() => removeToast(toast.id)}
                >
                    <div className="toast-icon">
                        {toast.type === 'success' && '✓'}
                        {toast.type === 'error' && '✕'}
                        {toast.type === 'warning' && '⚠'}
                        {toast.type === 'info' && 'ℹ'}
                    </div>
                    <div className="toast-message">{toast.message}</div>
                    <button
                        className="toast-close"
                        onClick={(e) => {
                            e.stopPropagation();
                            removeToast(toast.id);
                        }}
                    >
                        ✕
                    </button>
                </div>
            ))}

            <style jsx>{`
                .toast-container {
                    position: fixed;
                    top: 80px;
                    right: 20px;
                    z-index: 9999;
                    display: flex;
                    flex-direction: column;
                    gap: 12px;
                    pointer-events: none;
                }

                .toast {
                    pointer-events: auto;
                    min-width: 300px;
                    max-width: 400px;
                    padding: 16px 20px;
                    border-radius: 12px;
                    display: flex;
                    align-items: center;
                    gap: 12px;
                    cursor: pointer;
                    backdrop-filter: blur(10px);
                    border: 1px solid var(--glass-border);
                    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
                    transition: transform 0.2s ease, opacity 0.2s ease;
                }

                .toast:hover {
                    transform: translateX(-5px);
                }

                .toast-success {
                    background: rgba(82, 196, 26, 0.15);
                    border-color: rgba(82, 196, 26, 0.3);
                }

                .toast-error {
                    background: rgba(255, 77, 79, 0.15);
                    border-color: rgba(255, 77, 79, 0.3);
                }

                .toast-warning {
                    background: rgba(250, 173, 20, 0.15);
                    border-color: rgba(250, 173, 20, 0.3);
                }

                .toast-info {
                    background: rgba(24, 144, 255, 0.15);
                    border-color: rgba(24, 144, 255, 0.3);
                }

                .toast-icon {
                    font-size: 1.2rem;
                    font-weight: bold;
                    flex-shrink: 0;
                }

                .toast-success .toast-icon { color: #52c41a; }
                .toast-error .toast-icon { color: #ff4d4f; }
                .toast-warning .toast-icon { color: #faad14; }
                .toast-info .toast-icon { color: #1890ff; }

                .toast-message {
                    flex: 1;
                    color: var(--text-primary);
                    font-size: 0.9rem;
                    line-height: 1.4;
                }

                .toast-close {
                    background: none;
                    border: none;
                    color: var(--text-muted);
                    cursor: pointer;
                    font-size: 1.2rem;
                    padding: 0;
                    width: 24px;
                    height: 24px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    border-radius: 4px;
                    transition: background 0.2s ease;
                }

                .toast-close:hover {
                    background: rgba(255, 255, 255, 0.1);
                }

                @keyframes slideIn {
                    from {
                        transform: translateX(400px);
                        opacity: 0;
                    }
                    to {
                        transform: translateX(0);
                        opacity: 1;
                    }
                }

                .animate-slide-in {
                    animation: slideIn 0.3s ease-out;
                }

                @media (max-width: 768px) {
                    .toast-container {
                        top: 70px;
                        right: 10px;
                        left: 10px;
                    }

                    .toast {
                        min-width: auto;
                        max-width: none;
                    }
                }
            `}</style>
        </div>
    );
}
