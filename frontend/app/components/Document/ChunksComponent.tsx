import React, { useEffect } from "react";
import { DocumentChunk } from "../Document/types";
import { RAGConfig } from "../RAG/types";
import { FaDatabase, FaSearch, FaListUl } from "react-icons/fa";
import { IoSparkles } from "react-icons/io5";
import { MdSummarize } from "react-icons/md";
import { BsGraphUp } from "react-icons/bs";
import UserModalComponent from "../Navigation/UserModal";
import ChunkDropdown from "./ChunkDropdown";

interface ChunksComponentProps {
  chunks: DocumentChunk[];
  selectedChunk: DocumentChunk | null;
  chunkTime: number;
  setSelectedChunk: (c: DocumentChunk | null) => void;
  setCurrentPage: (p: any) => void;
  context: string;
  RAGConfig: RAGConfig | null;
  production: boolean;
}

interface FeatureButton {
  icon: React.ElementType;
  label: string;
  action: () => void;
  isRAGComponent?: boolean;
}

const ChunksComponent: React.FC<ChunksComponentProps> = ({
  chunks,
  selectedChunk,
  chunkTime,
  context,
  setSelectedChunk,
  setCurrentPage,
  RAGConfig,
  production,
}) => {
  useEffect(() => {
    if (chunks && chunks.length > 0) {
      setSelectedChunk(chunks[0]);
    } else {
      setSelectedChunk(null);
    }
  }, [chunks]);

  const openContextModal = () => {
    const modal = document.getElementById("context_modal");
    if (modal instanceof HTMLDialogElement) {
      modal.showModal();
    }
  };

  const featureButtons: FeatureButton[] = [
    { 
      icon: FaDatabase, 
      label: RAGConfig ? RAGConfig.Embedder.selected : "ADAEmbedder", 
      action: () => setCurrentPage("RAG"),
      isRAGComponent: true
    },
    { 
      icon: FaSearch, 
      label: RAGConfig ? "WindowRetriev" : "WindowRetriever",
      action: () => setCurrentPage("RAG"),
      isRAGComponent: true
    },
    { icon: IoSparkles, label: "See Context", action: openContextModal },
    { icon: FaListUl, label: "Bullet Points", action: () => console.log("Bullet Points") },
    { icon: MdSummarize, label: "Summarize", action: () => console.log("Summarize") },
    { icon: BsGraphUp, label: "Visualize", action: () => console.log("Visualize") },
  ];

  return (
    <div className="flex flex-col gap-4 bg-bg-alt-verba rounded-lg shadow-lg p-5 text-text-verba">
      <div className="flex justify-between items-center mb-2">
        <h2 className="text-lg font-semibold">Relevant Context</h2>
        {chunks && chunks.length > 0 && (
          <p className="text-text-alt-verba text-xs">
            {chunks.length} chunks in {chunkTime.toFixed(2)}s
          </p>
        )}
      </div>

      <ChunkDropdown
        chunks={chunks}
        selectedChunk={selectedChunk}
        setSelectedChunk={setSelectedChunk}
      />

      <div className="flex flex-col gap-2 mt-2">
        {featureButtons.map((button, index) => (
          <button
            key={index}
            onClick={button.action}
            disabled={button.isRAGComponent && production}
            className={`w-full bg-button-verba hover:bg-primary-verba text-text-verba flex items-center justify-between px-4 py-2.5 rounded-lg transition-all duration-200 ease-in-out transform hover:scale-102 hover:shadow-md ${button.isRAGComponent && production ? 'opacity-50 cursor-not-allowed' : ''}`}
          >
            <div className="flex items-center">
              <button.icon className="text-lg mr-3 flex-shrink-0" />
              <span className="text-sm font-medium truncate">{button.label}</span>
            </div>
          </button>
        ))}
      </div>

      <UserModalComponent
        modal_id="context_modal"
        title="Context Used"
        text={context}
      />
    </div>
  );
};

export default ChunksComponent;