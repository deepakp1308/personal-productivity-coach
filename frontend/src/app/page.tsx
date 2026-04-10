"use client";
import { useEffect, useState } from "react";
import { getDashboard, DashboardData, Recommendation, Decision, OpenQuestion } from "@/lib/api";
import Link from "next/link";

const PRIORITY_COLOR_MAP: Record<string, string> = {
  "Advanced Analytics & AI-Powered Insights": "var(--chart-navy)",
  "Platform Intelligence Across MC & QBO": "var(--chart-blue)",
  "Trusted Data Foundation & Quality at Scale": "var(--chart-teal)",
  "Other": "var(--chart-pink)",
};

function priorityColor(name: string): string {
  return PRIORITY_COLOR_MAP[name] || "var(--chart-pink)";
}

function MetricCard({ label, value, sub, color }: { label: string; value: string; sub?: string; color?: string }) {
  return (
    <div className="card p-5">
      <div className="text-[12px] font-medium" style={{ color: "var(--text-secondary)" }}>{label}</div>
      <div className="text-[28px] font-semibold mt-1" style={{ color: color || "var(--text-primary)" }}>{value}</div>
      {sub && <div className="text-[12px] mt-1" style={{ color: "var(--text-secondary)" }}>{sub}</div>}
    </div>
  );
}

function AIInsightBanner({ insight }: { insight: string }) {
  return (
    <div className="card p-5 flex items-start gap-3" style={{ borderLeft: "3px solid var(--ai-teal)" }}>
      <span className="text-xl" style={{ color: "var(--ai-teal)" }}>{"\u2726"}</span>
      <div>
        <div className="text-[14px] font-semibold" style={{ color: "var(--text-primary)" }}>Today&apos;s Insight</div>
        <div className="text-[13px] mt-1" style={{ color: "var(--text-secondary)" }}>{insight}</div>
      </div>
    </div>
  );
}

function RecCard({ rec }: { rec: Recommendation }) {
  const kindColors: Record<string, string> = { Accelerate: "badge-accelerate", Cut: "badge-cut", Redirect: "badge-redirect" };
  return (
    <div className="card p-5">
      <div className="flex items-center justify-between mb-2">
        <span style={{ color: "var(--ai-teal)" }}>{"\u2726"}</span>
        <span className={`text-[11px] font-medium px-2 py-0.5 rounded-full ${kindColors[rec.kind]}`}>{rec.kind}</span>
      </div>
      <div className="text-[13px]" style={{ color: "var(--text-primary)" }}>{rec.action}</div>
      <div className="text-[12px] mt-2" style={{ color: "var(--text-secondary)" }}>{rec.rationale}</div>
      {rec.judge_score && (
        <div className="mt-2 text-[11px]" style={{ color: "var(--text-secondary)" }}>
          Judge: {rec.judge_score}/5 | {rec.evidence_ids?.length || 0} evidence
        </div>
      )}
    </div>
  );
}

