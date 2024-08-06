'use client';

import React, { createContext, useContext, useEffect, useState } from 'react';
import { createClient, Session, SupabaseClient } from '@supabase/supabase-js';

interface AuthContextType {
  session: Session | null;
  supabase: SupabaseClient;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [supabase] = useState(() => createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  ));
  const [session, setSession] = useState<Session | null>(null);

  useEffect(() => {
    const setServerSession = async () => {
      const { data: { session } } = await supabase.auth.getSession();
      setSession(session);
    };
    setServerSession();

    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session);
    });

    return () => subscription.unsubscribe();
  }, [supabase]);

  return (
    <AuthContext.Provider value={{ session, supabase }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}