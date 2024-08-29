import React, { useState, useEffect } from "react";
import ChatInterfaceComponent from "./ChatInterface";
import { SettingsConfiguration } from "../Settings/types";
import { DocumentChunk } from "../Document/types";
import ChunksComponent from "../Document/ChunksComponent";
import DocumentComponent from "../Document/DocumentComponent";
import MermaidDiagram from "../Document/MermaidDiagram";  // Import the MermaidDiagram component
import { RAGConfig } from "../RAG/types";
import { Message, QueryPayload_Button } from "./types";

interface ChatComponentProps {
  settingConfig: SettingsConfiguration;
  APIHost: string | null;
  setCurrentPage: (p: any) => void;
  RAGConfig: RAGConfig | null;
  production: boolean;
}

const ChatComponent: React.FC<ChatComponentProps> = ({
  APIHost,
  settingConfig,
  setCurrentPage,
  RAGConfig,
  production,
}) => {
  const [chunks, setChunks] = useState<DocumentChunk[]>([]);
  const [context, setContext] = useState("");
  const [chunkTime, setChunkTime] = useState(0);
  const [selectedChunk, setSelectedChunk] = useState<DocumentChunk | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [featureContent, setFeatureContent] = useState<string | null>(null);
  const [featureType, setFeatureType] = useState<string | null>(null);

  useEffect(() => {
    console.log("Messages updated in ChatComponent:", messages);
  }, [messages]);

  const handleFeatureClick = async (feature: string) => {
    console.log(`Clicked feature: ${feature}`);
    
    const lastMessage = messages.filter(msg => msg.type === "system").pop();
    
    if (!lastMessage) {
      setFeatureContent("There are no chat messages available. Please ask the user to query.");
      setFeatureType(null);
      return;
    }

    const content = lastMessage.content;

    try {
      const payload: QueryPayload_Button = { query: content };
      console.log(`Backend route called: ${APIHost}/api/${feature}`);

      const response = await fetch(`${APIHost}/api/${feature}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log(`Backend response for ${feature}:`, data);

      if (feature === 'bullet_points') {
        // Handle bullet points
        let bulletPointsArray: string[];
        if (Array.isArray(data.bullet_points)) {
          bulletPointsArray = data.bullet_points;
        } else if (typeof data.bullet_points === 'string') {
          bulletPointsArray = data.bullet_points.split('\n').filter(Boolean);
        } else if (typeof data.bullet_points === 'object') {
          bulletPointsArray = Object.values(data.bullet_points);
        } else {
          throw new Error('Unexpected data structure for bullet points');
        }
        
        const bulletPointsMarkdown = bulletPointsArray.map((point: string) => `- ${point}`).join('\n');
        setFeatureContent(bulletPointsMarkdown);
        setFeatureType('bullet_points');
      } else if (feature === 'summarize') {
        setFeatureContent(data.summary);
        setFeatureType('summary');
      } else if (feature === 'visualize') {
        if (typeof data.mermaid_code === 'string') {
          console.log('Raw Mermaid code:', data.mermaid_code);
          setFeatureContent(data.mermaid_code);
          setFeatureType('visualization');
        } else {
          throw new Error('Unexpected data structure for Mermaid diagram');
        }
      }
    } catch (error) {
      console.error(`Error fetching ${feature}:`, error);
      setFeatureContent(`Error: ${error.message}`);
      setFeatureType(null);
    }
  };

  const renderFeatureContent = () => {
    if (!featureContent) return null;

    switch (featureType) {
      case 'bullet_points':
      case 'summary':
        return (
          <DocumentComponent
            production={production}
            setSelectedChunk={setSelectedChunk}
            selectedChunk={selectedChunk}
            APIhost={APIHost}
            settingConfig={settingConfig}
            deletable={false}
            selectedDocument={null}
            featureContent={featureContent}
            featureType={featureType}
          />
        );
      case 'visualization':
        return <MermaidDiagram code={featureContent} />;
      default:
        return null;
    }
  };

  return (
    <div className="flex sm:flex-col md:flex-row justify-between items-stretch md:gap-3 h-full">
      <div className="sm:w-full md:w-2/3 lg:w-3/5 flex flex-col">
        <ChatInterfaceComponent
          setContext={setContext}
          production={production}
          RAGConfig={RAGConfig}
          settingConfig={settingConfig}
          APIHost={APIHost}
          setChunks={setChunks}
          setChunkTime={setChunkTime}
          setCurrentPage={setCurrentPage}
          setMessages={setMessages}
          messages={messages}
        />
      </div>

      <div className="flex lg:flex-row sm:flex-col justify-between items-start sm:w-full md:w-1/2 lg:w-4/6 gap-3 h-full">
        <div className="sm:w-full md:w-1/3 lg:w-1/5 flex flex-col gap-2">
          <ChunksComponent
            context={context}
            production={production}
            chunks={chunks}
            RAGConfig={RAGConfig}
            selectedChunk={selectedChunk}
            setSelectedChunk={setSelectedChunk}
            chunkTime={chunkTime}
            setCurrentPage={setCurrentPage}
            messages={messages}
            onFeatureClick={handleFeatureClick}
          />
        </div>

        <div className="sm:w-full lg:w-4/5 flex flex-col gap-2 h-full">
          <DocumentComponent
            production={production}
            setSelectedChunk={setSelectedChunk}
            selectedChunk={selectedChunk}
            APIhost={APIHost}
            settingConfig={settingConfig}
            deletable={false}
            selectedDocument={null}
            featureContent={featureContent}
            featureType={featureType}
          />
        </div>
      </div>
    </div>
  );
};

export default ChatComponent;