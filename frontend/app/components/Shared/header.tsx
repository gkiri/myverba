import { signOut } from "@/utils/auth"; 
import { Button } from "@/components/ui/button"; 
import Link from "next/link";
import { useAuth } from '../Auth/AuthConext';
import { FaSignOutAlt } from 'react-icons/fa'; // Import the sign out icon

export default function Header() {
  const { user } = useAuth(); 

  return (
    <header className="z-50 fixed top-0 left-0 right-0 w-full border-b border-indigo-200 bg-white/95 backdrop-blur supports-[backdrop-filter]:bg-white/60">
      <div className="container flex h-14 max-w-screen-2xl items-center">
        <nav className="flex items-center space-x-4 lg:space-x-6">
          <Link className="mr-6 flex items-center space-x-2" href="/">
            <span className="font-bold text-indigo-600">Verba AI</span>
          </Link>
          {/* Add more navigation links here if needed */}
        </nav>
        <div className="flex flex-1 items-center justify-end space-x-2">
          {user ? (
            <form action={signOut} className="flex items-center gap-2">
              <p className="text-indigo-600">{user.email}</p>
              <Button type="submit" className="bg-indigo-600 hover:bg-indigo-700 text-white">
                <FaSignOutAlt className="mr-2" /> Sign Out
              </Button>
            </form>
          ) : (
            <Button asChild className="bg-indigo-600 hover:bg-indigo-700 text-white">
              <Link href="/login">Sign In</Link>
            </Button>
          )}
        </div>
      </div>
    </header>
  );
}