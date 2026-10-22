"use client";

import { useSearchParams } from "next/navigation";
import { Shield, Lock, CheckCircle2, AlertCircle, Zap } from "lucide-react";
import { GithubIcon } from "@/components/icons/GithubIcon";
import { Suspense, useState } from "react";

function LoginContent() {
  const searchParams = useSearchParams();
  const errorParam = searchParams.get("error");
  const [loading, setLoading] = useState(false);

  const handleSignIn = () => {
    setLoading(true);
    // Direct browser navigation to start GitHub OAuth flow
    window.location.href = "/auth/github/login";
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        width: "100%",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "24px",
        background: "radial-gradient(ellipse at 50% 20%, rgba(227, 41, 54, 0.08) 0%, var(--bg) 70%)",
      }}
    >
      <div
        style={{
          width: "100%",
          maxWidth: 440,
          display: "flex",
          flexDirection: "column",
          gap: 20,
        }}
      >
        {/* Brand Header */}
        <div style={{ textAlign: "center", marginBottom: 8 }}>
          <div
            style={{
              display: "inline-flex",
              alignItems: "center",
              justifyContent: "center",
              width: 44,
              height: 44,
              background: "var(--accent)",
              borderRadius: 10,
              marginBottom: 16,
              boxShadow: "0 0 24px rgba(227, 41, 54, 0.35)",
            }}
          >
            <Zap size={22} color="#ffffff" strokeWidth={2.5} />
          </div>
          <h1
            style={{
              fontSize: "1.75rem",
              fontWeight: 700,
              letterSpacing: "-0.03em",
              marginBottom: 6,
            }}
          >
            Sign in to TRACE
          </h1>
          <p
            style={{
              color: "var(--text-secondary)",
              fontSize: 13,
              lineHeight: 1.5,
            }}
          >
            Engineering Memory — verified contribution records powered by a bounded AI agent.
          </p>
        </div>

        {/* Error Alert */}
        {errorParam && (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 10,
              padding: "12px 14px",
              background: "rgba(239, 68, 68, 0.1)",
              border: "1px solid rgba(239, 68, 68, 0.25)",
              borderRadius: "var(--radius)",
              color: "#f87171",
              fontSize: 12,
            }}
          >
            <AlertCircle size={16} />
            <span>
              {errorParam === "access_denied"
                ? "GitHub sign-in was cancelled."
                : `Authentication error: ${errorParam}`}
            </span>
          </div>
        )}

        {/* Main Card */}
        <div
          className="card"
          style={{
            padding: 28,
            boxShadow: "0 12px 32px rgba(0, 0, 0, 0.5)",
          }}
        >
          <div style={{ marginBottom: 20 }}>
            <button
              id="github-signin-btn"
              onClick={handleSignIn}
              disabled={loading}
              className="btn btn-primary"
              style={{
                width: "100%",
                padding: "12px 18px",
                fontSize: 14,
                fontWeight: 600,
                display: "flex",
                justifyContent: "center",
                alignItems: "center",
                gap: 10,
                borderRadius: "var(--radius)",
                cursor: loading ? "wait" : "pointer",
                opacity: loading ? 0.7 : 1,
              }}
            >
              <GithubIcon size={18} />
              {loading ? "Redirecting to GitHub..." : "Sign in with GitHub"}
            </button>
          </div>

          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 10,
              margin: "18px 0",
              color: "var(--text-muted)",
              fontSize: 11,
              textTransform: "uppercase",
              letterSpacing: "0.08em",
            }}
          >
            <div style={{ flex: 1, height: 1, background: "var(--border)" }} />
            <span>Minimal Scope Guaranteed</span>
            <div style={{ flex: 1, height: 1, background: "var(--border)" }} />
          </div>

          {/* Scope Explanation */}
          <div
            style={{
              background: "var(--elevated)",
              border: "1px solid var(--border)",
              borderRadius: "var(--radius)",
              padding: 14,
              fontSize: 12,
              lineHeight: 1.5,
              color: "var(--text-secondary)",
            }}
          >
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 6,
                fontWeight: 600,
                color: "var(--text-primary)",
                marginBottom: 6,
              }}
            >
              <Shield size={14} color="var(--accent)" />
              <span>Permission Transparency</span>
            </div>
            <p style={{ margin: 0 }}>
              TRACE starts with only <strong style={{ color: "var(--text-primary)" }}>read:user</strong> and public repository access. Private repository access is never requested without your explicit, separate consent.
            </p>
          </div>
        </div>

        {/* Security Pillars */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "1fr 1fr",
            gap: 10,
            fontSize: 11,
            color: "var(--text-muted)",
          }}
        >
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 6,
              background: "rgba(255, 255, 255, 0.02)",
              border: "1px solid var(--border)",
              borderRadius: "var(--radius-sm)",
              padding: "8px 10px",
            }}
          >
            <Lock size={12} color="var(--success)" />
            <span>Encrypted at rest</span>
          </div>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 6,
              background: "rgba(255, 255, 255, 0.02)",
              border: "1px solid var(--border)",
              borderRadius: "var(--radius-sm)",
              padding: "8px 10px",
            }}
          >
            <CheckCircle2 size={12} color="var(--success)" />
            <span>HttpOnly cookies</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense
      fallback={
        <div
          style={{
            minHeight: "100vh",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            color: "var(--text-muted)",
          }}
        >
          Loading...
        </div>
      }
    >
      <LoginContent />
    </Suspense>
  );
}
