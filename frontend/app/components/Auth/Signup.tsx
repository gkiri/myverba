import React, { useState, useCallback, useEffect } from 'react'
import { useAuth } from '../../contexts/AuthContext'

const COOLDOWN_PERIOD = 60000; // 1 minute in milliseconds

const SignUp: React.FC = () => {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [cooldown, setCooldown] = useState(0)
  const { signUp } = useAuth()

  useEffect(() => {
    let timer: NodeJS.Timeout
    if (cooldown > 0) {
      timer = setInterval(() => {
        setCooldown(prev => Math.max(0, prev - 1000))
      }, 1000)
    }
    return () => clearInterval(timer)
  }, [cooldown])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (cooldown > 0) {
      setError(`Please wait ${Math.ceil(cooldown / 1000)} seconds before trying again.`)
      return
    }
    setIsSubmitting(true)
    setError(null)
    try {
      await signUp(email, password)
      // Handle successful sign up
    } catch (error) {
      if (error.message.includes('rate limit') || error.message.includes('Email rate limit exceeded')) {
        setError("We're experiencing high traffic. Please wait before trying again.")
        setCooldown(COOLDOWN_PERIOD)
      } else {
        setError(error.message)
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label htmlFor="email" className="block text-sm font-medium text-gray-700">Email</label>
        <input
          type="email"
          id="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50"
        />
      </div>
      <div>
        <label htmlFor="password" className="block text-sm font-medium text-gray-700">Password</label>
        <input
          type="password"
          id="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50"
        />
      </div>
      {error && <p className="text-red-500">{error}</p>}
      <button
        type="submit"
        disabled={isSubmitting || cooldown > 0}
        className={`w-full py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white 
        ${isSubmitting || cooldown > 0 ? 'bg-indigo-400 cursor-not-allowed' : 'bg-indigo-600 hover:bg-indigo-700'}
        focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500`}
      >
        {isSubmitting ? 'Signing Up...' : cooldown > 0 ? `Wait ${Math.ceil(cooldown / 1000)}s` : 'Sign Up'}
      </button>
    </form>
  )
}

export default SignUp