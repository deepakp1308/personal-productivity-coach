"use client";
import { useEffect, useState } from "react";
import { getWeeklySnapshots, getRecommendations, WeeklySnapshot, Recommendation } from "@/lib/api";

const PRIORITY_COLORS: Record<string, string> = {
  "Advanced Analytics & AI-Powered Insights": "var(--chart-navy)",
  "Platform Intelligence Across MC & QBO": "var(--chart-blue)",
  "Trusted Data Foundation & Quality at Scale": "var(--chart-teal)",
  "Leadership & Strategic Investments": "var(--warning)",
  "Other": "var(--chart-pink)",
};

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
      {rec.judge_score != null && (
        <div className="mt-2 text-[11px]" style={{ color: "var(--text-secondary)" }}>Judge: {rec.judge_score}/5</div>
      )}
    </div>
  );
}

export default function WeeklyReviewPage() {
  const [snapshots, setSnapshots] = useState<WeeklySnapshot[]>([]);
  const [recs, setRecs] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      getWeeklySnapshots(8).then(setSnapshots),
      getRecommendations().then(setRecs),
    ]).catch(() => {}).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="p-8 text-[14px]" style={{ color: "var(--text-secondary)" }}>Loading weekly review...</div>;

  const latest = snapshots[0];

  return (
    <div className="p-6 max-w-[1200px] mx-auto space-y-6">
      <div>
        <h1 className="text-[24px] font-semibold flex items-center gap-2">
          <span style={{ color: "var(--ai-teal)" }}>{"\u2726"}</span> Weekly Review
        </h1>
        <p className="text-[13px] mt-1" style={{ color: "var(--text-secondary)" }}>
          {latest ? `Week ${latest.week_iso}` : "No weekly data yet. Run the pipeline to generate a review."}
        </p>
      </div>

      {latest && (
        <>
          {/* Summary cards */}
          <div className="grid grid-cols-3 gap-4">
            <div className="card p-5">
              <div className="text-[12px] font-medium" style={{ color: "var(--text-secondary)" }}>Priority Alignment</div>
              <div className="text-[28px] font-semibold mt-1" style={{ color: latest.alignment_pct >= 70 ? "var(--green)" : "var(--warning)" }}>
                {latest.alignment_pct}%
              </div>
            </div>
            <div className="card p-5">
              <div className="text-[12px] font-medium" style={{ color: "var(--text-secondary)" }}>Meeting Hours</div>
              <div className="text-[28px] font-semibold mt-1">{latest.meeting_hours}h</div>
            </div>
            <div className="card p-5">
              <div className="text-[12px] font-medium" style={{ color: "var(--text-secondary)" }}>Fragmentation</div>
              <div className="text-[28px] font-semibold mt-1">{latest.fragmentation_score}</div>
              <div className="text-[11px]" style={{ color: "var(--text-secondary)" }}>switches/hr</div>
            </div>
          </div>

          {/* Priority breakdown */}
          <div className="card p-5">
            <h2 className="text-[16px] font-semibold mb-3">Priority Breakdown</h2>
            <div className="flex h-3 rounded-full overflow-hidden bg-gray-100 mb-3">
              {Object.entries(latest.priority_breakdown).map(([name, pct]) => (
                <div key={name} style={{ width: `${pct}%`, background: PRIORITY_COLORS[name] || "var(--chart-pink)" }} />
              ))}
            </div>
            <div className="space-y-2">
              {Object.entries(latest.priority_breakdown).map(([name, pct]) => (
                <div key={name} className="flex items-center gap-3">
                  <span className="w-3 h-3 rounded-full" style={{ background: PRIORITY_COLORS[name] || "var(--chart-pink)" }} />
                  <span className="text-[13px] flex-1">{name}</span>
                  <span className="text-[13px] font-semibold">{pct}%</span>
                </div>
              ))}
            </div>
          </div>

          {/* Insight */}
          {latest.top_insight && (
            <div className="card p-5 flex items-start gap-3" style={{ borderLeft: "3px solid var(--ai-teal)" }}>
              <span style={{ color: "var(--ai-teal)", fontSize: 18 }}>{"\u2726"}</span>
              <div className="text-[13px]" style={{ color: "var(--text-secondary)" }}>{latest.top_insight}</div>
            </div>
          )}
        </>
      )}

      {/* Recommendations */}
      {recs.length > 0 && (
        <div>
          <h2 className="text-[16px] font-semibold mb-3">Coaching Recommendations</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {recs.slice(0, 3).map((rec, i) => (
              <RecCard key={i} rec={rec} />
            ))}
          </div>
        </div>
      )}

      {/* Trend */}
      {snapshots.length > 1 && (
        <div className="card p-5">
          <h2 className="text-[16px] font-semibold mb-3">Alignment Trend</h2>
          <div className="flex items-end gap-2 h-[120px]">
            {snapshots.slice().reverse().map((s) => (
              <div key={s.week_iso} className="flex-1 flex flex-col items-center gap-1">
                <div className="text-[11px] font-medium" style={{ color: s.alignment_pct >= 70 ? "var(--green)" : "var(--warning)" }}>
                  {s.alignment_pct}%
                </div>
                <div
                  className="w-full rounded-t"
                  style={{
                    height: `${Math.max(s.alignment_pct, 5)}%`,
                    background: s.alignment_pct >= 70 ? "var(--chart-teal)" : "var(--chart-pink)",
                    minHeight: 4,
                  }}
                />
                <div className="text-[10px]" style={{ color: "var(--text-secondary)" }}>
                  {s.week_iso.split("-W")[1] ? `W${s.week_iso.split("-W")[1]}` : s.week_iso}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
