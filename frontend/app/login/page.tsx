"use client";

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { createSupabaseClient } from '@/utils/supabase/client.ts';
import { Button } from '../components/ui/button';
import { 
  Card, 
  CardHeader, 
  CardTitle, 
  CardDescription, 
  CardContent 
} from '../components/ui/card';
import { Label } from '../components/ui/label';
import { Input } from '../components/ui/input';
import { OAuthButtons } from './oauth-signin';
import { toast } from 'react-hot-toast';
import Link from 'next/link'; // Import the Link component

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const router = useRouter();
  const supabase = createSupabaseClient();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const { error } = await supabase.auth.signInWithPassword({ email, password });

      if (error) {
        console.error('Login error:', error);
        toast.error(error.message);
      } else {
        router.push('/'); 
      }
    } catch (err) {
      console.error('Unexpected login error:', err);
      toast.error('An unexpected error occurred during login.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-100">
      <Card className="w-full max-w-md p-8 bg-white shadow-md rounded-md"> 
        <CardHeader className="text-center mb-6">
          <CardTitle className="text-2xl font-bold text-gray-800">Login to Verba AI</CardTitle>
          <CardDescription className="text-gray-600">
            Enter your credentials or use GitHub to login.
          </CardDescription>
        </CardHeader>

        <CardContent>
          <form onSubmit={handleLogin} className="space-y-6"> 
            <div>
              <Label htmlFor="email" className="block text-sm font-medium text-gray-700">
                Email
              </Label>
              <Input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="mt-1 block w-full px-3 py-2 bg-gray-100 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
              />
            </div>

            <div>
              <Label htmlFor="password" className="block text-sm font-medium text-gray-700">
                Password
              </Label>
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="mt-1 block w-full px-3 py-2 bg-gray-100 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
              />
            </div>

            <Button type="submit" className="w-full py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500" disabled={loading}>
              {loading ? 'Logging in...' : 'Login'}
            </Button>
          </form>

          <div className="mt-8"> 
            <OAuthButtons /> 
          </div>

          {/* Add a link to the signup page */}
          <div className="mt-4 text-center text-sm text-gray-600">
            Don't have an account? <Link href="/signup" className="text-indigo-600 hover:text-indigo-500">Sign up</Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}