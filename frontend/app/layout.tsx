"use client"; // This makes RootLayout a client component

import { Inter } from 'next/font/google'
import './globals.css'
import { useAuth } from './utils/auth'
import { AuthProvider } from './components/Auth/AuthConext'; 
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';

const inter = Inter({ subsets: ['latin'] });

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const { user } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!user && router.pathname !== '/login' && router.pathname !== '/signup') {
      router.push('/login');
    }
  }, [user, router]);

  return (
    <html lang="en">
      <body className={inter.className}>
        <AuthProvider>
          {children}
        </AuthProvider> 
      </body>
    </html>
  );
}