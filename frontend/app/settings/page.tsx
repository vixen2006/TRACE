"use client";

import { useEffect, useState } from "react";
import {
  CheckCircle,
  AlertTriangle,
  Trash2,
  RefreshCw,
  Shield,
  Globe,
  Database,
} from "lucide-react";
import { GithubIcon } from "@/components/icons/GithubIcon";
import { fetchMe, logout, UserProfile } from "@/lib/api";

export default function SettingsPage() {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [timezone, setTimezone] = useState("UTC");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    fetchMe().then((u) => {
      if (mounted) {
        setUser(u);
        if (u?.timezone) setTimezone(u.timezone);
        setLoading(false);
      }
    });
    return () => {
      mounted = false;
    };
  }, []);

  const connected = Boolean(user);
  const displayName = user?.display_name || user?.name || user?.username || "Developer";
  const initials = displayName
    .split(" ")
    .map((s) => s[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();

  const handleConnectGitHub = () => {
    window.location.href = "/auth/github/login";
  };

  const handleDeleteAccount = async () => {
    if (
      !window.confirm(
        "Are you sure you want to permanently delete all your engineering memory data? This cannot be undone."
      )
    ) {
      return;
    }
    try {
      const res = await fetch("/api/v1/auth/me/data", {
        method: "DELETE",
        credentials: "include",
      });
      if (res.ok) {
        logout();
      }
    } catch (err) {
      console.error("Deletion failed", err);
    }
  };

  return (
    <div style={{ maxWidth: 720, margin: "0 auto" }}>
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
          Settings
        </div>
        <h1>Integrations & Preferences</h1>
        <p style={{ color: "var(--text-secondary)", fontSize: 13, marginTop: 4 }}>
          Manage connected sources, data scope, and privacy controls.
        </p>
      </div>

      {/* GitHub Integration */}
      <section className="card" style={{ marginBottom: 16 }}>
        <div
          style={{
            display: "flex",
            alignItems: "flex-start",
            justifyContent: "space-between",
            marginBottom: 16,
          }}
        >
          <div style={{ display: "flex", gap: 12, alignItems: "flex-start" }}>
            <GithubIcon size={20} color="var(--text-primary)" />
            <div>
              <div style={{ fontWeight: 600, marginBottom: 2 }}>GitHub Integration</div>
              <div style={{ fontSize: 12, color: "var(--text-secondary)" }}>
                Read-only access to repositories, PRs, commits, and reviews.
              </div>
            </div>
          </div>
          {connected ? (
            <div
              className="badge badge-merged"
              style={{ display: "inline-flex", alignItems: "center", gap: 4 }}
            >
              <CheckCircle size={12} /> Connected
            </div>
          ) : (
            <button
              className="btn btn-primary"
              onClick={handleConnectGitHub}
            >
              <GithubIcon size={13} /> Connect GitHub
            </button>
          )}
        </div>

        {connected && user && (
          <>
            <div className="divider" />
            <div style={{ marginBottom: 12 }}>
              <div className="section-label" style={{ marginBottom: 8 }}>
                Connected as
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                {user.avatar_url ? (
                  <img
                    src={user.avatar_url}
                    alt={displayName}
                    style={{
                      width: 32,
                      height: 32,
                      borderRadius: "50%",
                      border: "1px solid var(--border)",
                      objectFit: "cover",
                    }}
                  />
                ) : (
                  <div
                    style={{
                      width: 32,
                      height: 32,
                      background: "var(--elevated)",
                      borderRadius: "50%",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      fontSize: 12,
                      fontWeight: 700,
                      border: "1px solid var(--border)",
                    }}
                  >
                    {initials || "U"}
                  </div>
                )}
                <div>
                  <div style={{ fontSize: 13, fontWeight: 600 }}>{displayName}</div>
                  <div style={{ fontSize: 11, color: "var(--text-muted)" }}>
                    github.com/{user.username}
                  </div>
                </div>
              </div>
            </div>

            <div style={{ display: "flex", gap: 8, marginTop: 14 }}>
              <button
                className="btn btn-ghost"
                style={{ fontSize: 12 }}
                onClick={() => {
                  window.location.href = "/auth/github/login";
                }}
              >
                <RefreshCw size={12} /> Re-authenticate with GitHub
              </button>
              <button
                className="btn btn-danger"
                style={{ fontSize: 12 }}
                onClick={() => logout()}
              >
                Sign out
              </button>
            </div>
          </>
        )}
      </section>

      {/* Date & Timezone */}
      <section className="card" style={{ marginBottom: 16 }}>
        <div style={{ display: "flex", gap: 10, alignItems: "center", marginBottom: 16 }}>
          <Globe size={16} color="var(--text-secondary)" />
          <h3>Date & Timezone</h3>
        </div>
        <div style={{ marginBottom: 12 }}>
          <label
            style={{
              fontSize: 12,
              color: "var(--text-secondary)",
              display: "block",
              marginBottom: 6,
            }}
          >
            Timezone
          </label>
          <select
            className="input"
            value={timezone}
            onChange={(e) => setTimezone(e.target.value)}
            style={{ maxWidth: 280 }}
          >
            <option value="UTC">UTC</option>
            <option value="Asia/Kolkata">Asia/Kolkata (IST, UTC+5:30)</option>
            <option value="America/New_York">America/New_York (EST)</option>
            <option value="America/Los_Angeles">America/Los_Angeles (PST)</option>
            <option value="Europe/London">Europe/London (GMT)</option>
          </select>
        </div>
      </section>

      {/* Privacy & Data Controls */}
      <section className="card" style={{ marginBottom: 16 }}>
        <div style={{ display: "flex", gap: 10, alignItems: "center", marginBottom: 16 }}>
          <Shield size={16} color="var(--text-secondary)" />
          <h3>Privacy & Data Controls</h3>
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          {[
            {
              label: "Store only metadata",
              desc: "PR titles, hashes, and dates — raw code is not persisted.",
            },
            {
              label: "Require confirmation before sharing reports",
              desc: "Reports will not be published without explicit approval.",
            },
            {
              label: "Minimal scope policy",
              desc: "Private repos require separate, explicit consent.",
            },
          ].map((item, i) => (
            <label
              key={i}
              style={{
                display: "flex",
                gap: 12,
                cursor: "pointer",
                padding: "8px 0",
                borderBottom: "1px solid var(--border)",
              }}
            >
              <input
                type="checkbox"
                defaultChecked
                style={{ accentColor: "var(--accent)", marginTop: 2, flexShrink: 0 }}
              />
              <div>
                <div style={{ fontSize: 13, color: "var(--text-primary)", fontWeight: 500 }}>
                  {item.label}
                </div>
                <div style={{ fontSize: 12, color: "var(--text-muted)" }}>{item.desc}</div>
              </div>
            </label>
          ))}
        </div>
      </section>

      {/* Danger Zone */}
      <section className="card" style={{ borderColor: "rgba(255,69,69,0.3)" }}>
        <div style={{ display: "flex", gap: 10, alignItems: "center", marginBottom: 16 }}>
          <Database size={16} color="var(--error)" />
          <h3 style={{ color: "var(--error)" }}>Data Management</h3>
        </div>
        <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
          <button
            className="btn btn-danger"
            style={{ fontSize: 12 }}
            onClick={handleDeleteAccount}
          >
            <Trash2 size={12} /> Delete all user data & memory
          </button>
        </div>
        <div style={{ marginTop: 12, fontSize: 11, color: "var(--text-muted)" }}>
          Private engineering records are never used to train models. Deletion removes all stored data, tokens, and active sessions.
        </div>
      </section>
    </div>
  );
}
