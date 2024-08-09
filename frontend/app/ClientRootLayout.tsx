'use client'

import React from 'react'
import { useAuth } from './useAuth'
import LoadingSpinner from './components/LoadingSpinner'

export default function ClientRootLayout({ children }: { children: React.ReactNode }) {
  const { loading } = useAuth()

  if (loading) {
    return <LoadingSpinner />
  }

  return <>{children}</>
}