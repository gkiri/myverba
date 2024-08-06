import { createServerClient, type CookieOptions } from '@supabase/ssr';
import { NextResponse, type NextRequest } from 'next/server';

export async function middleware(request: NextRequest) {
    let response = NextResponse.next({
        request: {
            headers: request.headers,
        },
    });

    const supabase = createServerClient(
        process.env.NEXT_PUBLIC_SUPABASE_URL!,
        process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
        {
            cookies: {
                get(name: string) {
                    return request.cookies.get(name)?.value;
                },
                set(name: string, value: string, options: CookieOptions) {
                    request.cookies.set({
                        name,
                        value,
                        ...options,
                    });
                    response = NextResponse.next({
                        request: {
                            headers: request.headers,
                        },
                    });
                    response.cookies.set({
                        name,
                        value,
                        ...options,
                    });
                },
                remove(name: string, options: CookieOptions) {
                    request.cookies.set({
                        name,
                        value: '',
                        ...options,
                    });
                    response = NextResponse.next({
                        request: {
                            headers: request.headers,
                        },
                    });
                    response.cookies.set({
                        name,
                        value: '',
                        ...options,
                    });
                },
            },
        }
    );

    const { data: { session } } = await supabase.auth.getSession();

    // List of public routes that don't require authentication
    const publicRoutes = ['/login', '/signup', '/auth/callback'];

    if (!session && !publicRoutes.includes(request.nextUrl.pathname)) {
        // Redirect to login page if not authenticated and trying to access a protected route
        return NextResponse.redirect(new URL('/login', request.url));
    }

    // If user is authenticated and trying to access login/signup pages, redirect to home
    if (session && (request.nextUrl.pathname === '/login' || request.nextUrl.pathname === '/signup')) {
        return NextResponse.redirect(new URL('/', request.url));
    }

    return response;
}

// export const config = {
//     matcher: [
//         '/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)',
//     ],
// };