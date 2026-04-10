"use client";
import { useEffect, useState } from "react";
import { getPriorities, Priority } from "@/lib/api";

const PILLAR_COLORS: Record<number, string> = {
  1: "var(--chart-teal)",
  2: "var(--chart-navy)",
  3: "var(--chart-blue)",
};

export default function PrioritiesPage() {
  const [priorities, setPriorities] = useState<Priority[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getPriorities().then(setPriorities).catch(() => {}).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="p-8 text-[14px]" style={{ color: "var(--text-secondary)" }}>Loading priorities...</div>;

  const totalWeight = priorities.reduce((sum, p) => sum + p.weight, 0);

  return (
    <div className="p-6 max-w-[1200px] mx-auto space-y-6">
      <div>
        <h1 className="text-[24px] font-semibold">FY26 Q4 Priorities</h1>
        <p className="text-[13px] mt-1" style={{ color: "var(--text-secondary)" }}>
          Your strategic pillars and target time allocation from the R&A Q4 Roadmap.
        </p>
      </div>

      {/* Weight visualization */}
      <div className="card p-5">
        <h2 className="text-[16px] font-semibold mb-3">Target Allocation</h2>
        <div className="flex h-4 rounded-full overflow-hidden bg-gray-100 mb-4">
          {priorities.map((p) => (
            <div
              key={p.id}
              style={{ width: `${(p.weight / totalWeight) * 100}%`, background: PILLAR_COLORS[p.pillar] || "var(--chart-pink)" }}
              title={`${p.name}: ${(p.weight * 100).toFixed(0)}%`}
            />
          ))}
        </div>
      </div>

      {/* Priority cards */}
      <div className="space-y-4">
        {priorities.map((p) => (
          <div key={p.id} className="card p-5" style={{ borderLeft: `3px solid ${PILLAR_COLORS[p.pillar] || "var(--border)"}` }}>
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-[11px] px-2 py-0.5 rounded-full font-medium"
                    style={{ background: "rgba(0,185,169,0.08)", color: "var(--ai-teal)" }}>
                    Pillar {p.pillar}
                  </span>
                  <h3 className="text-[14px] font-semibold">{p.name}</h3>
                </div>
                <p className="text-[13px] mt-1" style={{ color: "var(--text-secondary)" }}>{p.description}</p>
              </div>
              <div className="text-right ml-4">
                <div className="text-[28px] font-semibold" style={{ color: PILLAR_COLORS[p.pillar] }}>
                  {(p.weight * 100).toFixed(0)}%
                </div>
                <div className="text-[11px]" style={{ color: "var(--text-secondary)" }}>target</div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Key dates */}
      <div className="card p-5">
        <h2 className="text-[16px] font-semibold mb-3">Key Q4 Dates</h2>
        <div className="space-y-2">
          <div className="flex items-center gap-3 text-[13px]">
            <span className="w-2 h-2 rounded-full" style={{ background: "var(--chart-blue)" }} />
            <span className="font-medium">Early May</span>
            <span style={{ color: "var(--text-secondary)" }}>Phase 1 GBSG BI Platform (Email + SMS + Marketing ROI)</span>
          </div>
          <div className="flex items-center gap-3 text-[13px]">
            <span className="w-2 h-2 rounded-full" style={{ background: "var(--chart-navy)" }} />
            <span className="font-medium">July</span>
            <span style={{ color: "var(--text-secondary)" }}>WhatsApp GA Target</span>
          </div>
          <div className="flex items-center gap-3 text-[13px]">
            <span className="w-2 h-2 rounded-full" style={{ background: "var(--chart-teal)" }} />
            <span className="font-medium">30-day target</span>
            <span style={{ color: "var(--text-secondary)" }}>Zero data inaccuracy VOCs</span>
          </div>
        </div>
      </div>
    </div>
  );
}
