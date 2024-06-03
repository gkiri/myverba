"use client";

import React from "react";
import { IoSchoolSharp } from "react-icons/io5"; //  Or any suitable icon 
import NavbarButton from "./NavButton";  // Import the existing NavbarButton component

interface MockExamButtonProps {
  APIHost: string | null;
  currentPage: string;
  setCurrentPage: (page: string) => void;
}

const MockExamButton: React.FC<MockExamButtonProps> = ({
  APIHost,
  currentPage,
  setCurrentPage,
}) => {
  return (
    <NavbarButton 
      hide={false}  // Always show the Mock Test button
      APIHost={APIHost}
      Icon={IoSchoolSharp}
      iconSize={18}  // Adjust icon size as needed 
      title="Mock Tests"
      currentPage={currentPage}
      setCurrentPage={setCurrentPage} 
      setPage="MOCK_EXAM"  // New page identifier 
    />
  );
};

export default MockExamButton;