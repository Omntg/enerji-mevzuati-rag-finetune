import React, { useState, useRef, useEffect } from 'react';
import { Send, FileText, BookOpen, User, Bot, Sparkles, ChevronRight, Zap } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    const assistantMessageId = Date.now();
    setMessages(prev => [...prev, { 
      id: assistantMessageId,
      role: 'assistant', 
      content: '', 
      sources: [] 
    }]);

    try {
      const response = await fetch('http://127.0.0.1:8000/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: userMessage.content }),
      });

      if (!response.ok) throw new Error('Network response was not ok');

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        buffer += chunk;
        
        const lines = buffer.split('\n\n');
        buffer = lines.pop();

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const jsonStr = line.slice(6);
            if (jsonStr === '[DONE]') continue;
            
            try {
              const data = JSON.parse(jsonStr);
              setMessages(prev => prev.map(msg => {
                if (msg.id === assistantMessageId) {
                  if (data.token) return { ...msg, content: msg.content + data.token };
                  if (data.sources) return { ...msg, sources: data.sources };
                }
                return msg;
              }));
            } catch (e) {
              console.error("JSON Parse Error:", e);
            }
          }
        }
      }
    } catch (error) {
      console.error("Error:", error);
      setMessages(prev => prev.map(msg => {
        if (msg.id === assistantMessageId) {
          return { 
            ...msg, 
            content: "Üzgünüm, bir hata oluştu. Lütfen bağlantınızı kontrol edip tekrar deneyin.",
            isError: true 
          };
        }
        return msg;
      }));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-[#0f172a] text-slate-200 font-sans selection:bg-indigo-500/30">
      
      {/* Background Ambience */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        <div className="absolute -top-[20%] -left-[10%] w-[50%] h-[50%] bg-blue-500/10 rounded-full blur-[120px]" />
        <div className="absolute top-[20%] -right-[10%] w-[40%] h-[40%] bg-indigo-500/10 rounded-full blur-[100px]" />
      </div>

      {/* Header */}
      <header className="flex items-center justify-between px-6 py-4 bg-slate-900/50 backdrop-blur-xl border-b border-white/5 sticky top-0 z-20">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-gradient-to-br from-indigo-500 to-blue-600 rounded-xl shadow-lg shadow-indigo-500/20">
            <BookOpen className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-white tracking-tight">Enerji Mevzuatı Asistanı</h1>
            <div className="flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
              <p className="text-xs text-slate-400 font-medium">Sistem Çevrimiçi</p>
            </div>
          </div>
        </div>
        <div className="hidden md:flex items-center gap-3 px-3 py-1.5 bg-white/5 rounded-full border border-white/5">
          <Sparkles className="w-3.5 h-3.5 text-amber-300" />
          <span className="text-xs text-slate-300 font-medium">Gemma-3-4b-it & RAG</span>
        </div>
      </header>

      {/* Chat Area */}
      <div className="flex-1 overflow-y-auto px-4 py-6 scrollbar-hide relative z-10">
        <div className="max-w-3xl mx-auto space-y-8">
          
          {messages.length === 0 && (
            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex flex-col items-center justify-center h-[60vh] text-center space-y-6"
            >
              <div className="w-20 h-20 bg-gradient-to-tr from-indigo-500/20 to-blue-500/20 rounded-3xl flex items-center justify-center border border-white/5 shadow-2xl">
                <Zap className="w-10 h-10 text-indigo-400" />
              </div>
              <div className="space-y-2 max-w-md">
                <h2 className="text-2xl font-bold text-white">Size nasıl yardımcı olabilirim?</h2>
                <p className="text-slate-400">Türkiye Enerji Mevzuatı hakkında her şeyi sorabilirsiniz. Kanunlar, yönetmelikler ve tebliğler taranır.</p>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full max-w-lg mt-8">
                {['Lisans başvuru süreci nasıl işler?', 'Önlisans süreleri nelerdir?', 'Yeka yarışma şartları', 'Teminat mektubu tutarları'].map((q, i) => (
                  <button 
                    key={i}
                    onClick={() => { setInput(q); }}
                    className="p-4 bg-white/5 hover:bg-white/10 border border-white/5 hover:border-indigo-500/30 rounded-xl text-left text-sm text-slate-300 transition-all group"
                  >
                    <span className="group-hover:text-indigo-300 transition-colors">{q}</span>
                  </button>
                ))}
              </div>
            </motion.div>
          )}

          <AnimatePresence mode='popLayout'>
            {messages.map((msg, index) => (
              <motion.div
                key={msg.id || index}
                initial={{ opacity: 0, y: 20, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                className={`flex gap-4 ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}
              >
                {/* Avatar */}
                <div className={`w-10 h-10 rounded-2xl flex items-center justify-center flex-shrink-0 shadow-lg ${
                  msg.role === 'user' 
                    ? 'bg-gradient-to-br from-indigo-500 to-blue-600' 
                    : (msg.isError ? 'bg-red-500/20 text-red-400 border border-red-500/30' : 'bg-slate-800 border border-white/5')
                }`}>
                  {msg.role === 'user' ? <User size={20} className="text-white" /> : <Bot size={20} className={msg.isError ? 'text-red-400' : 'text-emerald-400'} />}
                </div>

                {/* Content */}
                <div className={`flex flex-col max-w-[85%] sm:max-w-[75%] space-y-3`}>
                  <div className={`p-5 rounded-2xl leading-relaxed text-[15px] shadow-sm ${
                    msg.role === 'user'
                      ? 'bg-indigo-600 text-white rounded-tr-sm'
                      : 'bg-slate-800/80 border border-white/5 text-slate-200 rounded-tl-sm backdrop-blur-sm'
                  }`}>
                    {msg.content}
                    {msg.role === 'assistant' && loading && index === messages.length - 1 && (
                      <span className="inline-block w-1.5 h-4 ml-1.5 align-middle bg-emerald-400/50 animate-pulse rounded-full" />
                    )}
                  </div>

                  {/* Sources */}
                  {msg.sources && msg.sources.length > 0 && (
                    <motion.div 
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      className="flex flex-wrap gap-2"
                    >
                      {msg.sources.map((src, i) => (
                        <div key={i} className="group relative">
                          <div className="flex items-center gap-2 px-3 py-1.5 bg-slate-900/60 border border-white/10 hover:border-emerald-500/30 rounded-lg text-xs text-slate-400 hover:text-emerald-300 transition-all cursor-help">
                            <FileText size={12} className="text-emerald-500" />
                            <span className="font-medium">{src.source_file.replace('.pdf', '')}</span>
                            <span className="w-px h-3 bg-white/10" />
                            <span>Md. {src.article_number}</span>
                          </div>
                          
                          {/* Tooltip */}
                          <div className="absolute bottom-full left-0 mb-3 w-72 p-4 bg-slate-950 border border-white/10 rounded-xl shadow-2xl opacity-0 translate-y-2 group-hover:opacity-100 group-hover:translate-y-0 transition-all duration-200 pointer-events-none z-50">
                            <div className="flex items-center gap-2 mb-2 text-xs font-bold text-emerald-400 uppercase tracking-wider">
                              <Sparkles size={10} />
                              {src.section || 'İlgili Bölüm'}
                            </div>
                            <p className="text-xs text-slate-300 leading-5 line-clamp-6 bg-slate-900/50 p-2 rounded-lg border border-white/5">
                              {src.content}
                            </p>
                            <div className="absolute bottom-[-6px] left-4 w-3 h-3 bg-slate-950 border-r border-b border-white/10 transform rotate-45"></div>
                          </div>
                        </div>
                      ))}
                    </motion.div>
                  )}
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
          <div ref={messagesEndRef} className="h-4" />
        </div>
      </div>

      {/* Input Area */}
      <div className="p-4 sm:p-6 bg-slate-900/80 backdrop-blur-xl border-t border-white/5 relative z-20">
        <form onSubmit={handleSubmit} className="max-w-3xl mx-auto relative group">
          <div className="absolute inset-0 bg-gradient-to-r from-indigo-500/20 to-blue-500/20 rounded-2xl blur opacity-0 group-focus-within:opacity-100 transition-opacity duration-500" />
          
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Enerji mevzuatı hakkında bir soru sorun..."
            className="w-full bg-slate-800/80 text-white placeholder-slate-500 rounded-2xl pl-6 pr-14 py-4 focus:outline-none focus:ring-1 focus:ring-indigo-500/50 border border-white/10 transition-all shadow-xl relative z-10"
            disabled={loading}
          />
          
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="absolute right-3 top-1/2 -translate-y-1/2 p-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed hover:scale-105 active:scale-95 shadow-lg shadow-indigo-600/20 z-20"
          >
            {loading ? (
              <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            ) : (
              <Send size={18} />
            )}
          </button>
        </form>
        <p className="text-center mt-3 text-[10px] text-slate-600 font-medium tracking-wide">
          Yapay zeka hatalı bilgi verebilir. Lütfen mevzuatı resmi kaynaklardan teyit ediniz.
        </p>
      </div>
    </div>
  );
}

export default App;
