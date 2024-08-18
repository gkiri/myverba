// app/auth-wrapper.tsx (create a new file)
"use client"; 

import { useAuth } from './utils/auth'; 

const AuthWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, session, signOut } = useAuth();

  return (
    <>
      {children} 
    </>
  );
};

export default AuthWrapper;