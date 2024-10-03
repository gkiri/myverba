"use client";

import React, { useEffect, useState } from "react";
import AIMentorChatInterface from "./AIMentorChatInterface";
import SyllabusViewer from "./SyllabusViewer";
import { SettingsConfiguration } from "../Settings/types";
import { RAGConfig } from "../RAG/types";
import { useAuth } from '../Auth/AuthConext';

interface AIMentorPageProps {
  settingConfig: SettingsConfiguration;
  APIHost: string | null;
  setCurrentPage: (p: any) => void;
  RAGConfig: RAGConfig | null;
  production: boolean;
}

const AIMentorPage: React.FC<AIMentorPageProps> = ({
  APIHost,
  settingConfig,
  setCurrentPage,
  RAGConfig,
  production,
}) => {
  const { user } = useAuth();
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const checkUser = async () => {
      try {
        if (user) {
          console.log("User ID:", user.id);
        } else {
          console.log("User not authenticated");
        }
      } catch (error) {
        console.error("Error fetching user information:", error);
      } finally {
        setIsLoading(false);
      }
    };

    checkUser();
  }, [user]);

  if (isLoading) {
    return <div>Loading...</div>;
  }

  if (!user) {
    return <div>Please log in to access the AI Mentor.</div>;
  }

  return (
    <div className="flex flex-col items-center h-full w-full px-4">
      <div className="w-full h-full flex flex-col">
        <h1 className="text-2xl font-bold mb-4 text-center">AI Mentor</h1>
        <div className="flex-grow flex space-x-4">
          <div className="w-1/2">
            <div className="h-full bg-white dark:bg-gray-800 shadow-2xl rounded-xl overflow-hidden">
              <AIMentorChatInterface
                settingConfig={settingConfig}
                APIHost={APIHost}
                setCurrentPage={setCurrentPage}
                RAGConfig={RAGConfig}
                production={production}
              />
            </div>
          </div>
          <div className="w-1/2">
            <div className="h-full bg-white dark:bg-gray-800 shadow-2xl rounded-xl overflow-hidden">
              <SyllabusViewer
                APIHost={APIHost}
                production={production}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AIMentorPage;