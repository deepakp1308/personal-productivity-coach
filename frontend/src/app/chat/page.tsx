"use client";
import { useState, useRef, useEffect } from "react";
import { sendChatMessage } from "@/lib/api";

function renderMarkdown(text: string) {
  const lines = text.split("\n");
  const elements: React.ReactNode[] = [];
  lines.forEach((line, i) => {
    const parts = line.split(/(\*\*[^*]+\*\*)/g);
    const rendered = parts.map((part, j) => {
      if (part.startsWith("**") && part.endsWith("**")) {
        return <strong key={j}>{part.slice(2, -2)}</strong>;
      }
      if (part.startsWith("_") && part.endsWith("_") && part.length > 2) {
        return <em key={j}>{part.slice(1, -1)}</em>;
      }
      return part;
    });
    const trimmed = line.trim();
    if (trimmed.startsWith("- ") || trimmed.startsWith("  -")) {
      elements.push(<div key={i} style={{ paddingLeft: trimmed.startsWith("  ") ? 16 : 8 }}>{rendered}</div>);
    } else {
      elements.push(<span key={i}>{rendered}</span>);
    }
    if (i < lines.length - 1) elements.push(<br key={`br-${i}`} />);
  });
  return <>{elements}</>;
}

interface Message {
  role: "user" | "assistant";
  content: string;
}

const SUGGESTED = [
  "What did I spend time on yesterday?",
  "Am I on track for Analytics Agent this week?",
  "Show me my priority alignment",
  "What decisions did I make this week?",
  "What open questions need attention?",
  "Give me coaching recommendations",
  "How many meeting hours this week?",
  "Any anomalies or concerns?",
];

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string>("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const send = async (text: string) => {
    if (!text.trim() || loading) return;
    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setInput("");
    setLoading(true);
    try {
      const res = await sendChatMessage(text, sessionId || undefined);
      setSessionId(res.context?.session_id || sessionId);
      setMessages((prev) => [...prev, { role: "assistant", content: res.response }]);
    } catch {
      setMessages((prev) => [...prev, { role: "assistant", content: "Sorry, I encountered an error. Is the backend running?" }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full">
      <div className="p-6 pb-3">
        <h1 className="text-[24px] font-semibold flex items-center gap-2">
          <span style={{ color: "var(--ai-teal)" }}>{"\u2726"}</span> Ask Your Coach
        </h1>
        <p className="text-[13px] mt-1" style={{ color: "var(--text-secondary)" }}>
          Ask about your time allocation, priorities, decisions, and patterns. All answers cite your actual data.
        </p>
      </div>

      <div className="flex-1 overflow-y-auto px-6 space-y-4">
        {messages.length === 0 && (
          <div className="py-8">
            <div className="text-[14px] font-medium mb-4" style={{ color: "var(--text-secondary)" }}>Try asking:</div>
            <div className="flex flex-wrap gap-2">
              {SUGGESTED.map((q) => (
                <button
                  key={q}
                  onClick={() => send(q)}
                  className="text-[12px] px-3 py-2 rounded-lg transition-colors hover:shadow-sm"
                  style={{ background: "var(--card-bg)", border: "1px solid var(--border)", color: "var(--text-primary)" }}
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            <div
              className={`max-w-[70%] rounded-xl px-4 py-3 text-[13px]`}
              style={{
                background: msg.role === "user" ? "var(--accent-blue)" : "var(--card-bg)",
                border: msg.role === "assistant" ? "1px solid var(--border)" : "none",
                color: msg.role === "user" ? "white" : "var(--text-primary)",
              }}
            >
              {msg.role === "assistant" && (
                <div className="flex items-center gap-1 mb-1">
                  <span style={{ color: "var(--ai-teal)" }}>{"\u2726"}</span>
                  <span className="text-[11px] font-medium" style={{ color: "var(--ai-teal)" }}>Self Coach</span>
                </div>
              )}
              <div style={{ whiteSpace: "pre-wrap" }}>{msg.role === "assistant" ? renderMarkdown(msg.content) : msg.content}</div>
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="card px-4 py-3">
              <div className="flex items-center gap-2 text-[13px]" style={{ color: "var(--text-secondary)" }}>
                <span style={{ color: "var(--ai-teal)" }}>{"\u2726"}</span> Thinking...
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="p-6 pt-3">
        <div className="flex gap-3">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && send(input)}
            placeholder="Ask about your productivity..."
            className="flex-1 px-4 py-3 rounded-xl text-[13px] outline-none focus:ring-2 focus:ring-[var(--ai-teal)]"
            style={{ background: "var(--card-bg)", border: "1px solid var(--border)" }}
            disabled={loading}
          />
          <button
            onClick={() => send(input)}
            disabled={loading || !input.trim()}
            className="px-5 py-3 rounded-xl text-[13px] font-medium text-white disabled:opacity-50"
            style={{ background: "var(--accent-blue)" }}
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
