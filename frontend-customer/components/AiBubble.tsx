import React, { useState, useRef, useEffect, useCallback } from 'react';

const API = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

interface Message {
    id: string;
    role: 'bot' | 'user';
    text: string;
}

export default function AiBubble() {
    const [panelOpen, setPanelOpen] = useState(false);
    const [messages, setMessages] = useState<Message[]>([
        { id: 'init', role: 'bot', text: 'Namaste! 🫐 I am your Blueberry concierge. Ready to plan your Himalayan escape?' }
    ]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const sendMessage = async () => {
        const text = input.trim();
        if (!text || loading) return;
        setMessages(prev => [...prev, { id: Date.now().toString(), role: 'user', text }]);
        setInput('');
        setLoading(true);
        try {
            const res = await fetch(`${API}/api/v1/assistant/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: text }),
            });
            const data = await res.json();
            setMessages(prev => [...prev, { id: Date.now().toString(), role: 'bot', text: data.message }]);
        } catch {
            setMessages(prev => [...prev, { id: 'err', role: 'bot', text: 'I hit a mountain peak! Try again.' }]);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="ai-bubble-container">
            {!panelOpen ? (
                <button className="ai-btn" onClick={() => setPanelOpen(true)}>
                    <span>✨</span>
                </button>
            ) : (
                <div className="ai-panel glass-dark">
                    <div className="ai-header">
                        <h3>Blueberry AI</h3>
                        <button onClick={() => setPanelOpen(false)}>✕</button>
                    </div>
                    <div className="ai-chat">
                        {messages.map(m => (
                            <div key={m.id} className={`ai-message ${m.role}`}>
                                {m.text}
                            </div>
                        ))}
                        {loading && <div className="ai-message bot loading">...</div>}
                    </div>
                    <div className="ai-input-row">
                        <input 
                            value={input} 
                            onChange={e => setInput(e.target.value)}
                            onKeyDown={e => e.key === 'Enter' && sendMessage()}
                            placeholder="Ask me anything..."
                        />
                        <button onClick={sendMessage}>Send</button>
                    </div>
                </div>
            )}

            <style jsx>{`
                .ai-panel {
                    position: fixed;
                    bottom: 110px;
                    right: 32px;
                    width: 380px;
                    height: 540px;
                    background: rgba(10, 10, 12, 0.9);
                    backdrop-filter: blur(32px);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 32px;
                    display: flex;
                    flex-direction: column;
                    z-index: 2001;
                    animation: slideUp 0.5s cubic-bezier(0.4, 0, 0.2, 1);
                    box-shadow: 0 40px 80px rgba(0,0,0,0.4);
                    overflow: hidden;
                }
                @keyframes slideUp {
                    from { opacity: 0; transform: translateY(30px); }
                    to { opacity: 1; transform: translateY(0); }
                }
                .ai-header {
                    padding: 28px;
                    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    background: rgba(76, 124, 53, 0.1);
                }
                .ai-header h3 { font-size: 18px; font-weight: 800; color: white; margin: 0; letter-spacing: -0.02em; }
                .ai-header button { background: none; border: none; color: rgba(255,255,255,0.4); cursor: pointer; font-size: 18px; transition: color 0.2s; }
                .ai-header button:hover { color: white; }
                
                .ai-chat {
                    flex: 1;
                    overflow-y: auto;
                    padding: 28px;
                    display: flex;
                    flex-direction: column;
                    gap: 16px;
                }
                .ai-chat::-webkit-scrollbar { width: 6px; }
                .ai-chat::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.05); border-radius: 10px; }
                
                .ai-message {
                    padding: 14px 18px;
                    border-radius: 20px;
                    max-width: 85%;
                    font-size: 14px;
                    line-height: 1.5;
                }
                .ai-message.bot {
                    background: rgba(255, 255, 255, 0.05);
                    color: rgba(255,255,255,0.9);
                    align-self: flex-start;
                    border-bottom-left-radius: 4px;
                    border: 1px solid rgba(255,255,255,0.05);
                }
                .ai-message.user {
                    background: var(--primary);
                    color: white;
                    align-self: flex-end;
                    border-bottom-right-radius: 4px;
                    box-shadow: 0 4px 15px rgba(76, 124, 53, 0.3);
                    font-weight: 600;
                }
                .ai-input-row {
                    padding: 24px;
                    display: flex;
                    gap: 12px;
                    border-top: 1px solid rgba(255, 255, 255, 0.08);
                    background: rgba(0,0,0,0.2);
                }
                .ai-input-row input {
                    flex: 1;
                    background: rgba(255, 255, 255, 0.05);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 14px;
                    padding: 12px 18px;
                    color: white;
                    outline: none;
                    font-size: 14px;
                    transition: all 0.2s;
                }
                .ai-input-row input:focus { border-color: var(--primary-light); background: rgba(255,255,255,0.08); }
                .ai-input-row button {
                    background: var(--primary);
                    color: white;
                    border: none;
                    border-radius: 14px;
                    padding: 0 20px;
                    font-weight: 800;
                    cursor: pointer;
                    text-transform: uppercase;
                    font-size: 12px;
                    letter-spacing: 0.05em;
                    transition: all 0.2s;
                }
                .ai-input-row button:hover { background: var(--primary-light); transform: translateY(-1px); }
            `}</style>
        </div>
    );
}
