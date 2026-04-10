"use client";
import { useEffect, useState } from "react";
import { getDecisions, getOpenQuestions, Decision, OpenQuestion } from "@/lib/api";

export default function DecisionsPage() {
  const [decisions, setDecisions] = useState<Decision[]>([]);
  const [questions, setQuestions] = useState<OpenQuestion[]>([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<"decisions" | "questions">("decisions");

  useEffect(() => {
    Promise.all([
      getDecisions().then(setDecisions),
      getOpenQuestions().then(setQuestions),
    ]).catch(() => {}).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="p-8 text-[14px]" style={{ color: "var(--text-secondary)" }}>Loading...</div>;

  const urgencyStyles: Record<string, { bg: string; text: string }> = {
    high: { bg: "#fde8ea", text: "#d13438" },
    medium: { bg: "#fff8e1", text: "#f5a623" },
    low: { bg: "#e8f0fd", text: "#0070d2" },
  };

  const highCount = questions.filter(q => q.urgency === "high" && q.status === "open").length;
  const openCount = questions.filter(q => q.status === "open").length;

  return (
    <div className="p-6 max-w-[1200px] mx-auto space-y-6">
      <div>
        <h1 className="text-[24px] font-semibold">Decisions & Open Questions</h1>
        <p className="text-[13px] mt-1" style={{ color: "var(--text-secondary)" }}>
          Track key decisions and unresolved questions across your communications.
        </p>
      </div>

      {/* Tabs */}
      <div className="flex gap-1">
        <button
          onClick={() => setTab("decisions")}
          className="px-4 py-2 rounded-lg text-[13px] font-medium transition-colors"
          style={{
            background: tab === "decisions" ? "var(--accent-blue)" : "var(--card-bg)",
            color: tab === "decisions" ? "white" : "var(--text-secondary)",
            border: `1px solid ${tab === "decisions" ? "var(--accent-blue)" : "var(--border)"}`,
          }}
        >
          Decisions ({decisions.length})
        </button>
        <button
          onClick={() => setTab("questions")}
          className="px-4 py-2 rounded-lg text-[13px] font-medium transition-colors"
          style={{
            background: tab === "questions" ? "var(--accent-blue)" : "var(--card-bg)",
            color: tab === "questions" ? "white" : "var(--text-secondary)",
            border: `1px solid ${tab === "questions" ? "var(--accent-blue)" : "var(--border)"}`,
          }}
        >
          Open Questions ({openCount})
          {highCount > 0 && (
            <span className="ml-2 px-1.5 py-0.5 rounded-full text-[10px]" style={{ background: "#fde8ea", color: "#d13438" }}>
              {highCount} high
            </span>
          )}
        </button>
      </div>

      {/* Decisions */}
      {tab === "decisions" && (
        <div className="space-y-2">
          {decisions.length === 0 ? (
            <div className="card p-8 text-center text-[13px]" style={{ color: "var(--text-secondary)" }}>
              No decisions tracked yet. Use the chat to log decisions.
            </div>
          ) : (
            decisions.map((d) => (
              <div key={d.id} className="card p-4 flex items-start gap-3">
                <span style={{ color: "var(--ai-teal)", fontSize: 14, marginTop: 2 }}>{"\u2726"}</span>
                <div className="flex-1">
                  <div className="text-[13px]" style={{ color: "var(--text-primary)" }}>{d.description}</div>
                  <div className="flex items-center gap-3 mt-2 text-[11px]" style={{ color: "var(--text-secondary)" }}>
                    {d.channel && <span>#{d.channel}</span>}
                    <span>{d.decided_at?.slice(0, 10)}</span>
                    {d.related_priority && (
                      <span className="px-2 py-0.5 rounded-full" style={{ background: "rgba(0,112,210,0.08)", color: "var(--accent-blue)", fontSize: 10 }}>
                        {d.related_priority.split(" ").slice(0, 3).join(" ")}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* Open Questions */}
      {tab === "questions" && (
        <div className="space-y-2">
          {questions.length === 0 ? (
            <div className="card p-8 text-center text-[13px]" style={{ color: "var(--text-secondary)" }}>
              No open questions tracked yet.
            </div>
          ) : (
            questions.map((q) => {
              const style = urgencyStyles[q.urgency] || urgencyStyles.medium;
              return (
                <div key={q.id} className="card p-4 flex items-start gap-3">
                  <span style={{ fontSize: 14, marginTop: 2 }}>?</span>
                  <div className="flex-1">
                    <div className="text-[13px]" style={{ color: "var(--text-primary)" }}>{q.description}</div>
                    <div className="flex items-center gap-3 mt-2 text-[11px]" style={{ color: "var(--text-secondary)" }}>
                      {q.owner && <span>Owner: {q.owner}</span>}
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-medium" style={{ background: style.bg, color: style.text }}>
                        {q.urgency}
                      </span>
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-medium ${q.status === "open" ? "" : "opacity-60"}`}
                        style={{ background: q.status === "open" ? "#e8f7f0" : "#f3f4f6", color: q.status === "open" ? "#1aab68" : "#9ca3af" }}>
                        {q.status}
                      </span>
                      {q.related_priority && (
                        <span className="px-2 py-0.5 rounded-full" style={{ background: "rgba(0,112,210,0.08)", color: "var(--accent-blue)", fontSize: 10 }}>
                          {q.related_priority.split(" ").slice(0, 3).join(" ")}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>
      )}
    </div>
  );
}
