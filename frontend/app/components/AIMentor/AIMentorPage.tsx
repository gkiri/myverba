"use client";

import React, { useEffect, useState } from "react";
import AIMentorChatInterface from "./AIMentorChatInterface";
import SyllabusViewer from "./SyllabusViewer";
import { SettingsConfiguration } from "../Settings/types";
import { RAGConfig } from "../RAG/types";
import { useAuth } from '../Auth/AuthConext';
import { getUserId } from '@/utils/getUserId';

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
  const [llmResponse, setLlmResponse] = useState<string>("");

  const [initialFetchDone, setInitialFetchDone] = useState(false);

  useEffect(() => {
    const fetchSyllabusChapter = async () => {
      if (initialFetchDone) return;

      try {
        const userId = user?.id;
        if (!userId) {
          console.error("User ID not found");
          return;
        }

        const chapterId = "h1"; // Hardcoded for now, can be made dynamic later

        const response = await fetch(`${APIHost}/api/get_syllabus_chapter_with_userstatus`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ user_id: userId, chapter_id: chapterId }),
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        setLlmResponse(data.llm_response);
        setInitialFetchDone(true);
      } catch (error) {
        console.error("Error fetching syllabus chapter:", error);
      } finally {
        setIsLoading(false);
      }
    };

    if (user && !initialFetchDone) {
      fetchSyllabusChapter();
    }
  }, [APIHost, user, initialFetchDone]);

  if (isLoading) {
    return <div>Loading...</div>;
  }

  return (
    <div className="flex flex-col items-center h-full w-full px-4 pt-6">
      <h1 className="text-2xl font-bold mb-4 text-center">AI Mentor</h1>
      <div className="w-full h-[calc(100vh-120px)] flex flex-row space-x-4">
        <div className="w-1/2">
          <div className="h-full bg-white dark:bg-gray-800 shadow-2xl rounded-xl overflow-hidden">
            <AIMentorChatInterface
              settingConfig={settingConfig}
              APIHost={APIHost}
              setCurrentPage={setCurrentPage}
              RAGConfig={RAGConfig}
              production={production}
              initialMessage={llmResponse}
              isInitialMessage={!isLoading && initialFetchDone}
            />
          </div>
        </div>
        <div className="w-1/2">
          <div className="h-full bg-white dark:bg-gray-800 shadow-2xl rounded-xl overflow-hidden">
            <SyllabusViewer APIHost={APIHost} production={production} />
          </div>
        </div>
      </div>
    </div>
  );
};

export default AIMentorPage;