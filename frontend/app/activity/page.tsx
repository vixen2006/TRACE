"use client";
import { useState } from "react";
import { Search, Filter, ExternalLink, GitMerge, GitPullRequest, GitCommit, MessageSquare, CheckCircle, AlertTriangle, Clock } from "lucide-react";

const ACTIVITIES = [
  { id: "pr-248", type: "pull_request", title: "feat: JWT refresh token rotation with revocation list", repo: "auth-service",  status: "merged",  author: "vaishnavit", date: "Oct 9, 2026", url: "#", evidence: "verified" },
  { id: "pr-251", type: "pull_request", title: "fix: handle concurrent token refresh race condition",   repo: "auth-service",  status: "merged",  author: "vaishnavit", date: "Oct 8, 2026", url: "#", evidence: "verified" },
  { id: "pr-183", type: "pull_request", title: "feat: idempotency key validation for payment endpoints",repo: "payment-svc",   status: "merged",  author: "vaishnavit", date: "Oct 6, 2026", url: "#", evidence: "verified" },
  { id: "pr-71",  type: "pull_request", title: "refactor: migrate to async request handlers",           repo: "api-gateway",   status: "open",    author: "vaishnavit", date: "Oct 7, 2026", url: "#", evidence: "pending" },
  { id: "cm-a3f", type: "commit",       title: "fix: correct token expiry timezone handling",            repo: "auth-service",  status: "merged",  author: "vaishnavit", date: "Oct 9, 2026", url: "#", evidence: "verified" },
  { id: "rv-248", type: "review",       title: "Reviewed: DB index strategy for user sessions",          repo: "auth-service",  status: "approved",author: "vaishnavit", date: "Oct 5, 2026", url: "#", evidence: "verified" },
  { id: "iss-89", type: "issue",        title: "Bug: duplicate payment charges on retry",                repo: "payment-svc",   status: "closed",  author: "vaishnavit", date: "Sep 30, 2026",url: "#", evidence: "verified" },
  { id: "pr-41",  type: "pull_request", title: "chore: update Terraform provider to v5",                repo: "infra-tf",      status: "merged",  author: "vaishnavit", date: "Oct 4, 2026", url: "#", evidence: "pending" },
  { id: "cm-8b2", type: "commit",       title: "docs: add ADR for Kafka adoption",                       repo: "data-pipeline", status: "merged",  author: "vaishnavit", date: "Sep 28, 2026",url: "#", evidence: "verified" },
  { id: "pr-66",  type: "pull_request", title: "feat: streaming consumer with at-least-once delivery",  repo: "data-pipeline", status: "open",    author: "vaishnavit", date: "Oct 3, 2026", url: "#", evidence: "gap" },
];

function typeIcon(t: string) {
  switch (t) {
    case "pull_request": return <GitPullRequest size={13} />;
    case "commit":       return <GitCommit size={13} />;
    case "review":       return <MessageSquare size={13} />;
    case "issue":        return <AlertTriangle size={13} />;
    default:             return <GitCommit size={13} />;
  }
}

