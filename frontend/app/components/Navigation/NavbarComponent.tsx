"use client";

import React, { useState, useEffect } from "react";
import Link from 'next/link';
import { User } from '@supabase/supabase-js';
import { IoChatbubbleSharp } from "react-icons/io5";
import { IoDocumentSharp } from "react-icons/io5";
import { HiOutlineStatusOnline } from "react-icons/hi";
import { IoMdAddCircle } from "react-icons/io";
import { IoMdAddCircleOutline } from "react-icons/io";
import { IoSettingsSharp } from "react-icons/io5";
import { FaGithub } from "react-icons/fa";
import { IoBuildSharp } from "react-icons/io5";
import { LuMenu } from "react-icons/lu";

import NavbarButton from "./NavButton";
import MockExamButton from "./MockExamButton";
import { getGitHubStars } from "./util";
import { useAuth } from '../Auth/AuthConext';

interface NavbarProps {
  user: User | null;
  imageSrc: string;
  title: string;
  subtitle: string;
  version: string;
  currentPage: string;
  APIHost: string | null;
  production: boolean;
  setCurrentPage: (
    page: "CHAT" | "DOCUMENTS" | "STATUS" | "ADD" | "SETTINGS" | "RAG" | "PROFILE" | "MOCK_EXAM_START" | "MOCK_EXAM" | "ADD_MOCKS"
  ) => void;
}

const formatGitHubNumber = (num: number): string => {
  if (num >= 1000) {
    return (num / 1000).toFixed(1).replace(/\.0$/, "") + "k";
  }
  return num.toString();
};

