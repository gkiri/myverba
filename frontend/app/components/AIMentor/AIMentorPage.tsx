import React from "react";
import ChatInterfaceComponent from "../Chat/ChatInterface";
import { SettingsConfiguration } from "../Settings/types";
import { RAGConfig } from "../RAG/types";
import { Message } from "../Chat/types";

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
  const [messages, setMessages] = React.useState<Message[]>([
    {
      type: "system",
      content: "Welcome to AI Mentor! How can I assist you with your UPSC preparation today?",
    },
  ]);

  return (
    <div className="flex flex-col h-full w-full">
      <h1 className="text-2xl font-bold mb-4">AI Mentor</h1>
      <div className="flex-grow">
        <ChatInterfaceComponent
          settingConfig={settingConfig}
          APIHost={APIHost}
          setChunks={() => {}}
          setChunkTime={() => {}}
          setCurrentPage={setCurrentPage}
          setContext={() => {}}
          RAGConfig={RAGConfig}
          production={production}
          setMessages={setMessages}
          messages={messages}
        />
      </div>
    </div>
  );
};

export default AIMentorPage;