export default function ActivityPage() {
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");
  const [evidenceFilter, setEvidenceFilter] = useState("all");

  const filtered = ACTIVITIES.filter(a =>
    (typeFilter === "all" || a.type === typeFilter) &&
    (statusFilter === "all" || a.status === statusFilter) &&
    (evidenceFilter === "all" || a.evidence === evidenceFilter) &&
    (search === "" || a.title.toLowerCase().includes(search.toLowerCase()) || a.repo.includes(search) || a.id.includes(search))
  );

  return (
    <div style={{ maxWidth: 1200, margin: "0 auto" }}>
      <div style={{ marginBottom: 24 }}>
        <div style={{ fontSize: 11, color: "var(--accent)", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: 6 }}>
          Activity Explorer
        </div>
        <h1>Raw Source Records</h1>
        <p style={{ color: "var(--text-secondary)", fontSize: 13, marginTop: 4 }}>
          Inspect engineering activity and trace why each claim appears in a report. Source-linked, not interpreted.
        </p>
      </div>

      {/* Filters */}
      <div className="card" style={{ marginBottom: 20, padding: 14 }}>
        <div style={{ display: "flex", gap: 10, flexWrap: "wrap", alignItems: "center" }}>
          <div style={{ position: "relative", flex: 1, minWidth: 200 }}>
            <Search size={13} style={{ position: "absolute", left: 10, top: "50%", transform: "translateY(-50%)", color: "var(--text-muted)" }} />
            <input className="input" placeholder="Search by title, repo, or hash..." value={search} onChange={e => setSearch(e.target.value)} style={{ paddingLeft: 30 }} />
          </div>
          <select className="input" style={{ width: "auto" }} value={typeFilter} onChange={e => setTypeFilter(e.target.value)}>
            <option value="all">All types</option>
            <option value="pull_request">Pull requests</option>
            <option value="commit">Commits</option>
            <option value="review">Reviews</option>
            <option value="issue">Issues</option>
          </select>
          <select className="input" style={{ width: "auto" }} value={statusFilter} onChange={e => setStatusFilter(e.target.value)}>
            <option value="all">All statuses</option>
            <option value="merged">Merged</option>
            <option value="open">Open</option>
            <option value="closed">Closed</option>
            <option value="approved">Approved</option>
          </select>
          <select className="input" style={{ width: "auto" }} value={evidenceFilter} onChange={e => setEvidenceFilter(e.target.value)}>
            <option value="all">All evidence</option>
            <option value="verified">Verified</option>
            <option value="pending">Pending</option>
            <option value="gap">Gap</option>
          </select>
          <div style={{ fontSize: 12, color: "var(--text-muted)", whiteSpace: "nowrap" }}>
            {filtered.length} of {ACTIVITIES.length} records
          </div>
        </div>
      </div>

      {/* Legend */}
      <div style={{ display: "flex", gap: 16, marginBottom: 16, padding: "0 4px" }}>
        <div style={{ fontSize: 11, color: "var(--text-muted)", display: "flex", alignItems: "center", gap: 4 }}>
          <div style={{ width: 8, height: 8, borderRadius: "50%", background: "var(--surface)", border: "2px solid var(--border)" }} />
          Raw source record
        </div>
        <div style={{ fontSize: 11, color: "var(--text-muted)", display: "flex", alignItems: "center", gap: 4 }}>
          <CheckCircle size={11} color="var(--success)" />
          Verified
        </div>
        <div style={{ fontSize: 11, color: "var(--text-muted)", display: "flex", alignItems: "center", gap: 4 }}>
          <Clock size={11} color="#f59e0b" />
          Pending verification
        </div>
        <div style={{ fontSize: 11, color: "var(--text-muted)", display: "flex", alignItems: "center", gap: 4 }}>
          <AlertTriangle size={11} color="var(--accent)" />
          Insufficient evidence
        </div>
      </div>

      {/* Table */}
      <div className="card" style={{ padding: 0, overflow: "hidden" }}>
        <table className="data-table">
          <thead>
            <tr>
              <th>Type</th>
              <th>Title</th>
              <th>Repository</th>
              <th>Status</th>
              <th>Evidence</th>
              <th>Date</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {filtered.map(a => (
              <tr key={a.id}>
                <td>
                  <div style={{ display: "flex", alignItems: "center", gap: 6, color: "var(--text-secondary)" }}>
                    {typeIcon(a.type)}
                    <span style={{ fontSize: 11, textTransform: "capitalize" }}>{a.type.replace("_", " ")}</span>
                  </div>
                </td>
                <td style={{ color: "var(--text-primary)", maxWidth: 300 }}>
                  <div style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{a.title}</div>
                  <div className="hash" style={{ marginTop: 2, display: "inline-block" }}>{a.id}</div>
                </td>
                <td><span className="hash">{a.repo}</span></td>
                <td>
                  <span className={`badge ${a.status === "merged" || a.status === "closed" || a.status === "approved" ? "badge-merged" : "badge-open"}`}>
                    {a.status}
                  </span>
                </td>
                <td>
                  {a.evidence === "verified" && <span className="badge badge-verified"><CheckCircle size={9} /> Verified</span>}
                  {a.evidence === "pending"  && <span className="badge badge-pending"><Clock size={9} /> Pending</span>}
                  {a.evidence === "gap"      && <span className="badge badge-gap"><AlertTriangle size={9} /> Gap</span>}
                </td>
                <td style={{ color: "var(--text-muted)", fontSize: 12, whiteSpace: "nowrap" }}>{a.date}</td>
                <td>
                  <a href={a.url} style={{ color: "var(--text-muted)", display: "flex" }}>
                    <ExternalLink size={13} />
                  </a>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {filtered.length === 0 && (
          <div style={{ textAlign: "center", padding: "48px", color: "var(--text-muted)" }}>
            No records match the current filters.
          </div>
        )}
      </div>
    </div>
  );
}
