/**
 * API client for the Personal Productivity Coach.
 *
 * Read-only data: always served from static JSON in public/api/
 * (works on GitHub Pages, Netlify, and local dev with no backend).
 *
 * Chat/write operations: hit the live backend on localhost:8001
 * (only available when running the FastAPI server locally).
 */

const BACKEND_URL = "http://localhost:8001";

async function fetchJSON<T>(path: string): Promise<T> {
  // Strip "/api" prefix and add ".json" to get the static file path
  const endpoint = path.replace(/^\/api/, "").replace(/\?.*$/, "");
  const staticPath = `/api${endpoint}.json`;

  // Always try static JSON first (works everywhere)
  try {
    const res = await fetch(staticPath);
    if (res.ok) return res.json();
  } catch {}

  // Fallback: try live backend (only works when server is running)
  try {
    const res = await fetch(`${BACKEND_URL}${path}`);
    if (res.ok) return res.json();
  } catch {}

  throw new Error(`Failed to fetch ${path}`);
}

// ── Types ────────────────────────────────────────────────────────────────────

export interface DashboardData {
  total_activities: number;
  alignment_pct: number;
  meeting_hours: number;
  fragmentation_score: number;
  source_breakdown: Record<string, number>;
  type_breakdown: Record<string, number>;
  priority_breakdown: Record<string, number>;
  priority_targets: Record<string, number>;
  open_questions_count: number;
  total_hours: number;
  top_priority: string;
  top_insight: string;
  recommendations: Recommendation[];
  anomalies: Anomaly[];
  recent_decisions: Decision[];
  open_questions: OpenQuestion[];
  messages: number;
  emails: number;
  meetings: number;
}

export interface Recommendation {
  id?: number;
  week_iso?: string;
  kind: string;
  action: string;
  rationale: string;
  evidence_ids: number[];
  judge_score?: number;
  judge_reasoning?: string;
  status?: string;
}

export interface Anomaly {
  type: string;
  severity: string;
  message: string;
}

export interface Decision {
  id: number;
  description: string;
  channel: string;
  related_priority?: string;
  stakeholders: string[];
  decided_at: string;
}

export interface OpenQuestion {
  id: number;
  description: string;
  urgency: string;
  owner: string;
  channel: string;
  related_priority?: string;
  status: string;
  created_at: string;
  resolved_at?: string;
}

export interface Priority {
  id: number;
  name: string;
  description: string;
  weight: number;
  pillar: number;
  active: number;
}

export interface WeeklySnapshot {
  id: number;
  week_iso: string;
  alignment_pct: number;
  meeting_hours: number;
  fragmentation_score: number;
  type_breakdown: Record<string, number>;
  priority_breakdown: Record<string, number>;
  recommendations_json: Recommendation[];
  top_insight: string;
}

export interface ChatResponse {
  response: string;
  context: { session_id: string };
}

// ── Fetchers ─────────────────────────────────────────────────────────────────

export async function getDashboard(): Promise<DashboardData> {
  return fetchJSON("/api/dashboard");
}

export async function getActivities(params?: Record<string, string>): Promise<any[]> {
  const qs = params ? "?" + new URLSearchParams(params).toString() : "";
  return fetchJSON(`/api/activities${qs}`);
}

export async function getPriorities(): Promise<Priority[]> {
  return fetchJSON("/api/priorities");
}

export async function getRecommendations(weekIso?: string): Promise<Recommendation[]> {
  const qs = weekIso ? `?week_iso=${weekIso}` : "";
  return fetchJSON(`/api/recommendations${qs}`);
}

export async function getDecisions(): Promise<Decision[]> {
  return fetchJSON("/api/decisions");
}

export async function getOpenQuestions(status?: string): Promise<OpenQuestion[]> {
  const qs = status ? `?status=${status}` : "";
  return fetchJSON(`/api/questions${qs}`);
}

export async function getWeeklySnapshots(limit?: number): Promise<WeeklySnapshot[]> {
  const qs = limit ? `?limit=${limit}` : "";
  return fetchJSON(`/api/weekly${qs}`);
}

export async function getMetrics(period?: string): Promise<any> {
  const qs = period ? `?period=${period}` : "";
  return fetchJSON(`/api/metrics${qs}`);
}

export async function sendChatMessage(message: string, sessionId?: string): Promise<ChatResponse> {
  try {
    const res = await fetch(`${BACKEND_URL}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, session_id: sessionId }),
    });
    if (!res.ok) throw new Error("Chat request failed");
    return res.json();
  } catch {
    return {
      response: "The backend server isn't running. Start it with:\n\n`cd /Users/dprabhakara/ai_workspace/personal-coach && python3 -m backend.main --serve`\n\nThen try again.",
      context: { session_id: sessionId || "offline" },
    };
  }
}
