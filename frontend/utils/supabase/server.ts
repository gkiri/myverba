import { Database } from '@/types/supabase'
import { createServerClient, type CookieOptions } from '@supabase/ssr'
import { createClient as createClientBase } from '@supabase/supabase-js'

export function createClient() {
    return createClientBase<Database>(
        process.env.NEXT_PUBLIC_SUPABASE_URL!,
        process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
        {
            auth: {
                persistSession: false,
            },
        }
    )
}
