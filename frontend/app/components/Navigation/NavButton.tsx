"use client";

import React from "react";
import { FaStar } from "react-icons/fa";
import { PageType } from '../../types';

interface NavbarButtonProps {
  Icon: typeof FaStar;
  iconSize: number;
  title: string;
  currentPage: PageType;
  setCurrentPage: (page: PageType) => void;
  setPage: PageType;
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
          ? "bg-indigo-100 text-indigo-900"
          : "text-indigo-600 hover:bg-indigo-50 hover:text-indigo-900"
      }`}
      onClick={(e) => {
        setCurrentPage(setPage);
      }}
    >
      <Icon size={iconSize} className="mr-2 text-indigo-600" />
      <span className="hidden md:inline">{title}</span>
    </button>
  );
};

export default NavbarButton;
