import React, { useState, useEffect, createContext, useContext, ReactNode } from 'react';
import { createClient, Session, SupabaseClient } from '@supabase/supabase-js';

interface SessionContextType {
  session: Session | null;
  loading: boolean;
  supabase: SupabaseClient;
}

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
);

const SessionContext = createContext<SessionContextType | undefined>(undefined);

interface SessionProviderProps {
  children: ReactNode;
}

export const SessionProvider: React.FC<SessionProviderProps> = ({ children }) => {
  const [sessionState, setSessionState] = useState<SessionContextType>({
    session: null,
    loading: true,
    supabase,
  });

  useEffect(() => {
    const session = supabase.auth.getSession();
    setSessionState(prevState => ({ ...prevState, session: session || null, loading: false }));

    const { data: authListener } = supabase.auth.onAuthStateChange(
      async (event, session) => {
        setSessionState(prevState => ({ ...prevState, session, loading: false }));
      }
    );

    return () => {
      authListener?.unsubscribe();
    };
  }, []);

  return (
    <SessionContext.Provider value={sessionState}>
      {children}
    </SessionContext.Provider>
  );
};

export const useSession = (): SessionContextType => {
  const context = useContext(SessionContext);
  if (context === undefined) {
    throw new Error('useSession must be used within a SessionProvider');
  }
  return context;
};