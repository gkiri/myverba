"use client"; // This makes RootLayout a client component

import { Inter } from 'next/font/google'
import './globals.css'
import { AuthProvider } from './components/Auth/AuthConext';

const inter = Inter({ subsets: ['latin'] });

export default function RootLayout({ children }: { children: React.ReactNode }) {
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