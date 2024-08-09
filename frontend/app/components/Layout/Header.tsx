"use client";

import Link from 'next/link';
import { useAuth } from '@/app/useAuth';
import { Button } from '../ui/button';

export function Header() {
  const { session, signOut } = useAuth();

  return (
    <header className="bg-white shadow-sm">
      <nav className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8" aria-label="Top">
        <div className="w-full py-6 flex items-center justify-between border-b border-indigo-500 lg:border-none">
          <div className="flex items-center">
            <Link href="/">
              <span className="sr-only">Verba AI</span>
              <img
                className="h-10 w-auto"
                src="/logo.png"
                alt="Verba AI"
              />
            </Link>
            <div className="hidden ml-10 space-x-8 lg:block">
              <Link href="/chat" className="text-base font-medium text-gray-500 hover:text-gray-900">
                Chat
              </Link>
              <Link href="/documents" className="text-base font-medium text-gray-500 hover:text-gray-900">
                Documents
              </Link>
              <Link href="/mock-exam" className="text-base font-medium text-gray-500 hover:text-gray-900">
                Mock Exam
              </Link>
            </div>
          </div>
          <div className="ml-10 space-x-4">
            {session ? (
              <Button onClick={signOut}>Sign Out</Button>
            ) : (
              <Link href="/login">
                <Button>Sign In</Button>
              </Link>
            )}
          </div>
        </div>
      </nav>
    </header>
  );
}