function DecisionCard({ decision }: { decision: Decision }) {
  return (
    <div className="card p-4 flex items-start gap-3">
      <span style={{ color: "var(--ai-teal)", fontSize: 14, marginTop: 2 }}>{"\u2726"}</span>
      <div className="flex-1">
        <div className="text-[13px]" style={{ color: "var(--text-primary)" }}>{decision.description}</div>
        <div className="flex items-center gap-3 mt-2 text-[11px]" style={{ color: "var(--text-secondary)" }}>
          {decision.channel && <span>{decision.channel}</span>}
          <span>{decision.decided_at?.slice(0, 10)}</span>
          {decision.related_priority && (
            <span className="px-2 py-0.5 rounded-full" style={{ background: "rgba(0,112,210,0.08)", color: "var(--accent-blue)", fontSize: 10 }}>
              {decision.related_priority.split(" ").slice(0, 3).join(" ")}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

function QuestionCard({ question }: { question: OpenQuestion }) {
  const urgencyStyles: Record<string, { bg: string; text: string }> = {
    high: { bg: "#fde8ea", text: "#d13438" },
    medium: { bg: "#fff8e1", text: "#f5a623" },
    low: { bg: "#e8f0fd", text: "#0070d2" },
  };
  const style = urgencyStyles[question.urgency] || urgencyStyles.medium;
  return (
    <div className="card p-4 flex items-start gap-3">
      <span style={{ fontSize: 14, marginTop: 2 }}>?</span>
      <div className="flex-1">
        <div className="text-[13px]" style={{ color: "var(--text-primary)" }}>{question.description}</div>
        <div className="flex items-center gap-3 mt-2 text-[11px]" style={{ color: "var(--text-secondary)" }}>
          {question.owner && <span>Owner: {question.owner}</span>}
          <span className="px-2 py-0.5 rounded-full text-[10px] font-medium" style={{ background: style.bg, color: style.text }}>{question.urgency}</span>
        </div>
      </div>
    </div>
  );
}

export default function BriefingPage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getDashboard().then(setData).catch(() => {}).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="p-8 text-[14px]" style={{ color: "var(--text-secondary)" }}>Loading briefing...</div>;
  if (!data) return <div className="p-8 text-[14px]" style={{ color: "var(--red)" }}>Failed to load. Is the backend running on port 8001?</div>;

  const hour = new Date().getHours();
  const greeting = hour < 12 ? "Good morning" : hour < 18 ? "Good afternoon" : "Good evening";
  const dateStr = new Date().toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric", year: "numeric" });

  return (
    <div className="p-6 max-w-[1200px] mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-[24px] font-semibold">{greeting}, Deepak</h1>
          <p className="text-[13px] mt-1" style={{ color: "var(--text-secondary)" }}>{dateStr}</p>
        </div>
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg" style={{ background: "rgba(0,185,169,0.08)", border: "1px solid rgba(0,185,169,0.2)" }}>
          <span style={{ color: "var(--ai-teal)", fontSize: 14 }}>{"\u2726"}</span>
          <span className="text-[13px] font-semibold" style={{ color: "var(--text-primary)" }}>Personal Coach</span>
        </div>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-4 gap-4">
        <MetricCard
          label="Priority Alignment"
          value={`${data.alignment_pct}%`}
          sub="this week"
          color={data.alignment_pct >= 70 ? "var(--green)" : "var(--warning)"}
        />
        <MetricCard label="Meeting Hours" value={`${data.meeting_hours}h`} sub="this week" />
        <MetricCard label="Activities" value={String(data.total_activities)} sub="tracked" color="var(--accent-blue)" />
        <MetricCard
          label="Open Questions"
          value={String(data.open_questions_count)}
          sub="unresolved"
          color={data.open_questions_count > 3 ? "var(--red)" : "var(--ai-teal)"}
        />
      </div>

      {/* AI Insight */}
      <AIInsightBanner insight={data.top_insight} />

      {/* Priority Pulse */}
      {Object.keys(data.priority_breakdown).length > 0 && (
        <div className="card p-5">
          <h2 className="text-[16px] font-semibold mb-3">Priority Pulse</h2>
          <div className="flex h-3 rounded-full overflow-hidden bg-gray-100 mb-3">
            {Object.entries(data.priority_breakdown).map(([name, pct]) => (
              <div key={name} style={{ width: `${pct}%`, background: priorityColor(name) }} title={`${name}: ${pct}%`} />
            ))}
          </div>
          <div className="grid grid-cols-3 gap-4">
            {Object.entries(data.priority_breakdown).map(([name, pct]) => {
              const target = data.priority_targets?.[name] || 0;
              const delta = pct - target;
              return (
                <div key={name} className="flex items-center gap-2">
                  <span className="w-3 h-3 rounded-full" style={{ background: priorityColor(name) }} />
                  <div>
                    <div className="text-[12px] font-medium">{name.split(" ").slice(0, 3).join(" ")}</div>
                    <div className="text-[11px]" style={{ color: "var(--text-secondary)" }}>
                      {pct}% actual / {target}% target
                      <span style={{ color: delta >= 0 ? "var(--green)" : "var(--red)", marginLeft: 4 }}>
                        {delta >= 0 ? "+" : ""}{delta.toFixed(0)}pp
                      </span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Needs Your Attention */}
      {data.open_questions && data.open_questions.length > 0 && (
        <div>
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-[16px] font-semibold">Needs Your Attention</h2>
            <Link href="/decisions" className="text-[13px] font-medium" style={{ color: "var(--accent-blue)" }}>View all &rarr;</Link>
          </div>
          <div className="space-y-2">
            {data.open_questions.filter(q => q.urgency === "high").slice(0, 3).map((q) => (
              <QuestionCard key={q.id} question={q} />
            ))}
          </div>
        </div>
      )}

      {/* Key Decisions */}
      {data.recent_decisions && data.recent_decisions.length > 0 && (
        <div>
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-[16px] font-semibold flex items-center gap-2">
              <span style={{ color: "var(--ai-teal)" }}>{"\u2726"}</span> Key Decisions
            </h2>
            <Link href="/decisions" className="text-[13px] font-medium" style={{ color: "var(--accent-blue)" }}>View all &rarr;</Link>
          </div>
          <div className="space-y-2">
            {data.recent_decisions.slice(0, 4).map((d) => (
              <DecisionCard key={d.id} decision={d} />
            ))}
          </div>
        </div>
      )}

      {/* Coaching */}
      {data.recommendations && data.recommendations.length > 0 && (
        <div>
          <h2 className="text-[16px] font-semibold mb-3">This Week&apos;s Coaching</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {data.recommendations.slice(0, 3).map((rec, i) => (
              <RecCard key={i} rec={rec} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
