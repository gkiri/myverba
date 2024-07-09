import React, { useEffect, useState } from "react";
import { DocumentChunk } from "../Document/types";
import CountUp from "react-countup";
import { RAGConfig } from "../RAG/types";
import ComponentStatus from "../Status/ComponentStatus";
import { FaSearch, FaDatabase } from "react-icons/fa";
import { IoSparkles } from "react-icons/io5";
import UserModalComponent from "../Navigation/UserModal";

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
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);

  useEffect(() => {
    if (chunks && chunks.length > 0) {
      setSelectedChunk(chunks[0]);
    } else {
      setSelectedChunk(null);
    }
  }, [chunks]);

  const handleChunkSelect = (chunk: DocumentChunk) => {
    setSelectedChunk(chunk);
    setIsDropdownOpen(false);
  };

  const openContextModal = () => {
    const modal = document.getElementById("context_modal");
    if (modal instanceof HTMLDialogElement) {
      modal.showModal();
    }
  };

  return (
    <div className="flex flex-col gap-2">
      <div className="flex flex-col bg-bg-alt-verba rounded-lg shadow-lg p-5 text-text-verba gap-3 md:h-[17vh] lg:h-[65vh] overflow-auto">
        <div className="flex md:flex-col gap-5">
          {/* RAG Component Status */}
          {RAGConfig && (
            <div className="flex flex-row lg:flex-col gap-2 items-center lg:w-full">
              <ComponentStatus
                disable={production}
                component_name={RAGConfig ? RAGConfig["Embedder"].selected : ""}
                Icon={FaDatabase}
                changeTo={"RAG"}
                changePage={setCurrentPage}
              />
              <ComponentStatus
                disable={production}
                component_name={RAGConfig ? RAGConfig["Retriever"].selected : ""}
                Icon={FaSearch}
                changeTo={"RAG"}
                changePage={setCurrentPage}
              />
            </div>
          )}
          
          {/* Chunk retrieval info */}
          {chunks && chunks.length > 0 && (
            <div className="sm:hidden md:flex items-center justify-center">
              <p className="items-center justify-center text-text-alt-verba text-xs">
                {chunks.length} chunks retrieved in {chunkTime} seconds.
              </p>
            </div>
          )}
        </div>

        {/* Chunks Dropdown */}
        <div className="relative">
          <button
            onClick={() => setIsDropdownOpen(!isDropdownOpen)}
            className="w-full btn bg-button-verba hover:bg-button-hover-verba text-text-verba"
          >
            {selectedChunk ? `Chunk ${selectedChunk.chunk_id + 1}` : "Select a Chunk"}
          </button>
          {isDropdownOpen && (
            <div className="absolute z-10 w-full mt-1 bg-bg-alt-verba border border-gray-300 rounded-md shadow-lg">
              {chunks.map((chunk, index) => (
                <button
                  key={`${chunk.doc_name}-${index}`}
                  onClick={() => handleChunkSelect(chunk)}
                  className="w-full text-left px-4 py-2 hover:bg-button-hover-verba"
                >
                  <div className="flex items-center">
                    <span className="mr-2">
                      <CountUp end={index + 1} className="text-sm" />
                    </span>
                    <div>
                      <p className="text-sm">{chunk.doc_name}</p>
                      <p className="text-xs text-text-alt-verba">{chunk.doc_type}</p>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* See Context Button */}
        {context !== "" && (
          <button
            onClick={openContextModal}
            className="btn flex gap-2 w-full border-none bg-button-verba text-text-verba hover:bg-button-hover-verba"
          >
            <IoSparkles className="text-text-verba" />
            <p className="text-text-verba text-xs">See Context</p>
          </button>
        )}
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