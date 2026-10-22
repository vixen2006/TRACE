/**
 * Frontend API client for TRACE.
 * Automatically sends same-origin credentials (session cookies) for all requests.
 */

export interface UserProfile {
  id: string;
  username: string;
  name?: string | null;
  display_name?: string | null;
  avatar_url?: string | null;
  email?: string | null;
  timezone?: string;
  created_at?: string;
}

export interface DashboardStats {
  merged_prs: number;
  open_prs: number;
  total_commits: number;
  projects_active: number;
  evidence_coverage_pct: number;
  claims_needing_sources: number;
  needs_verification: number;
}

export interface ProjectItem {
  id: string;
  user_id: string;
  name: string;
  repository_url?: string | null;
  github_repo_full_name?: string | null;
  description?: string | null;
  created_at: string;
}

export interface ActivityItem {
  id: string;
  project_id: string;
  provider: string;
  external_id: string;
  activity_type: string;
  title?: string | null;
  occurred_at?: string | null;
  status?: string | null;
  url?: string | null;
  author_handle?: string | null;
  synced_at: string;
}

export async function fetchMe(): Promise<UserProfile | null> {
  try {
    const res = await fetch("/api/me", {
      credentials: "include",
      headers: { Accept: "application/json" },
    });
    if (!res.ok) {
      if (res.status === 401) return null;
      return null;
    }
    return await res.json();
  } catch {
    return null;
  }
}

export async function fetchDashboardStats(): Promise<DashboardStats | null> {
  try {
    const res = await fetch("/api/v1/dashboard/stats", {
      credentials: "include",
      headers: { Accept: "application/json" },
    });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

export async function fetchProjects(): Promise<ProjectItem[]> {
  try {
    const res = await fetch("/api/v1/projects", {
      credentials: "include",
      headers: { Accept: "application/json" },
    });
    if (!res.ok) return [];
    return await res.json();
  } catch {
    return [];
  }
}

export async function fetchActivities(): Promise<ActivityItem[]> {
  try {
    const res = await fetch("/api/v1/activities", {
      credentials: "include",
      headers: { Accept: "application/json" },
    });
    if (!res.ok) return [];
    return await res.json();
  } catch {
    return [];
  }
}

export async function logout(): Promise<void> {
  try {
    await fetch("/auth/logout", {
      method: "POST",
      credentials: "include",
    });
  } catch {
    // ignore
  } finally {
    // Clear cookies on client side as well
    document.cookie = "trace_session=; path=/; max-age=0; expires=Thu, 01 Jan 1970 00:00:00 GMT";
    document.cookie = "session=; path=/; max-age=0; expires=Thu, 01 Jan 1970 00:00:00 GMT";
    window.location.href = "/login";
  }
}
