"use client";

import React from "react";
import { FaStar } from "react-icons/fa";

interface NavbarButtonProps {
  Icon: typeof FaStar;
  iconSize: number;
  title: string;
  currentPage: string;
  setCurrentPage: (
    page: "CHAT" | "DOCUMENTS" | "STATUS" | "ADD" | "SETTINGS" | "RAG"
  ) => void;
  setPage: "CHAT" | "DOCUMENTS" | "STATUS" | "ADD" | "SETTINGS" | "RAG";
  APIHost: string | null;
  hide: boolean;
}

const NavbarButton: React.FC<NavbarButtonProps> = ({
  Icon,
  iconSize,
  title,
  currentPage,
  setPage,
  setCurrentPage,
  APIHost,
  hide,
}) => {
  return (
    <button
      disabled={APIHost === null}
      key={title}
      className={`px-3 py-2 rounded-md text-sm font-medium ${
        hide ? "hidden" : "flex"
      } items-center justify-center ${
        currentPage === setPage
          ? "bg-gray-100 text-gray-900"
          : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
      }`}
      onClick={(e) => {
        setCurrentPage(setPage);
      }}
    >
      <Icon size={iconSize} className="mr-2" />
      <span className="hidden md:inline">{title}</span>
    </button>
  );
};

export default NavbarButton;
