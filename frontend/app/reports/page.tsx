"use client";
import { useState } from "react";
import { Download, CheckCircle, AlertTriangle, ArrowRight } from "lucide-react";

const TABS = ["Weekly Summary", "1:1 Talking Points", "Performance Review", "Interview Stories", "CSV Export"];

const WEEKLY_REPORT = {
  period: "Oct 3 – Oct 10, 2026",
  shipped: [
    { title: "JWT refresh token rotation with revocation", repo: "auth-service", pr: "#248", confidence: 0.97 },
    { title: "Payment idempotency key validation",         repo: "payment-svc",  pr: "#183", confidence: 0.95 },
    { title: "Auth latency reduced via Redis key caching", repo: "auth-service", pr: "#251", confidence: 0.92 },
    { title: "Terraform provider migration v4 → v5",       repo: "infra-tf",     pr: "#41",  confidence: 0.89 },
  ],
  in_progress: [
    { title: "Async request handler migration", repo: "api-gateway",   pr: "#71" },
    { title: "Kafka streaming consumer",        repo: "data-pipeline", pr: "#66" },
  ],
  decisions: [
    { title: "Selected Kafka over RabbitMQ for event pipeline", context: "ADR recorded in data-pipeline/docs" },
  ],
  problems: [
    { title: "Diagnosed race condition in token refresh", outcome: "Resolved with optimistic locking on session table" },
  ],
  gaps: [
    { claim: "Auth service deployed to production", reason: "Deployment evidence not found. PR merge is not deployment proof." },
  ],
  blockers: [],
};

const ONE_TO_ONE = [
  { topic: "Shipped: JWT security hardening", detail: "Completed token rotation and revocation across auth-service. Evidence: PR #248, #251." },
  { topic: "In progress: API gateway async refactor", detail: "PR #71 open. Blocking on review from @team-lead. ETA: Oct 14." },
  { topic: "Decision: Kafka adoption", detail: "ADR written and reviewed. Implementation beginning next sprint." },
  { topic: "Growth: Mentoring", detail: "Ran 2 design review sessions this week. Junior engineers are onboarded to auth patterns." },
  { topic: "Flag: Evidence gap", detail: "Deployment claim for auth-service lacks production evidence. Will not include in report until resolved." },
];

const INTERVIEW_STORIES = [
  {
    title: "Preventing duplicate payment charges at scale",
    situation: "Payment service was processing duplicate charges on client retries.",
    task: "Diagnose the root cause and implement a durable fix without downtime.",
    action: "Root-caused to missing idempotency handling; added idempotency key validation with 24h TTL in Redis and DB fallback.",
    result: "Zero duplicate charges reported post-deployment. PR #183 — auth-service. Confidence: 95%.",
  },
  {
    title: "Reducing authentication latency by 40%",
    situation: "JWT validation taking 180ms avg due to repeated RSA public key fetches.",
    task: "Identify bottleneck and reduce without compromising security.",
    action: "Introduced Redis-based public key caching with short TTL. Added cache invalidation on key rotation.",
    result: "Latency reduced from 180ms to 105ms. Evidence: PR #251, performance benchmark in PR description.",
  },
];

function ConfidenceBar({ value }: { value: number }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
      <div style={{ height: 4, width: 60, background: "var(--border)", borderRadius: 2, overflow: "hidden" }}>
        <div style={{ height: "100%", width: `${value * 100}%`, background: value > 0.9 ? "var(--success)" : value > 0.7 ? "#f59e0b" : "var(--accent)", borderRadius: 2, transition: "width 500ms ease" }} />
      </div>
      <span style={{ fontSize: 11, color: "var(--text-muted)", fontFamily: "var(--mono)" }}>{Math.round(value * 100)}%</span>
    </div>
  );
}

