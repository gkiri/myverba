'use client'

import React from 'react';
import { AuthProvider } from './AuthProvider';

const AuthWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <AuthProvider>
      {children}
    </AuthProvider>
  );
};

export default AuthWrapper;