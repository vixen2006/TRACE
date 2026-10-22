"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  GitMerge,
  Shield,
  Folders,
  AlertTriangle,
  ArrowRight,
  GitBranch,
  Clock,
  Circle,
  PlusCircle,
  RefreshCw,
} from "lucide-react";
import {
  fetchMe,
  fetchDashboardStats,
  fetchProjects,
  fetchActivities,
  UserProfile,
  DashboardStats,
  ProjectItem,
  ActivityItem,
} from "@/lib/api";

export default function Dashboard() {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [projects, setProjects] = useState<ProjectItem[]>([]);
  const [activities, setActivities] = useState<ActivityItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    async function loadData() {
      try {
        const [meData, statsData, projectsData, activitiesData] = await Promise.all([
          fetchMe(),
          fetchDashboardStats(),
          fetchProjects(),
          fetchActivities(),
        ]);
        if (mounted) {
          setUser(meData);
          setStats(statsData);
          setProjects(projectsData);
          setActivities(activitiesData);
        }
      } catch (err) {
        console.error("Failed to load dashboard data", err);
      } finally {
        if (mounted) setLoading(false);
      }
    }
    loadData();
    return () => {
      mounted = false;
    };
  }, []);

  const displayName = user?.display_name || user?.name || user?.username || "Developer";

  // Check if user has no data yet
  const hasNoData =
    !stats ||
    (stats.projects_active === 0 &&
      stats.total_commits === 0 &&
      stats.merged_prs === 0 &&
      projects.length === 0);

  return (
    <div style={{ maxWidth: 1200, margin: "0 auto" }}>
      {/* Header */}
      <div style={{ marginBottom: 28 }}>
        <div
          style={{
            fontSize: 11,
            color: "var(--accent)",
            fontWeight: 700,
            textTransform: "uppercase",
            letterSpacing: "0.1em",
            marginBottom: 6,
          }}
        >
          Your Engineering Impact · Real-time Overview
        </div>
        <h1 style={{ marginBottom: 6 }}>Good morning, {displayName}.</h1>
        <p style={{ color: "var(--text-secondary)", fontSize: 13 }}>
          Your work, accounted for. A verified record of what you built, what changed, and what still needs attention.
        </p>
      </div>

      {/* Stat cards */}
      <div className="grid-4" style={{ marginBottom: 24 }}>
        <div className="stat-card">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
            <span className="stat-label">Merged PRs</span>
            <GitMerge size={16} color="var(--success)" />
          </div>
          <div className="stat-value">{stats?.merged_prs ?? 0}</div>
          <div className="stat-sub">{stats ? `${stats.open_prs} open PRs` : "Live from GitHub"}</div>
        </div>
        <div className="stat-card">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
            <span className="stat-label">Evidence Coverage</span>
            <Shield size={16} color="var(--accent)" />
          </div>
          <div className="stat-value">
            {stats?.evidence_coverage_pct ?? 0}
            <span style={{ fontSize: "1rem", color: "var(--text-secondary)" }}>%</span>
          </div>
          <div className="stat-sub">
            {stats?.claims_needing_sources ?? 0} claims need sources
          </div>
        </div>
        <div className="stat-card">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
            <span className="stat-label">Projects Active</span>
            <Folders size={16} color="var(--text-muted)" />
          </div>
          <div className="stat-value">{stats?.projects_active ?? 0}</div>
          <div className="stat-sub">{projects.length} connected repos</div>
        </div>
        <div className="stat-card" style={{ borderColor: "rgba(227,41,54,0.3)" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
            <span className="stat-label">Needs Verification</span>
            <AlertTriangle size={16} color="var(--accent)" />
          </div>
          <div className="stat-value" style={{ color: "var(--accent)" }}>
            {stats?.needs_verification ?? 0}
          </div>
          <div className="stat-sub">Pending verification</div>
        </div>
      </div>

      {/* Empty State vs Content */}
      {hasNoData ? (
        <div
          className="card"
          style={{
            padding: "56px 24px",
            textAlign: "center",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            background: "radial-gradient(ellipse at 50% 30%, rgba(227, 41, 54, 0.05) 0%, var(--surface) 70%)",
            border: "1px dashed var(--border-hover)",
            borderRadius: "var(--radius-lg)",
            marginBottom: 24,
          }}
        >
          <div
            style={{
              width: 56,
              height: 56,
              borderRadius: "50%",
              background: "var(--elevated)",
              border: "1px solid var(--border)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              marginBottom: 18,
            }}
          >
            <GitBranch size={24} color="var(--accent)" />
          </div>
          <h2 style={{ fontSize: "1.25rem", fontWeight: 700, marginBottom: 8 }}>
            Connect a repository to get started
          </h2>
          <p
            style={{
              color: "var(--text-secondary)",
              fontSize: 13,
              maxWidth: 480,
              lineHeight: 1.6,
              marginBottom: 24,
            }}
          >
            TRACE builds verified engineering records by analyzing your pull requests, commits, and code reviews. Connect your first repository to begin tracing your engineering impact.
          </p>
          <div style={{ display: "flex", gap: 12, flexWrap: "wrap", justifyContent: "center" }}>
            <Link href="/settings" className="btn btn-primary" style={{ padding: "10px 20px" }}>
              <PlusCircle size={15} />
              Connect a repository
            </Link>
            <Link href="/agent" className="btn btn-ghost" style={{ padding: "10px 20px" }}>
              View agent
              <ArrowRight size={14} />
            </Link>
          </div>
        </div>
      ) : (
        <div className="grid-2" style={{ marginBottom: 24 }}>
          {/* Active Projects */}
          <div className="card">
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
              <div>
                <div className="section-label">Connected Repositories</div>
                <h3 style={{ color: "var(--text-primary)" }}>Active Projects</h3>
              </div>
              <Link href="/settings" className="btn btn-ghost" style={{ fontSize: 12, padding: "6px 12px" }}>
                Manage <ArrowRight size={12} />
              </Link>
            </div>
            {projects.length === 0 ? (
              <p style={{ color: "var(--text-muted)", fontSize: 13 }}>No active projects.</p>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                {projects.map((proj) => (
                  <div
                    key={proj.id}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      padding: "10px 14px",
                      background: "var(--elevated)",
                      borderRadius: "var(--radius)",
                      border: "1px solid var(--border)",
                    }}
                  >
                    <div>
                      <div style={{ fontWeight: 600, fontSize: 13 }}>{proj.name}</div>
                      {proj.github_repo_full_name && (
                        <div className="hash" style={{ fontSize: 11, color: "var(--text-muted)" }}>
                          {proj.github_repo_full_name}
                        </div>
                      )}
                    </div>
                    <Link href={`/activity`} className="btn btn-ghost" style={{ fontSize: 11, padding: "4px 8px" }}>
                      View
                    </Link>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Recent Activity */}
          <div className="card">
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
              <div>
                <div className="section-label">Source Ingestion</div>
                <h3 style={{ color: "var(--text-primary)" }}>Recent Activity</h3>
              </div>
              <Link href="/activity" className="btn btn-ghost" style={{ fontSize: 12, padding: "6px 12px" }}>
                View all <ArrowRight size={12} />
              </Link>
            </div>
            {activities.length === 0 ? (
              <p style={{ color: "var(--text-muted)", fontSize: 13 }}>
                No recent activity ingested. Trigger a sync in Settings.
              </p>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                {activities.slice(0, 5).map((act) => (
                  <div
                    key={act.id}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      padding: "8px 12px",
                      background: "var(--elevated)",
                      borderRadius: "var(--radius-sm)",
                    }}
                  >
                    <div style={{ minWidth: 0, flex: 1, marginRight: 10 }}>
                      <div
                        style={{
                          fontSize: 12,
                          color: "var(--text-primary)",
                          whiteSpace: "nowrap",
                          overflow: "hidden",
                          textOverflow: "ellipsis",
                        }}
                      >
                        {act.title || act.external_id}
                      </div>
                      <div style={{ fontSize: 11, color: "var(--text-muted)" }}>
                        {act.activity_type} · {act.status || "recorded"}
                      </div>
                    </div>
                    <span
                      className={`badge ${
                        act.status === "merged"
                          ? "badge-merged"
                          : act.status === "open"
                          ? "badge-open"
                          : "badge-default"
                      }`}
                    >
                      {act.status || act.activity_type}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
