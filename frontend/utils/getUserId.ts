import { useAuth } from '../app/components/Auth/AuthConext';

let cachedUserId: string | null = null;

export async function getUserId(): Promise<string | null> {
  if (cachedUserId) {
    return cachedUserId;
  }

  const { user } = useAuth();

  if (user && user.id) {
    cachedUserId = user.id;
    return user.id;
  }

  // If user is not available in the context, try to fetch it from Supabase
  const { createClient } = await import('@/utils/supabase/server');
  const supabase = createClient();
  const { data: { user: supabaseUser } } = await supabase.auth.getUser();

  if (supabaseUser && supabaseUser.id) {
    cachedUserId = supabaseUser.id;
    return supabaseUser.id;
  }

  return null;
}

// Function to clear the cache when user logs out
export function clearUserIdCache() {
  cachedUserId = null;
}
