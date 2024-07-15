import React from 'react'
import { supabase } from '../../utils/supabaseClient'
import { FaGoogle, FaFacebook } from 'react-icons/fa'

const SocialLogin: React.FC = () => {
  const handleGoogleLogin = async () => {
    try {
      const { error } = await supabase.auth.signInWithOAuth({
        provider: 'google',
      })
      if (error) throw error
    } catch (error) {
      console.error('Error logging in with Google:', error.message)
    }
  }

  const handleFacebookLogin = async () => {
    try {
      const { error } = await supabase.auth.signInWithOAuth({
        provider: 'facebook',
      })
      if (error) throw error
    } catch (error) {
      console.error('Error logging in with Facebook:', error.message)
    }
  }

  return (
    <div className="space-y-4">
      <button
        onClick={handleGoogleLogin}
        className="w-full py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 flex items-center justify-center"
      >
        <FaGoogle className="mr-2" /> Sign in with Google
      </button>
      <button
        onClick={handleFacebookLogin}
        className="w-full py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 flex items-center justify-center"
      >
        <FaFacebook className="mr-2" /> Sign in with Facebook
      </button>
    </div>
  )
}

export default SocialLogin