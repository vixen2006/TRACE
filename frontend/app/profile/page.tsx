"use client";
import { useState } from "react";
import { CheckCircle, AlertTriangle, Clock, ChevronRight, ExternalLink } from "lucide-react";

const SECTIONS = [
  {
    id: "projects",
    label: "Projects",
    items: [
      { title: "auth-service JWT rotation", project: "auth-service", date: "Oct 2026", status: "verified", summary: "Designed and implemented JWT refresh token rotation with database-backed revocation list." },
      { title: "payment-svc idempotency", project: "payment-svc",   date: "Sep 2026", status: "verified", summary: "Resolved duplicate payment processing by adding idempotency keys at the API layer." },
      { title: "data-pipeline streaming",  project: "data-pipeline", date: "Sep 2026", status: "pending", summary: "Migrating batch jobs to streaming architecture using Kafka consumers." },
    ],
  },
  {
    id: "problems",
    label: "Problems Solved",
    items: [
      { title: "Eliminated payment duplicate charges", project: "payment-svc", date: "Sep 2026", status: "verified", summary: "Root-caused intermittent duplicate charge issue to race condition in order service. Resolved with distributed locks." },
      { title: "Reduced auth latency by 40%",          project: "auth-service",date: "Aug 2026", status: "verified", summary: "Profiled token validation bottleneck; introduced Redis caching for public key lookups." },
    ],
  },
  {
    id: "decisions",
    label: "Decisions",
    items: [
      { title: "Adopted Kafka for pipeline events", project: "data-pipeline", date: "Sep 2026", status: "verified", summary: "Evaluated RabbitMQ vs Kafka for event streaming; selected Kafka for throughput and retention guarantees." },
    ],
  },
  {
    id: "invisible",
    label: "Invisible Work",
    items: [
      { title: "Mentored two junior engineers on system design", project: "auth-service", date: "Oct 2026", status: "pending", summary: "Conducted bi-weekly design reviews and code walkthroughs." },
      { title: "Improved CI pipeline reliability",              project: "infra-tf",       date: "Sep 2026", status: "verified", summary: "Flaky test investigation and Terraform pipeline stabilisation." },
    ],
  },
  {
    id: "skills",
    label: "Skills Demonstrated",
    items: [
      { title: "Distributed systems design",  project: "data-pipeline", date: "2026", status: "verified", summary: "Streaming architecture, Kafka topic partitioning, consumer group coordination." },
      { title: "Security engineering",        project: "auth-service",  date: "2026", status: "verified", summary: "JWT lifecycle, token revocation, PKCE implementation." },
      { title: "Infrastructure as code",      project: "infra-tf",      date: "2026", status: "verified", summary: "Terraform module authoring, state management, drift detection." },
    ],
  },
  {
    id: "improvements",
    label: "Improvement Areas",
    items: [
      { title: "Observability and tracing setup",    project: "api-gateway",  date: "Oct 2026", status: "pending", summary: "Structured logging implemented; distributed tracing not yet established." },
    ],
  },
  {
    id: "gaps",
    label: "Evidence Gaps",
    items: [
      { title: "'Deployed to production' claim",    project: "auth-service", date: "Oct 2026", status: "gap", summary: "Claim requires deployment evidence (CI/CD logs, release tag). PR merge alone does not establish deployment." },
      { title: "'System-wide impact' metric",       project: "payment-svc",  date: "Sep 2026", status: "gap", summary: "Quantified impact claim lacks source metrics. Do not include until evidence is located." },
    ],
  },
];

