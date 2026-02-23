import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { GeminiChatService } from '../services/chatService';

interface Message {
    id: string;
    role: 'user' | 'model';
    text: string;
}

export const ChatWidget: React.FC = () => {
    const [isOpen, setIsOpen] = useState(false);
    const [messages, setMessages] = useState<Message[]>([
        { id: '1', role: 'model', text: 'Hi! I\'m Sophie. Ask me anything about our AI receptionist services.' }
    ]);
    const [inputValue, setInputValue] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const chatServiceRef = useRef<GeminiChatService | null>(null);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        chatServiceRef.current = new GeminiChatService();
    }, []);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages, isOpen]);

    const handleSendMessage = async (e?: React.FormEvent) => {
        e?.preventDefault();
        if (!inputValue.trim() || isLoading) return;

        const userMsg: Message = {
            id: Date.now().toString(),
            role: 'user',
            text: inputValue.trim()
        };

        setMessages(prev => [...prev, userMsg]);
        setInputValue('');
        setIsLoading(true);

        try {
            const history = messages.map(m => ({ role: m.role, text: m.text }));
            const responseText = await chatServiceRef.current?.sendMessage(history, userMsg.text);

            const botMsg: Message = {
                id: (Date.now() + 1).toString(),
                role: 'model',
                text: responseText || "I'm sorry, I couldn't process that."
            };

            setMessages(prev => [...prev, botMsg]);
        } catch (error) {
            console.error(error);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <>
            <AnimatePresence>
                {isOpen && (
                    <motion.div
                        initial={{ opacity: 0, scale: 0.9, y: 20 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.9, y: 20 }}
                        className="fixed bottom-24 right-6 w-[90vw] max-w-[350px] md:max-w-[380px] h-[500px] bg-offwhite border border-dark shadow-[8px_8px_0px_#111111] flex flex-col z-[10000] pointer-events-auto font-sans"
                    >
                        {/* Header */}
                        <div className="bg-dark p-4 flex items-center justify-between text-paper shrink-0 border-b border-dark">
                            <div className="flex items-center gap-3">
                                <div className="w-8 h-8 bg-signal border border-dark flex items-center justify-center relative">
                                    <span className="text-paper font-heading font-bold text-sm">S</span>
                                    <span className="absolute -bottom-1 -right-1 w-2.5 h-2.5 bg-signal border border-dark animate-pulse"></span>
                                </div>
                                <div>
                                    <div className="font-mono font-bold text-sm uppercase tracking-widest">Sophie</div>
                                    <div className="font-sans text-[10px] text-paper/70 tracking-tight">AI Agent</div>
                                </div>
                            </div>
                            <button
                                onClick={() => setIsOpen(false)}
                                className="text-paper/70 hover:text-signal transition-transform hover:rotate-90 group"
                            >
                                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                                    <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                                </svg>
                            </button>
                        </div>

                        {/* Messages */}
                        <div className="flex-1 bg-paper overflow-y-auto p-4 space-y-4 relative">
                            <div className="hiw-noise opacity-30 pointer-events-none absolute inset-0 z-0"></div>
                            {messages.map((msg) => (
                                <div
                                    key={msg.id}
                                    className={`flex relative z-10 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                                >
                                    <div
                                        className={`max-w-[85%] p-3 font-sans text-sm leading-relaxed border ${msg.role === 'user'
                                            ? 'bg-dark text-paper border-dark shadow-[3px_3px_0px_#E63B2E]'
                                            : 'bg-offwhite border-dark text-dark shadow-[3px_3px_0px_#111111]'
                                            }`}
                                    >
                                        {msg.text}
                                    </div>
                                </div>
                            ))}
                            {isLoading && (
                                <div className="flex justify-start relative z-10">
                                    <div className="bg-offwhite border border-dark px-4 py-3 shadow-[3px_3px_0px_#111111] flex gap-1.5 items-center justify-center min-h-[42px]">
                                        <span className="w-1.5 h-1.5 bg-signal border border-dark animate-bounce"></span>
                                        <span className="w-1.5 h-1.5 bg-signal border border-dark animate-bounce delay-100"></span>
                                        <span className="w-1.5 h-1.5 bg-signal border border-dark animate-bounce delay-200"></span>
                                    </div>
                                </div>
                            )}
                            <div ref={messagesEndRef} className="h-px" />
                        </div>

                        {/* Input */}
                        <form onSubmit={handleSendMessage} className="p-4 bg-paper border-t border-dark shrink-0 relative z-10">
                            <div className="relative flex items-center">
                                <input
                                    type="text"
                                    placeholder="Ask a question..."
                                    className="w-full pl-4 pr-12 py-3 bg-offwhite border border-dark focus:outline-none focus:ring-1 focus:ring-dark transition-all text-sm font-sans text-dark placeholder-dark/40"
                                    value={inputValue}
                                    onChange={(e) => setInputValue(e.target.value)}
                                />
                                <button
                                    type="submit"
                                    disabled={!inputValue.trim() || isLoading}
                                    className="absolute right-2 p-2 bg-dark text-paper border border-dark disabled:opacity-50 disabled:cursor-not-allowed hover:bg-signal transition-all shadow-[2px_2px_0px_#111111] active:translate-y-[2px] active:translate-x-[2px] active:shadow-none"
                                >
                                    <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                                        <path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z" />
                                    </svg>
                                </button>
                            </div>
                        </form>
                    </motion.div>
                )}
            </AnimatePresence>

            <button
                onClick={() => setIsOpen(!isOpen)}
                className="fixed bottom-6 right-6 w-14 h-14 bg-dark text-paper border border-dark shadow-[4px_4px_0px_#111111] flex items-center justify-center z-[10000] pointer-events-auto hover:bg-signal transition-transform hover:scale-105 active:scale-95 group"
            >
                {isOpen ? (
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 group-hover:rotate-90 transition-transform duration-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                ) : (
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                    </svg>
                )}
                {/* Notification Dot */}
                {!isOpen && (
                    <span className="absolute -top-1 -right-1 w-3 h-3 bg-signal border border-dark animate-pulse"></span>
                )}
            </button>
        </>
    );
};
