import React from "react";
import AIMentorChatInterface from "./AIMentorChatInterface";
import { SettingsConfiguration } from "../Settings/types";
import { RAGConfig } from "../RAG/types";

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
  return (
    <div className="flex flex-col items-center h-full w-full px-4">
      <div className="w-full sm:w-3/4 md:w-2/3 lg:w-1/2 h-full flex flex-col">
        <h1 className="text-2xl font-bold mb-4 text-center">AI Mentor</h1>
        <div className="flex-grow">
          <AIMentorChatInterface
            settingConfig={settingConfig}
            APIHost={APIHost}
            setCurrentPage={setCurrentPage}
            RAGConfig={RAGConfig}
            production={production}
          />
        </div>
      </div>
    </div>
  );
};

export default AIMentorPage;
