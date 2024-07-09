import React, { useState } from "react";
import { DocumentChunk } from "../Document/types";
import { FaChevronDown, FaDatabase } from "react-icons/fa";

interface ChunkDropdownProps {
  chunks: DocumentChunk[];
  selectedChunk: DocumentChunk | null;
  setSelectedChunk: (c: DocumentChunk | null) => void;
}

const ChunkDropdown: React.FC<ChunkDropdownProps> = ({
  chunks,
  selectedChunk,
  setSelectedChunk,
}) => {
  const [isOpen, setIsOpen] = useState(false);

  const handleChunkSelect = (chunk: DocumentChunk) => {
    setSelectedChunk(chunk);
    setIsOpen(false);
  };

  return (
    <div className="relative w-full">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full bg-button-verba hover:bg-primary-verba text-text-verba flex items-center justify-between px-4 py-2.5 rounded-lg transition-all duration-200 ease-in-out transform hover:scale-102 hover:shadow-md"
      >
        <div className="flex items-center">
          <FaDatabase   className="text-lg mr-3 flex-shrink-0" />
          <span className="text-sm font-medium truncate">
            {selectedChunk ? `Chunk ${selectedChunk.chunk_id + 1}` : "Select Chunk"}
          </span>
        </div>
        <FaChevronDown className={`ml-2 transition-transform duration-200 ${isOpen ? 'transform rotate-180' : ''}`} />
      </button>
      {isOpen && (
        <div className="absolute z-10 w-full mt-1 bg-bg-alt-verba border border-gray-200 rounded-lg shadow-lg max-h-60 overflow-auto">
          {chunks.map((chunk, index) => (
            <button
              key={`${chunk.doc_name}-${index}`}
              onClick={() => handleChunkSelect(chunk)}
              className="w-full text-left px-4 py-2.5 hover:bg-primary-verba transition-colors duration-150 flex items-center"
            >
              <FaDatabase  className="text-lg mr-3 flex-shrink-0" />
              <div className="overflow-hidden">
                <p className="text-sm font-medium truncate">Chunk {chunk.chunk_id + 1}</p>
                <p className="text-xs text-text-alt-verba truncate">{chunk.doc_name}</p>
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

export default ChunkDropdown;