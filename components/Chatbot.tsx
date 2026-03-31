'use client';

import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { MessageSquare, X, Send, Sparkles, User, Loader2 } from 'lucide-react';
import { useChat } from '@/contexts/ChatContext';

interface Message {
  role: 'user' | 'assistant' | 'error';
  content: string;
}

const Chatbot: React.FC = () => {
  const { isChatOpen: isOpen, setChatOpen: setIsOpen } = useChat();
  const [isClosing, setIsClosing] = useState(false);
  const [isFullScreen, setIsFullScreen] = useState(true); // Always fullscreen by default
  const [dontShowAgain, setDontShowAgain] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isStreaming]);

  // Check for first visit and auto-open (DISABLED as per user request)
  useEffect(() => {
    // Disabled auto-open logic
    /*
    const hasBeenDismissed = localStorage.getItem('chatbot_dismissed');
    if (!hasBeenDismissed) {
      const timer = setTimeout(() => {
        setIsOpen(true);
      }, 3500);
      return () => clearTimeout(timer);
    }
    */
  }, []);

  // Update animating state when isOpen changes
  useEffect(() => {
    if (isOpen) {
      setIsClosing(false);
    }
  }, [isOpen]);

  // Auto-greeting when opened for the first time
  useEffect(() => {
    if (isOpen && messages.length === 0 && !isStreaming) {
      const timer = setTimeout(() => {
        const greeting = "Xin chào Quý khách! em là trợ lý ảo của Sàn Dịch Vụ 24/7. Em có thể giúp gì cho Quý khách trong việc tìm kiếm các dịch vụ vận tải, sửa chữa, hay chăm sóc gia đình ngay lúc này không ạ?";
        setMessages([{ role: 'assistant', content: greeting }]);
      }, 800);
      return () => clearTimeout(timer);
    }
  }, [isOpen, messages.length, isStreaming]);

  // Stop in-flight request when component unmounts
  useEffect(() => {
    return () => abortControllerRef.current?.abort();
  }, []);

  // Lock body & html scroll correctly using fixed positioning
  useEffect(() => {
    let scrollPos = 0;
    const lock = () => {
      scrollPos = window.scrollY;
      document.body.style.position = 'fixed';
      document.body.style.top = `-${scrollPos}px`;
      document.body.style.left = '0';
      document.body.style.right = '0';
      document.body.style.width = '100%';
      document.body.style.overflow = 'hidden';
    };
    const unlock = () => {
      const top = document.body.style.top;
      document.body.style.position = '';
      document.body.style.top = '';
      document.body.style.left = '';
      document.body.style.right = '';
      document.body.style.width = '';
      document.body.style.overflow = '';
      if (top) {
        window.scrollTo(0, parseInt(top || '0') * -1);
      }
    };

    if (isOpen) {
      lock();
    } else {
      unlock();
    }
    return unlock;
  }, [isOpen]);

  const handleClose = () => {
    setIsClosing(true);
    // Xoá layoutId trước, sau đó mới tắt thực sự để dùng exit animation cho nền trắng
    setTimeout(() => {
      setIsOpen(false);
      if (dontShowAgain) {
        localStorage.setItem('chatbot_dismissed', 'true');
      }
    }, 20);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isStreaming) return;

    const userMessage: Message = { role: 'user', content: input.trim() };
    const currentMessages = [...messages, userMessage];
    setMessages(currentMessages);
    setInput('');
    setIsStreaming(true);

    const newController = new AbortController();
    abortControllerRef.current = newController;

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: currentMessages.map((m) => ({
            role: m.role === 'error' ? 'assistant' : m.role,
            content: m.content,
          })),
        }),
        signal: newController.signal,
      });

      if (!response.ok || !response.body) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || `Server error: ${response.status}`);
      }

      const answer = await response.text();
      const updatedMessages = [...currentMessages, { role: 'assistant' as const, content: answer }];
      setMessages(updatedMessages);

      // Refocus input after sending
      setTimeout(() => inputRef.current?.focus(), 100);
    } catch (error: any) {
      if (error.name === 'AbortError') return;
      setMessages((prev) => [...prev, { role: 'error', content: `⚠️ Lỗi: ${error.message}. Vui lòng thử lại sau.` }]);
    } finally {
      setIsStreaming(false);
      abortControllerRef.current = null;
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-[9999] flex items-center justify-center pointer-events-none p-4 md:p-8">
          {/* Backdrop Overlay */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={handleClose}
            className="absolute inset-0 bg-slate-900/40 backdrop-blur-md pointer-events-auto"
          />

          {/* Expansion Shell */}
          <motion.div
            layoutId={isClosing ? undefined : "chatbot-modal"}
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95, transition: { duration: 0.2, ease: "easeOut" } }}
            transition={{
              type: "spring",
              stiffness: 400,
              damping: 40,
              mass: 1,
              layout: { duration: 0.35, ease: "circOut" }
            }}
            style={{
              willChange: "transform, opacity, border-radius",
              transform: "translateZ(0)"
            }}
            className="w-full max-w-5xl h-full max-h-[850px] flex flex-col bg-white rounded-[40px] md:rounded-[48px] shadow-2xl overflow-hidden border border-slate-200 pointer-events-auto relative z-10"
          >
              <AnimatePresence>
                  <motion.div
                    key="chat-content"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 0.4, delay: 0.15, ease: "easeOut" }}
                    className="flex flex-col h-full w-full"
                  >
              {/* Header */}
              <div className="flex-none p-4 md:p-6 flex justify-between items-center bg-white border-b border-slate-100">
                <div className="flex items-center gap-3 md:gap-4">
                  <motion.div
                    layoutId="chatbot-icon"
                    className="w-10 h-10 md:w-12 md:h-12 rounded-full bg-white/80 backdrop-blur-md flex items-center justify-center shadow-lg ring-1 ring-white/50 text-emerald-500"
                  >
                    <Sparkles size={28} className="text-emerald-500" />
                  </motion.div>
                  <div>
                    <h3 className="font-bold text-slate-800 text-lg md:text-xl">Nhân viên hỗ trợ</h3>
                    <div className="flex items-center gap-1.5">
                      <span className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></span>
                      <span className="text-[11px] text-slate-500 font-bold uppercase tracking-wider">Trực tuyến 24/7</span>
                    </div>
                  </div>
                </div>
                <button
                  onClick={handleClose}
                  className="hover:bg-slate-100 p-2 rounded-full transition-colors text-slate-400"
                >
                  <X size={24} />
                </button>
              </div>

              {/* Messages Area */}
              <div
                className="flex-1 overflow-y-auto p-4 md:p-10 space-y-8 bg-slate-50 custom-scrollbar"
                style={{ WebkitOverflowScrolling: 'touch' }}
                onWheel={(e) => e.stopPropagation()}
              >
                {messages.map((msg, index) => (
                  <div
                    key={index}
                    className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div className={`flex gap-3 md:gap-5 max-w-[85%] ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                      <div
                        className={`w-10 h-10 md:w-12 md:h-12 rounded-full flex-shrink-0 flex items-center justify-center shadow-md ${msg.role === 'user'
                          ? 'bg-slate-100 text-slate-500'
                          : 'bg-emerald-500 text-white'
                          }`}
                      >
                        {msg.role === 'user' ? <User size={22} /> : <Sparkles size={22} />}
                      </div>
                      <div
                        className={`p-4 px-6 md:p-5 md:px-8 rounded-3xl text-[15px] md:text-[16px] leading-relaxed shadow-sm ${msg.role === 'user'
                          ? 'bg-emerald-500 text-white font-medium shadow-emerald-200 shadow-lg'
                          : msg.role === 'error'
                            ? 'bg-red-50 text-red-600 border border-red-100'
                            : 'bg-white text-slate-700 border border-slate-100'
                          }`}
                        style={{ whiteSpace: 'pre-wrap' }}
                      >
                        {msg.content}
                      </div>
                    </div>
                  </div>
                ))}

                {/* Messenger-style Typing Indicator */}
                {isStreaming && (
                  <div className="flex justify-start">
                    <div className="flex gap-3 items-start max-w-[85%]">
                      <div className="w-10 h-10 rounded-full bg-emerald-500 text-white flex items-center justify-center flex-shrink-0 shadow-sm">
                        <Sparkles size={20} />
                      </div>
                      <div className="bg-white border border-slate-100 px-6 py-4 rounded-3xl flex gap-1.5 items-center shadow-sm">
                        <span className="w-2 h-2 bg-emerald-400 rounded-full animate-bounce [animation-delay:-0.3s]"></span>
                        <span className="w-2 h-2 bg-emerald-400 rounded-full animate-bounce [animation-delay:-0.15s]"></span>
                        <span className="w-2 h-2 bg-emerald-400 rounded-full animate-bounce"></span>
                      </div>
                    </div>
                  </div>
                )}

                <div ref={messagesEndRef} />
              </div>

              {/* Input Area */}
              <form onSubmit={handleSubmit} className="flex-none p-4 md:p-8 bg-white border-t border-slate-100">
                <div className="flex flex-col gap-5">
                  <div className="relative flex items-center group max-w-4xl mx-auto w-full">
                    <input
                      ref={inputRef}
                      type="text"
                      value={input}
                      onChange={(e) => setInput(e.target.value)}
                      placeholder="Nhập tin nhắn để tư vấn dịch vụ cho khách hàng..."
                      className="w-full bg-slate-50 text-slate-800 rounded-[2rem] py-5 px-8 pr-20 focus:outline-none focus:ring-4 focus:ring-emerald-500/10 text-base md:text-lg border border-slate-200 transition-all placeholder:text-slate-400 group-hover:border-slate-300 disabled:opacity-50"
                    />
                    <button
                      type="submit"
                      disabled={isStreaming || !input.trim()}
                      className="absolute right-3 p-3.5 rounded-full bg-emerald-500 text-white hover:bg-emerald-600 disabled:bg-slate-200 disabled:text-slate-400 transition-all shadow-xl shadow-emerald-500/20"
                    >
                      <Send size={24} />
                    </button>
                  </div>

                  <div className="flex flex-col items-center gap-3">
                    <div className="flex items-center gap-8">
                      <button
                        type="button"
                        onClick={handleClose}
                        className="text-[14px] font-bold text-white bg-slate-800 px-10 py-3 rounded-full hover:bg-slate-900 transition-all shadow-lg"
                      >
                        Bỏ qua để xem Website
                      </button>
                    </div>

                    {/* Checkbox "Don't show again" */}
                    <label className="flex items-center gap-2 cursor-pointer group">
                      <input
                        type="checkbox"
                        checked={dontShowAgain}
                        onChange={(e) => setDontShowAgain(e.target.checked)}
                        className="w-4 h-4 rounded border-slate-300 text-emerald-500 focus:ring-emerald-500 transition-all cursor-pointer"
                      />
                        <span className="text-[12px] text-slate-400 group-hover:text-slate-500 transition-colors">
                          Không tự động hiển thị lại lần sau
                        </span>
                      </label>
                    </div>
                  </div>
                </form>
              </motion.div>
          </AnimatePresence>
        </motion.div>
      </div>
    )}
  </AnimatePresence>
  );
};

export default Chatbot;
