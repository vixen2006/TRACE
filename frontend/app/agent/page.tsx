"use client";
import { useState, useRef, useEffect } from "react";
import { Send, Bot, Zap, CheckCircle, AlertTriangle, Clock, Search, FileText } from "lucide-react";

type EventType = "run_started" | "tool_started" | "tool_completed" | "tool_error" | "evidence_found" | "claim_flagged" | "limit_reached" | "run_completed" | "model_finished";

interface AgentEvent {
  id: number;
  type: EventType;
  message: string;
  tool?: string;
  timestamp: Date;
}

const SAVED_GOALS = [
  "What did I ship this week?",
  "Prepare my one-to-one notes for this month.",
  "Which projects best demonstrate system design?",
  "Build five interview stories from my verified work.",
  "Find claims in my profile that lack sufficient evidence.",
];

const DEMO_EVENTS: AgentEvent[] = [
  { id: 1, type: "run_started",    message: "Interpreting the reporting period: Oct 3 – Oct 10.", timestamp: new Date() },
  { id: 2, type: "tool_started",  message: "Calling list_repositories", tool: "list_repositories", timestamp: new Date() },
  { id: 3, type: "tool_completed",message: "Found 14 accessible repositories.", tool: "list_repositories", timestamp: new Date() },
  { id: 4, type: "tool_started",  message: "Calling fetch_pull_requests — auth-service", tool: "fetch_pull_requests", timestamp: new Date() },
  { id: 5, type: "tool_completed",message: "Retrieved 4 PRs. 3 merged, 1 open.", tool: "fetch_pull_requests", timestamp: new Date() },
  { id: 6, type: "tool_started",  message: "Calling fetch_reviews — PR #248", tool: "fetch_reviews", timestamp: new Date() },
  { id: 7, type: "tool_completed",message: "Review records confirm authorship on PR #248.", tool: "fetch_reviews", timestamp: new Date() },
  { id: 8, type: "claim_flagged", message: "Claim 'deployed to production' has no deployment evidence. Held for review.", timestamp: new Date() },
  { id: 9, type: "evidence_found",message: "5 contribution claims validated with source links.", timestamp: new Date() },
  { id: 10,type: "run_completed", message: "Investigation complete. Report ready.", timestamp: new Date() },
];

function eventIcon(type: EventType) {
  switch (type) {
    case "tool_started":   return <Clock size={13} color="var(--text-muted)" />;
    case "tool_completed": return <CheckCircle size={13} color="var(--success)" />;
    case "tool_error":     return <AlertTriangle size={13} color="var(--error)" />;
    case "claim_flagged":  return <AlertTriangle size={13} color="var(--accent)" />;
    case "run_completed":  return <CheckCircle size={13} color="var(--success)" />;
    case "evidence_found": return <Search size={13} color="var(--text-secondary)" />;
    default:               return <Bot size={13} color="var(--accent)" />;
  }
}

function dotClass(type: EventType) {
  if (type === "tool_completed" || type === "run_completed" || type === "evidence_found") return "event-dot-done";
  if (type === "claim_flagged" || type === "tool_error") return "event-dot-error";
  if (type === "tool_started" || type === "run_started") return "event-dot-running";
  return "event-dot-default";
}

