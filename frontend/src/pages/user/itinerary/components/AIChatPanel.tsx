import { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Send, Bot, User, Check, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useAIChat } from '../hooks/useAIChat';

interface AIChatPanelProps {
  tripId: string;
}

export default function AIChatPanel({ tripId }: AIChatPanelProps) {
  const { messages, currentThought, isThinking, sendMessage, approveDraft } = useAIChat(tripId);
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, currentThought]);

  const handleSend = () => {
    if (!input.trim() || isThinking) return;
    sendMessage(input);
    setInput('');
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex flex-col h-full bg-slate-50 border-l border-slate-200">
      {/* Header */}
      <div className="flex items-center justify-between p-4 bg-white border-b border-slate-200">
        <div className="flex items-center gap-2">
          <Bot className="w-5 h-5 text-emerald-600" />
          <h2 className="font-semibold text-slate-800 tracking-tight">AI Assistant</h2>
        </div>
        <Button 
          variant="outline" 
          size="sm" 
          className="text-emerald-700 border-emerald-200 bg-emerald-50 hover:bg-emerald-100"
          onClick={approveDraft}
          disabled={isThinking || messages.length === 0}
        >
          <Check className="w-4 h-4 mr-2" />
          Approve Draft
        </Button>
      </div>

      {/* Chat History */}
      <div className="flex-1 p-4 overflow-y-auto space-y-6">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center space-y-3">
            <div className="w-12 h-12 rounded-full bg-emerald-100 flex items-center justify-center">
              <Bot className="w-6 h-6 text-emerald-600" />
            </div>
            <p className="text-slate-500 max-w-[200px] text-sm">
              I can help you brainstorm and draft the perfect itinerary.
            </p>
          </div>
        ) : (
          messages.map((msg) => (
            <div key={msg.id} className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
              <div className={`w-8 h-8 rounded-md flex items-center justify-center shrink-0 ${msg.role === 'user' ? 'bg-slate-800 text-white' : 'bg-emerald-100 text-emerald-700'}`}>
                {msg.role === 'user' ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
              </div>
              <div className={`flex flex-col max-w-[85%] ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                <div className={`px-4 py-3 rounded-lg text-sm shadow-sm ${msg.role === 'user' ? 'bg-slate-800 text-white' : 'bg-white border border-slate-200 text-slate-800'}`}>
                  {msg.role === 'user' ? (
                    <p className="whitespace-pre-wrap">{msg.content}</p>
                  ) : (
                    <div className="prose prose-sm prose-emerald max-w-none">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown>
                    </div>
                  )}
                </div>
                {msg.isStreaming && (
                  <span className="flex mt-1 text-emerald-500">
                    <Loader2 className="w-3 h-3 animate-spin" />
                  </span>
                )}
              </div>
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Agent Thoughts Terminal */}
      {isThinking && currentThought && (
        <div className="bg-[#0D1117] border-t border-slate-800 p-3 max-h-40 overflow-y-auto font-mono text-xs text-emerald-400">
          <div className="flex items-center gap-2 mb-2 pb-2 border-b border-slate-800/50">
            <Loader2 className="w-3 h-3 animate-spin text-emerald-500" />
            <span className="text-slate-400 font-semibold tracking-wider text-[10px] uppercase">Agent Internal Reasoning</span>
          </div>
          <pre className="whitespace-pre-wrap opacity-90">{currentThought}</pre>
        </div>
      )}

      {/* Input Area */}
      <div className="p-4 bg-white border-t border-slate-200">
        <div className="relative flex items-end gap-2 bg-slate-50 border border-slate-200 rounded-lg p-2 focus-within:ring-1 focus-within:ring-emerald-500 focus-within:border-emerald-500 transition-all">
          <textarea
            className="flex-1 max-h-32 min-h-[40px] bg-transparent resize-none outline-none py-2 px-2 text-sm text-slate-800 placeholder:text-slate-400"
            placeholder="Ask AI to plan or modify your draft..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isThinking}
            rows={1}
          />
          <Button 
            size="icon" 
            className="h-10 w-10 shrink-0 bg-emerald-600 hover:bg-emerald-700 shadow-sm"
            onClick={handleSend}
            disabled={!input.trim() || isThinking}
          >
            <Send className="w-4 h-4" />
          </Button>
        </div>
        <p className="text-center text-[10px] text-slate-400 mt-2 font-medium">
          AI can make mistakes. Please verify the draft before approving.
        </p>
      </div>
    </div>
  );
}
