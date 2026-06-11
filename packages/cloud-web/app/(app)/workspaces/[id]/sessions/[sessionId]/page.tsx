import { redirect } from 'next/navigation';

/**
 * Canonical workspace-scoped session URL. The time-travel inspector lives at
 * /dashboard/sessions/[id]; this route keeps /workspaces/:id/sessions/:sessionId
 * links working without duplicating the page.
 */
export default function WorkspaceSessionPage({
  params,
}: {
  params: { id: string; sessionId: string };
}) {
  redirect(`/dashboard/sessions/${params.sessionId}`);
}
