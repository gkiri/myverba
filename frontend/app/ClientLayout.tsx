'use client';

import React from 'react';
import { AuthProvider } from './useAuth';

export default function ClientLayout({ children }: { children: React.ReactNode }) {
  return (
    <AuthProvider>{children}</AuthProvider>
  );
}