export default function AgentPage() {
  const [goal, setGoal] = useState("");
  const [events, setEvents] = useState<AgentEvent[]>([]);
  const [running, setRunning] = useState(false);
  const timelineRef = useRef<HTMLDivElement>(null);

  const runDemo = async () => {
    if (!goal.trim() || running) return;
    setRunning(true);
    setEvents([]);
    for (let i = 0; i < DEMO_EVENTS.length; i++) {
      await new Promise(r => setTimeout(r, 500 + Math.random() * 400));
      setEvents(prev => [...prev, { ...DEMO_EVENTS[i], timestamp: new Date() }]);
    }
    setRunning(false);
  };

  useEffect(() => {
    if (timelineRef.current) timelineRef.current.scrollTop = timelineRef.current.scrollHeight;
  }, [events]);

  return (
    <div style={{ maxWidth: 1200, margin: "0 auto" }}>
      <div style={{ marginBottom: 24 }}>
        <div style={{ fontSize: 11, color: "var(--accent)", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: 6 }}>
          Agent Workspace
        </div>
        <h1>Investigation Console</h1>
        <p style={{ color: "var(--text-secondary)", fontSize: 13, marginTop: 4 }}>
          Define a goal, watch the agent investigate, verify evidence, and generate a trusted report.
        </p>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "220px 1fr 280px", gap: 16, minHeight: 600 }}>
        {/* Left: Goals */}
        <div className="card" style={{ padding: 16 }}>
          <div className="section-label" style={{ marginBottom: 12 }}>Saved Goals</div>
          <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            {SAVED_GOALS.map((g, i) => (
              <button key={i} onClick={() => setGoal(g)}
                style={{
                  background: goal === g ? "var(--elevated)" : "transparent",
                  border: goal === g ? "1px solid var(--border)" : "1px solid transparent",
                  borderRadius: 6, padding: "8px 10px", color: "var(--text-secondary)",
                  fontSize: 12, textAlign: "left", cursor: "pointer", lineHeight: 1.4,
                  transition: "all 150ms"
                }}>
                {g}
              </button>
            ))}
          </div>

          <div className="divider" />
          <div className="section-label">Recent Runs</div>
          {["Weekly summary", "1:1 prep", "Interview stories"].map((r, i) => (
            <div key={i} style={{ fontSize: 12, color: "var(--text-muted)", padding: "6px 0", borderBottom: "1px solid var(--border)", display: "flex", justifyContent: "space-between" }}>
              <span>{r}</span>
              <span style={{ fontSize: 10 }}>Oct {9-i}</span>
            </div>
          ))}
        </div>

        {/* Center: Task + Timeline */}
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          {/* Input */}
          <div className="card" style={{ padding: 16 }}>
            <div className="section-label" style={{ marginBottom: 8 }}>Investigation Goal</div>
            <textarea
              className="input"
              rows={3}
              placeholder="e.g. What did I ship this week? · Prepare my 1:1 notes · Build interview stories from verified work"
              value={goal}
              onChange={e => setGoal(e.target.value)}
              style={{ marginBottom: 10 }}
            />
            <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
              <input type="date" className="input" style={{ width: 140 }} defaultValue="2026-10-03" />
              <span style={{ color: "var(--text-muted)", fontSize: 12 }}>to</span>
              <input type="date" className="input" style={{ width: 140 }} defaultValue="2026-10-10" />
              <button className="btn btn-primary" onClick={runDemo} disabled={!goal.trim() || running}
                style={{ marginLeft: "auto", opacity: (!goal.trim() || running) ? 0.5 : 1 }}>
                {running ? <><span style={{ animation: "pulse 1.5s infinite" }}>●</span> Running...</> : <><Zap size={13} /> Investigate</>}
              </button>
            </div>
          </div>

          {/* Execution timeline */}
          <div className="card" style={{ flex: 1, display: "flex", flexDirection: "column" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
              <div>
                <div className="section-label">Execution Timeline</div>
                <h3>Tool calls and outcomes · Real-time</h3>
              </div>
              {running && (
                <span className="badge badge-red">
                  <span style={{ display: "inline-block", width: 6, height: 6, borderRadius: "50%", background: "var(--accent)", animation: "pulse 1.5s infinite" }} />
                  Running
                </span>
              )}
            </div>

            <div ref={timelineRef} style={{ flex: 1, overflowY: "auto", minHeight: 300, maxHeight: 400 }}>
              {events.length === 0 && !running && (
                <div style={{ textAlign: "center", padding: "48px 24px", color: "var(--text-muted)" }}>
                  <Bot size={32} style={{ marginBottom: 12, opacity: 0.4 }} />
                  <p style={{ fontSize: 13 }}>Set a goal and click Investigate to start the agent.</p>
                </div>
              )}
              {events.map(ev => (
                <div key={ev.id} className="agent-event">
                  <div className={`event-dot ${dotClass(ev.type)}`} />
                  <div style={{ flex: 1 }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 2 }}>
                      {eventIcon(ev.type)}
                      {ev.tool && <span className="hash">{ev.tool}</span>}
                    </div>
                    <div style={{ fontSize: 13, color: ev.type === "claim_flagged" ? "var(--accent)" : "var(--text-primary)" }}>
                      {ev.message}
                    </div>
                    <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 2, fontFamily: "var(--mono)" }}>
                      {ev.timestamp.toLocaleTimeString()}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right: Evidence + Preview */}
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          <div className="card" style={{ padding: 16 }}>
            <div className="section-label" style={{ marginBottom: 12 }}>Evidence Collected</div>
            {events.length === 0 ? (
              <div style={{ color: "var(--text-muted)", fontSize: 12, textAlign: "center", padding: "24px 0" }}>No evidence yet</div>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                {["auth-service#pr:248", "auth-service#pr:251", "payment-svc#pr:183", "data-pipeline@a3f9c1b2"].map((src, i) => (
                  <div key={i} style={{ display: "flex", alignItems: "center", gap: 8, padding: "6px 8px", background: "var(--elevated)", borderRadius: 6 }}>
                    <CheckCircle size={12} color="var(--success)" />
                    <span className="hash" style={{ background: "none", padding: 0, fontSize: 11 }}>{src}</span>
                  </div>
                ))}
                <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "6px 8px", background: "var(--accent-dim)", borderRadius: 6, border: "1px solid rgba(227,41,54,0.25)" }}>
                  <AlertTriangle size={12} color="var(--accent)" />
                  <span style={{ fontSize: 11, color: "var(--accent)" }}>1 claim needs evidence</span>
                </div>
              </div>
            )}
          </div>

          <div className="card" style={{ padding: 16, flex: 1 }}>
            <div className="section-label" style={{ marginBottom: 12 }}>Report Preview</div>
            {events.some(e => e.type === "run_completed") ? (
              <div>
                <div style={{ fontSize: 13, color: "var(--text-primary)", marginBottom: 12, lineHeight: 1.6 }}>
                  <strong>5 contributions verified</strong><br />
                  <span style={{ color: "var(--text-secondary)" }}>3 merged · 1 in progress · 1 held</span>
                </div>
                <div className="gap-item" style={{ marginBottom: 12 }}>
                  <AlertTriangle size={14} color="var(--accent)" style={{ flexShrink: 0, marginTop: 1 }} />
                  <div style={{ fontSize: 12 }}>
                    <div style={{ fontWeight: 600, color: "var(--accent)", marginBottom: 2 }}>Evidence gap</div>
                    <div style={{ color: "var(--text-secondary)" }}>'Deployed to production' claim lacks deployment evidence.</div>
                  </div>
                </div>
                <button className="btn btn-primary" style={{ width: "100%", justifyContent: "center", fontSize: 12 }}>
                  <FileText size={13} /> View full report
                </button>
              </div>
            ) : (
              <div style={{ color: "var(--text-muted)", fontSize: 12, textAlign: "center", padding: "24px 0" }}>
                Report will appear here after investigation completes.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
