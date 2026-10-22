import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Sign in — TRACE",
  description: "Sign in with GitHub to access your engineering memory.",
};

export default function LoginLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
