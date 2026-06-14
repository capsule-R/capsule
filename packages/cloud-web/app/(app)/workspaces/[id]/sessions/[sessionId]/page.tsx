import { redirect } from 'next/navigation';

/**
 * Canonical workspace-scoped session URL. The time-travel inspector lives at
 * /dashboard/sessions/[id]; this route keeps /workspaces/:id/sessions/:sessionId
 * links working without duplicating the page.
 */
export default async function WorkspaceSessionPage({
  params,
}: {
  params: Promise<{ id: string; sessionId: string }>;
}) {
  const { sessionId } = await params;
  redirect(`/dashboard/sessions/${sessionId}`);
}