export default function ReportsPage() {
  const [tab, setTab] = useState(0);

  return (
    <div style={{ maxWidth: 1100, margin: "0 auto" }}>
      <div style={{ marginBottom: 24 }}>
        <div style={{ fontSize: 11, color: "var(--accent)", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: 6 }}>Reports</div>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end" }}>
          <div>
            <h1>Engineering Reports</h1>
            <p style={{ color: "var(--text-secondary)", fontSize: 13, marginTop: 4 }}>Source-linked. Verified. A quiet week is reported honestly.</p>
          </div>
          <button className="btn btn-primary"><Download size={13} /> Export PDF</button>
        </div>
      </div>

      {/* Tabs */}
      <div style={{ display: "flex", gap: 2, marginBottom: 24, background: "var(--surface)", padding: 4, borderRadius: "var(--radius-lg)", border: "1px solid var(--border)", width: "fit-content" }}>
        {TABS.map((t, i) => (
          <button key={i} onClick={() => setTab(i)} style={{
            padding: "7px 16px", borderRadius: 8, border: "none", cursor: "pointer",
            background: tab === i ? "var(--elevated)" : "transparent",
            color: tab === i ? "var(--text-primary)" : "var(--text-muted)",
            fontSize: 13, fontWeight: tab === i ? 600 : 400, transition: "all 150ms",
          }}>{t}</button>
        ))}
      </div>

      {/* Weekly Summary */}
      {tab === 0 && (
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 20, padding: "10px 16px", background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 8 }}>
            <CheckCircle size={14} color="var(--success)" />
            <span style={{ fontSize: 13, color: "var(--text-secondary)" }}>Report period: <strong style={{ color: "var(--text-primary)" }}>{WEEKLY_REPORT.period}</strong></span>
            <span style={{ fontSize: 11, color: "var(--text-muted)", marginLeft: "auto" }}>Generated by TRACE agent run #7 · Evidence verified</span>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20, marginBottom: 20 }}>
            {/* Shipped */}
            <div className="card">
              <div className="section-label" style={{ marginBottom: 12 }}>✓ Shipped</div>
              <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                {WEEKLY_REPORT.shipped.map((s, i) => (
                  <div key={i} style={{ padding: "10px 12px", background: "var(--elevated)", borderRadius: 8 }}>
                    <div style={{ fontSize: 13, color: "var(--text-primary)", fontWeight: 500, marginBottom: 4 }}>{s.title}</div>
                    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                      <span className="hash">{s.repo}</span>
                      <span className="hash">{s.pr}</span>
                      <ConfidenceBar value={s.confidence} />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* In progress + decisions */}
            <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
              <div className="card">
                <div className="section-label" style={{ marginBottom: 12 }}>→ In Progress</div>
                {WEEKLY_REPORT.in_progress.map((s, i) => (
                  <div key={i} style={{ padding: "8px 0", borderBottom: i < WEEKLY_REPORT.in_progress.length - 1 ? "1px solid var(--border)" : "none" }}>
                    <div style={{ fontSize: 13, color: "var(--text-primary)" }}>{s.title}</div>
                    <div style={{ display: "flex", gap: 6, marginTop: 4 }}>
                      <span className="hash">{s.repo}</span>
                      <span className="hash">{s.pr}</span>
                      <span className="badge badge-open" style={{ fontSize: 10 }}>open</span>
                    </div>
                  </div>
                ))}
              </div>
              <div className="card">
                <div className="section-label" style={{ marginBottom: 12 }}>◆ Decisions Made</div>
                {WEEKLY_REPORT.decisions.map((d, i) => (
                  <div key={i} style={{ fontSize: 13 }}>
                    <div style={{ color: "var(--text-primary)", marginBottom: 4 }}>{d.title}</div>
                    <div style={{ color: "var(--text-muted)", fontSize: 12 }}>{d.context}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Evidence gaps */}
          {WEEKLY_REPORT.gaps.length > 0 && (
            <div className="card" style={{ borderColor: "rgba(227,41,54,0.3)" }}>
              <div style={{ display: "flex", gap: 8, marginBottom: 12, alignItems: "center" }}>
                <AlertTriangle size={14} color="var(--accent)" />
                <div className="section-label" style={{ margin: 0, color: "var(--accent)" }}>Evidence Gaps — Held from Report</div>
              </div>
              {WEEKLY_REPORT.gaps.map((g, i) => (
                <div key={i} className="gap-item">
                  <AlertTriangle size={14} color="var(--accent)" style={{ flexShrink: 0, marginTop: 1 }} />
                  <div>
                    <div style={{ fontSize: 13, fontWeight: 600, color: "var(--text-primary)", marginBottom: 2 }}>{g.claim}</div>
                    <div style={{ fontSize: 12, color: "var(--text-secondary)" }}>{g.reason}</div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* 1:1 Talking Points */}
      {tab === 1 && (
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {ONE_TO_ONE.map((item, i) => (
            <div key={i} className="card">
              <div style={{ display: "flex", gap: 12 }}>
                <div style={{ width: 28, height: 28, background: "var(--elevated)", borderRadius: 6, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0, fontSize: 12, fontWeight: 700, color: "var(--accent)" }}>
                  {i + 1}
                </div>
                <div>
                  <div style={{ fontSize: 13, fontWeight: 600, color: "var(--text-primary)", marginBottom: 4 }}>{item.topic}</div>
                  <div style={{ fontSize: 13, color: "var(--text-secondary)", lineHeight: 1.6 }}>{item.detail}</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Interview Stories */}
      {tab === 3 && (
        <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
          {INTERVIEW_STORIES.map((story, i) => (
            <div key={i} className="card">
              <h3 style={{ marginBottom: 16 }}>{story.title}</h3>
              {(["situation", "task", "action", "result"] as const).map(key => (
                <div key={key} style={{ display: "flex", gap: 12, marginBottom: 12 }}>
                  <div style={{ width: 72, fontSize: 10, fontWeight: 700, color: "var(--accent)", textTransform: "uppercase", letterSpacing: "0.08em", paddingTop: 2, flexShrink: 0 }}>
                    {key}
                  </div>
                  <div style={{ fontSize: 13, color: "var(--text-secondary)", lineHeight: 1.6 }}>{story[key]}</div>
                </div>
              ))}
            </div>
          ))}
        </div>
      )}

      {/* Placeholder tabs */}
      {(tab === 2 || tab === 4) && (
        <div style={{ textAlign: "center", padding: "64px 24px", color: "var(--text-muted)" }}>
          <div style={{ fontSize: 32, marginBottom: 12 }}>{tab === 4 ? "↓" : "◑"}</div>
          <p style={{ fontSize: 14 }}>{tab === 4 ? "CSV export available after connecting GitHub." : "Performance review material generated from verified contributions."}</p>
          <button className="btn btn-ghost" style={{ marginTop: 16 }}>Connect GitHub <ArrowRight size={13} /></button>
        </div>
      )}
    </div>
  );
}