export default function ProfilePage() {
  const [active, setActive] = useState("projects");
  const [selected, setSelected] = useState<any>(null);
  const section = SECTIONS.find(s => s.id === active)!;

  return (
    <div style={{ maxWidth: 1200, margin: "0 auto" }}>
      <div style={{ marginBottom: 24 }}>
        <div style={{ fontSize: 11, color: "var(--accent)", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: 6 }}>Engineering Profile</div>
        <h1>Your Engineering Narrative</h1>
        <p style={{ color: "var(--text-secondary)", fontSize: 13, marginTop: 4 }}>Every statement links to verified source evidence. Claims without evidence are flagged, not published.</p>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "200px 1fr", gap: 20 }}>
        {/* Section nav */}
        <div>
          {SECTIONS.map(s => {
            const hasGaps = s.items.some(i => i.status === "gap");
            return (
              <button key={s.id} onClick={() => { setActive(s.id); setSelected(null); }}
                className={`nav-link${active === s.id ? " active" : ""}`}
                style={{ justifyContent: "space-between", marginBottom: 2 }}>
                <span>{s.label}</span>
                <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
                  <span style={{ fontSize: 11, color: "var(--text-muted)" }}>{s.items.length}</span>
                  {hasGaps && <AlertTriangle size={11} color="var(--accent)" />}
                </div>
              </button>
            );
          })}
        </div>

        {/* Content */}
        <div style={{ display: "grid", gridTemplateColumns: selected ? "1fr 320px" : "1fr", gap: 16 }}>
          <div className="card" style={{ padding: 0, overflow: "hidden" }}>
            <div style={{ padding: "16px 20px", borderBottom: "1px solid var(--border)" }}>
              <h3>{section.label}</h3>
              <div style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 2 }}>{section.items.length} items · click any row to inspect evidence</div>
            </div>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Statement</th>
                  <th>Project</th>
                  <th>Date</th>
                  <th>Status</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {section.items.map((item, i) => (
                  <tr key={i} onClick={() => setSelected(item)} style={{ cursor: "pointer" }}>
                    <td style={{ color: "var(--text-primary)", fontWeight: 500 }}>{item.title}</td>
                    <td><span className="hash">{item.project}</span></td>
                    <td style={{ color: "var(--text-muted)", fontSize: 12 }}>{item.date}</td>
                    <td>
                      <span className={`badge ${item.status === "verified" ? "badge-verified" : item.status === "gap" ? "badge-gap" : "badge-pending"}`}>
                        {item.status}
                      </span>
                    </td>
                    <td><ChevronRight size={14} color="var(--text-muted)" /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Detail panel */}
          {selected && (
            <div className="card" style={{ padding: 20 }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 16 }}>
                <h3>{selected.title}</h3>
                <button onClick={() => setSelected(null)} style={{ background: "none", border: "none", color: "var(--text-muted)", cursor: "pointer", fontSize: 18, lineHeight: 1 }}>×</button>
              </div>
              <span className={`badge ${selected.status === "verified" ? "badge-verified" : selected.status === "gap" ? "badge-gap" : "badge-pending"}`} style={{ marginBottom: 16 }}>
                {selected.status}
              </span>
              <div style={{ fontSize: 13, color: "var(--text-secondary)", lineHeight: 1.7, marginBottom: 16, marginTop: 12 }}>
                {selected.summary}
              </div>
              <div className="divider" />
              <div className="section-label">Evidence Links</div>
              {selected.status === "gap" ? (
                <div className="gap-item">
                  <AlertTriangle size={14} color="var(--accent)" />
                  <div style={{ fontSize: 12, color: "var(--accent)" }}>No qualifying evidence found. This claim is held from reports until evidence is verified.</div>
                </div>
              ) : (
                <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                  {["PR #248 — auth-service", "Commit a3f9c1b2", "Issue #102"].map((src, i) => (
                    <div key={i} style={{ display: "flex", alignItems: "center", gap: 8, padding: "8px 10px", background: "var(--elevated)", borderRadius: 6 }}>
                      <CheckCircle size={12} color="var(--success)" />
                      <span style={{ fontSize: 12, color: "var(--text-primary)", flex: 1 }}>{src}</span>
                      <ExternalLink size={11} color="var(--text-muted)" />
                    </div>
                  ))}
                </div>
              )}
              <div className="divider" />
              <div style={{ fontSize: 11, color: "var(--text-muted)" }}>Last updated: Oct 10 · by TRACE agent run #7</div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
