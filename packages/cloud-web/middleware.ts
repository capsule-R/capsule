import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { updateSession } from '@/lib/supabase/middleware';

const PUBLIC_PATHS = ['/', '/login', '/signup'];

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Allow all public routes and static files through
  const isPublic =
    PUBLIC_PATHS.includes(pathname) ||
    pathname.startsWith('/_next') ||
    pathname.startsWith('/api') ||
    pathname.includes('.');

  if (isPublic) return NextResponse.next();

  // Dashboard routes: verify Supabase JWT
  const { supabaseResponse, user } = await updateSession(request);

  if (!user) {
    const loginUrl = new URL('/login', request.url);
    loginUrl.searchParams.set('next', pathname);
    return NextResponse.redirect(loginUrl);
  }

  return supabaseResponse;
}

export const config = {
  // Run middleware on all routes except static assets
  matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'],
};
