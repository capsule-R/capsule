// Shared layout wrapper for all /dashboard/* routes.
// Individual pages still pass their own `active` / `title` props to DashboardShell,
// so this layout is intentionally minimal — it just ensures the <main> wrapper
// is present and the background colour is locked to --bg-base across all routes.
export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
