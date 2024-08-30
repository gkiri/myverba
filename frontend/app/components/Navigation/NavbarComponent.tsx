"use client";

import React from "react";
import NavbarButton from "./NavButton";
import { FaComments, FaFileAlt, FaChartBar, FaPlus, FaCog, FaTachometerAlt } from "react-icons/fa";
import { IoBuildSharp } from "react-icons/io5";
import MockExamButton from "./MockExamButton";
import Link from "next/link";
import { useAuth } from '../Auth/AuthConext';
import { Button } from "@/components/ui/button";

interface NavbarProps {
  APIHost: string | null;
  production: boolean;
  title: string;
  subtitle: string;
  imageSrc: string;
  version: string;
  currentPage: string;
  setCurrentPage: (page: string) => void;
  className?: string;
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
}) => {
  const icon_size = 18;
  const { user, signOut } = useAuth();

  const handleSignOut = async () => {
    await signOut();
  };

  return (
    <nav className={`bg-white shadow-md w-full ${className}`}>
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex">
            <div className="flex-shrink-0 flex items-center">
              <img className="h-8 w-auto" src={imageSrc} alt="Logo" />
              <div className="ml-2">
                <h1 className="text-xl font-bold text-gray-900">{title}</h1>
                <p className="text-sm text-gray-600">{subtitle}</p>
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
              setPage="CHAT"
            />
            <NavbarButton
              hide={false}
              APIHost={APIHost}
              Icon={FaFileAlt}
              iconSize={icon_size}
              title="Documents"
              currentPage={currentPage}
              setCurrentPage={setCurrentPage}
              setPage="DOCUMENTS"
            />
            <NavbarButton
              hide={production}
              APIHost={APIHost}
              Icon={FaChartBar}
              iconSize={icon_size}
              title="Overview"
              currentPage={currentPage}
              setCurrentPage={setCurrentPage}
              setPage="STATUS"
            />
            <NavbarButton
              hide={production}
              APIHost={APIHost}
              Icon={FaPlus}
              iconSize={icon_size}
              title="Add Documents"
              currentPage={currentPage}
              setCurrentPage={setCurrentPage}
              setPage="ADD"
            />
            <NavbarButton
              hide={production}
              APIHost={APIHost}
              Icon={IoBuildSharp}
              iconSize={icon_size}
              title="RAG"
              currentPage={currentPage}
              setCurrentPage={setCurrentPage}
              setPage="RAG"
            />
            <NavbarButton
              hide={production}
              APIHost={APIHost}
              Icon={FaCog}
              iconSize={icon_size}
              title="Settings"
              currentPage={currentPage}
              setCurrentPage={setCurrentPage}
              setPage="SETTINGS"
            />
            <MockExamButton
              APIHost={APIHost}
              currentPage={currentPage}
              setCurrentPage={setCurrentPage}
            />
            {user && (
              <Link href="/dashboard" className="text-gray-600 hover:text-gray-900">
                <FaTachometerAlt className="inline-block mr-1" />
                Dashboard
              </Link>
            )}
            {user && (
              <Button onClick={handleSignOut} variant="outline" size="sm">
                Sign Out
              </Button>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;