const Navbar: React.FC<NavbarProps> = ({
  user,
  imageSrc,
  title,
  subtitle,
  APIHost,
  version,
  currentPage,
  setCurrentPage,
  production,
}) => {
  const { signOut } = useAuth();
  const [gitHubStars, setGitHubStars] = useState("0");
  const icon_size = 18;

  useEffect(() => {
    const fetchGitHubStars = async () => {
      try {
        const response: number = await getGitHubStars();
        if (response) {
          const formattedStars = formatGitHubNumber(response);
          setGitHubStars(formattedStars);
        }
      } catch (error) {
        console.error("Failed to fetch GitHub stars:", error);
      }
    };

    fetchGitHubStars();
  }, []);

  const handleGitHubClick = () => {
    window.open(
      "https://github.com/weaviate/verba",
      "_blank",
      "noopener,noreferrer"
    );
  };

  return (
    <div className="flex justify-between items-center mb-10">
      {/* Logo, Title, Subtitle */}
      <div className="flex flex-row items-center gap-5">
        <img src={imageSrc} width={80} className="flex" alt="Logo" />
        <div className="flex flex-col lg:flex-row lg:items-end justify-center lg:gap-3">
          <p className="sm:text-2xl md:text-3xl text-text-verba">{title}</p>
          <p className="sm:text-sm text-base text-text-alt-verba font-light">
            {subtitle}
          </p>
        </div>
      </div>

      <div className="flex flex-row justify-center items-center">
        <div className="hidden sm:h-[3vh] lg:h-[5vh] bg-text-alt-verba w-px sm:mx-2 md:mx-4"></div>

        {/* Pages */}
        <div className="lg:flex hidden lg:flex-row items-center lg:gap-3 justify-between">
          <div
            className={`${production ? "h-[0vh]" : "sm:h-[3vh] lg:h-[5vh] mx-1"} hidden sm:block bg-text-alt-verba w-px`}
          ></div>
          <NavbarButton
            hide={false}
            APIHost={APIHost}
            Icon={IoChatbubbleSharp}
            iconSize={icon_size}
            title="Chat"
            currentPage={currentPage}
            setCurrentPage={setCurrentPage}
            setPage="CHAT"
          />
          <NavbarButton
            hide={false}
            APIHost={APIHost}
            Icon={IoDocumentSharp}
            iconSize={icon_size}
            title="Documents"
            currentPage={currentPage}
            setCurrentPage={setCurrentPage}
            setPage="DOCUMENTS"
          />
          <NavbarButton
            hide={production}
            APIHost={APIHost}
            Icon={HiOutlineStatusOnline}
            iconSize={icon_size}
            title="Overview"
            currentPage={currentPage}
            setCurrentPage={setCurrentPage}
            setPage="STATUS"
          />
          <div
            className={`${production ? "h-[0vh]" : "sm:h-[3vh] lg:h-[5vh] mx-1"} hidden sm:block bg-text-alt-verba w-px`}
          ></div>
          <NavbarButton
            hide={production}
            APIHost={APIHost}
            Icon={IoMdAddCircle}
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
            Icon={IoSettingsSharp}
            iconSize={icon_size}
            title="Settings"
            currentPage={currentPage}
            setCurrentPage={setCurrentPage}
            setPage="SETTINGS"
          />
          <div
            className={`sm:h-[3vh] lg:h-[5vh] mx-1 hidden sm:block bg-text-alt-verba w-px`}
          ></div>

          {/* Mock Exam Button */}
          <MockExamButton  
            APIHost={APIHost} 
            currentPage={currentPage} 
            setCurrentPage={setCurrentPage}
          /> 

          <NavbarButton
            hide={production}
            APIHost={APIHost}
            Icon={IoMdAddCircleOutline}
            iconSize={icon_size}
            title="Add Mocks" 
            currentPage={currentPage}
            setCurrentPage={setCurrentPage}
            setPage="ADD_MOCKS" 
          />

          {user ? (
            <>
              <NavbarButton
                hide={false}
                APIHost={APIHost}
                Icon={IoSettingsSharp}
                iconSize={icon_size}
                title="Profile"
                currentPage={currentPage}
                setCurrentPage={setCurrentPage}
                setPage="PROFILE"
              />
              <button
                onClick={() => signOut()}
                className="btn btn-ghost btn-sm normal-case"
              >
                Sign Out
              </button>
            </>
          ) : (
            <>
              <Link href="/login" className="btn btn-ghost btn-sm normal-case">
                Login
              </Link>
              <Link href="/signup" className="btn btn-primary btn-sm normal-case">
                Sign Up
              </Link>
            </>
          )}
        </div>

        {/* Menu for mobile */}
        <div className="lg:hidden sm:flex md:ml-4 sm:mr-8">
          <ul className="menu md:menu-md sm:menu-sm sm:menu-horizontal bg-base-200 rounded-box bg-bg-alt-verba z-50">
            <li>
              <details>
                <summary>
                  <LuMenu size={20} />
                </summary>
                <ul className="bg-bg-alt-verba">
                  <li onClick={() => setCurrentPage("CHAT")}>
                    <a>Chat</a>
                  </li>
                  <li onClick={() => setCurrentPage("DOCUMENTS")}>
                    <a>Documents</a>
                  </li>
                  {!production && (
                    <li onClick={() => setCurrentPage("STATUS")}>
                      <a>Status</a>
                    </li>
                  )}
                  {!production && (
                    <li onClick={() => setCurrentPage("ADD")}>
                      <a>Add Documents</a>
                    </li>
                  )}
                  {!production && (
                    <li onClick={() => setCurrentPage("RAG")}>
                      <a>RAG</a>
                    </li>
                  )}
                  {!production && (
                    <li onClick={() => setCurrentPage("SETTINGS")}>
                      <a>Settings</a>
                    </li>
                  )}
                  <li onClick={() => setCurrentPage("MOCK_EXAM_START")}>
                    <a>Mock Exams</a>
                  </li>
                  {!production && (
                    <li onClick={() => setCurrentPage("ADD_MOCKS")}>
                      <a>Add Mocks</a>
                    </li>
                  )}
                  {user ? (
                    <>
                      <li onClick={() => setCurrentPage("PROFILE")}>
                        <a>Profile</a>
                      </li>
                      <li onClick={() => signOut()}>
                        <a>Sign Out</a>
                      </li>
                    </>
                  ) : (
                    <>
                      <li>
                        <Link href="/login">Login</Link>
                      </li>
                      <li>
                        <Link href="/signup">Sign Up</Link>
                      </li>
                    </>
                  )}
                  <li onClick={handleGitHubClick}>
                    <a>GitHub</a>
                  </li>
                  <li className="items-center justify-center text-xs text-text-alt-verba mt-2">
                    {version}
                  </li>
                </ul>
              </details>
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default Navbar;