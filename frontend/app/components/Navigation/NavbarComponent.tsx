"use client";

import React from "react";
import NavbarButton from "./NavButton";
import { FaComments, FaFileAlt, FaChartBar, FaPlus, FaCog, FaTachometerAlt } from "react-icons/fa";
import { IoBuildSharp } from "react-icons/io5";
import MockExamButton from "./MockExamButton";
import Link from "next/link";
import { useAuth } from '../Auth/AuthConext';
import { Button } from "@/components/ui/button";
import { IoPersonSharp } from "react-icons/io5";
import { PageType, PAGE_TYPES } from '../../types';
import { User } from '@supabase/supabase-js';

interface NavbarProps {
  APIHost: string | null;
  production: boolean;
  title: string;
  subtitle: string;
  imageSrc: string;
  version: string;
  currentPage: PageType;
  setCurrentPage: (page: PageType) => void;
  className?: string;
  user: User | null;
}

const Navbar: React.FC<NavbarProps> = ({
  APIHost,
  production,
  title,
  subtitle,
  imageSrc,
  version,
  currentPage,
  setCurrentPage,
  className,
  user,
}) => {
  const icon_size = 18;
  const { signOut } = useAuth();

  const handleSignOut = async () => {
    await signOut();
  };

  return (
    <nav className={`bg-white shadow-md w-full ${className}`}>
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-20"> {/* Increased height from h-16 to h-20 */}
          <div className="flex items-center pl-4 sm:pl-6 lg:pl-8"> {/* Added padding-left */}
            <div className="flex-shrink-0 flex items-center">
              <img className="h-8 w-auto mr-3" src={imageSrc} alt="Logo" />
              <div>
                <h1 className="text-xl font-bold text-indigo-600">{title}</h1>
                <p className="text-sm text-indigo-500">{subtitle}</p>
              </div>
            </div>
          </div>
          <div className="flex items-center space-x-4">
            <NavbarButton
              hide={false}
              APIHost={APIHost}
              Icon={FaComments}
              iconSize={icon_size}
              title="Chat"
              currentPage={currentPage}
              setCurrentPage={setCurrentPage}
              setPage={PAGE_TYPES.CHAT}
            />
            <NavbarButton
              hide={false}
              APIHost={APIHost}
              Icon={FaFileAlt}
              iconSize={icon_size}
              title="Documents"
              currentPage={currentPage}
              setCurrentPage={setCurrentPage}
              setPage={PAGE_TYPES.DOCUMENTS}
            />
            <NavbarButton
              hide={production}
              APIHost={APIHost}
              Icon={FaChartBar}
              iconSize={icon_size}
              title="Overview"
              currentPage={currentPage}
              setCurrentPage={setCurrentPage}
              setPage={PAGE_TYPES.STATUS}
            />
            <NavbarButton
              hide={production}
              APIHost={APIHost}
              Icon={FaPlus}
              iconSize={icon_size}
              title="Add Documents"
              currentPage={currentPage}
              setCurrentPage={setCurrentPage}
              setPage={PAGE_TYPES.ADD}
            />
            <NavbarButton
              hide={production}
              APIHost={APIHost}
              Icon={IoBuildSharp}
              iconSize={icon_size}
              title="RAG"
              currentPage={currentPage}
              setCurrentPage={setCurrentPage}
              setPage={PAGE_TYPES.RAG}
            />
            <MockExamButton
              APIHost={APIHost}
              currentPage={currentPage}
              setCurrentPage={setCurrentPage}
            />
            {user ? (
              <div className="flex items-center">
                <span className="mr-2">{user.email}</span>
                <Button onClick={handleSignOut} variant="outline" size="sm">
                  Sign Out
                </Button>
              </div>
            ) : (
              <Link href="/login">
                <Button variant="outline" size="sm">Sign In</Button>
              </Link>
            )}
            <NavbarButton
              hide={false}
              APIHost={APIHost}
              Icon={IoPersonSharp}
              iconSize={icon_size}
              title="AI Mentor"
              currentPage={currentPage}
              setCurrentPage={setCurrentPage}
              setPage={PAGE_TYPES.AI_MENTOR}
            />
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
