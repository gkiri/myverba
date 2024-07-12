import React, { useState, useEffect, useRef } from "react";
import { DocumentChunk, Document, DocumentPayload } from "../Document/types";
import ReactMarkdown from "react-markdown";
import PulseLoader from "react-spinners/PulseLoader";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneDark, oneLight } from "react-syntax-highlighter/dist/cjs/styles/prism";
import { SettingsConfiguration } from "../Settings/types";
import { FormattedDocument } from "../Document/types";
import { splitDocument } from "./util";
import { FaExternalLinkAlt } from "react-icons/fa";
import { MdOutlineSimCardDownload } from "react-icons/md";
import { HiMiniSparkles } from "react-icons/hi2";
import { MdDelete } from "react-icons/md";
import UserModalComponent from "../Navigation/UserModal";
import MermaidDiagram from "./MermaidDiagram";

interface DocumentComponentProps {
  settingConfig: SettingsConfiguration;
  APIhost: string | null;
  selectedChunk: DocumentChunk | null;
  setSelectedChunk: (s: any | null) => void;
  selectedDocument: Document | null;
  deletable: boolean;
  setDocuments?: (d: Document[] | null) => void;
  setTriggerReset?: (b: any) => void;
  production: boolean;
  featureContent: string | null;
  featureType: string | null;
}

const DocumentComponent: React.FC<DocumentComponentProps> = ({
  APIhost,
  selectedChunk,
  settingConfig,
  selectedDocument,
  deletable,
  setSelectedChunk,
  setDocuments,
  setTriggerReset,
  production,
  featureContent,
  featureType,
}) => {
  const [currentDocument, setCurrentDocument] = useState<Document | null>(null);
  const [formattedDocument, setFormattedDocument] = useState<FormattedDocument | null>(null);
  const [isFetching, setIsFetching] = useState(false);
  const [showWholeDocument, setWholeDocument] = useState(false);

  const chunkRef = useRef<null | HTMLDivElement>(null);

  useEffect(() => {
    if (selectedChunk != null && APIhost != null) {
      fetchDocuments();
    } else {
      setCurrentDocument(null);
    }
  }, [selectedChunk]);

  const fetchDocuments = async () => {
    if (selectedChunk != null && APIhost != null) {
      try {
        setIsFetching(true);

        const response = await fetch(APIhost + "/api/get_document", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            document_id: selectedChunk.doc_uuid,
          }),
        });
        const data: DocumentPayload = await response.json();

        if (data) {
          if (data.error !== "") {
            setCurrentDocument(null);
            console.error(data.error);
            setFormattedDocument(null);
            setIsFetching(false);
            setWholeDocument(false);
          } else {
            setCurrentDocument(data.document);
            setFormattedDocument(
              splitDocument(data.document.text, selectedChunk.text)
            );
            setIsFetching(false);
            if (chunkRef.current) {
              chunkRef.current.scrollIntoView({ behavior: "smooth" });
            }
            if (
              selectedChunk.text !== "" &&
              data.document.text.length >
                settingConfig.Chat.settings.max_document_size.value
            ) {
              setWholeDocument(false);
            } else {
              setWholeDocument(true);
            }
          }
        }
      } catch (error) {
        console.error("Failed to fetch document:", error);
        setIsFetching(false);
      }
    }
  };

  const handleSourceClick = () => {
    window.open(currentDocument?.link, "_blank", "noopener,noreferrer");
  };

  const handleDeleteDocument = async (uuid: string) => {
    try {
      console.log("DELETING " + uuid);
      fetch(APIhost + "/api/delete_document", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ document_id: uuid }),
      });
      setCurrentDocument(null);
      setSelectedChunk(null);
      if (setDocuments) {
        setDocuments(null);
      }
      if (setTriggerReset) {
        setTriggerReset((prev: boolean) => !prev);
      }
    } catch (error) {
      console.error("Failed to delete document:", error);
    }
  };

  const handleDocumentShow = () => {
    setWholeDocument((prev) => !prev);
  };

  const openDeleteModal = () => {
    const modal = document.getElementById("delete_document_modal");
    if (modal instanceof HTMLDialogElement) {
      modal.showModal();
    }
  };

  const renderFeatureContent = () => {
    if (!featureContent) return null;

    const commonClasses = "bg-bg-alt-verba rounded-lg p-6 shadow-lg prose prose-verba max-w-none";

    switch (featureType) {
      case 'bullet_points':
        return (
          <div className={commonClasses}>
            <h2 className="text-2xl font-bold mb-4 text-primary-verba">Key Points</h2>
            <ReactMarkdown
              components={{
                ul: ({node, ...props}) => <ul className="list-disc pl-5 space-y-2" {...props} />,
                li: ({node, ...props}) => <li className="text-text-verba" {...props} />,
              }}
            >
              {featureContent}
            </ReactMarkdown>
          </div>
        );
      case 'summary':
        return (
          <div className={commonClasses}>
            <h2 className="text-2xl font-bold mb-4 text-primary-verba">Summary</h2>
            <ReactMarkdown>{featureContent}</ReactMarkdown>
          </div>
        );
      case 'visualization':
        return <MermaidDiagram code={featureContent} />;
      default:
        return (
          <div className={commonClasses}>
            <ReactMarkdown>{featureContent}</ReactMarkdown>
          </div>
        );
    }
  };

  if (featureContent) {
    return (
      <div className="flex flex-col bg-bg-alt-verba rounded-lg shadow-lg p-5 text-text-verba gap-5 sm:h-[53.5vh] lg:h-[65vh] overflow-auto">
        {renderFeatureContent()}
      </div>
    );
  }

  if (currentDocument !== null && !isFetching) {
    return (
      <div className="flex flex-col bg-bg-alt-verba rounded-lg shadow-lg p-5 text-text-verba gap-5 sm:h-[53.5vh] lg:h-[65vh] overflow-auto">
        {/*Title*/}
        <div className="flex justify-between">
          <div className="flex flex-col">
            <p className="sm:text-sm md:text-lg font-semibold">
              {currentDocument.name}
            </p>
            <p className="sm:text-xs md:text-sm text-text-alt-verba">
              {currentDocument.type}
            </p>
          </div>
          <div className="flex gap-3">
            {formattedDocument && formattedDocument.substring !== "" && (
              <div className="flex">
                <button
                  onClick={handleDocumentShow}
                  className="btn border-none text-text-verba bg-button-verba hover:bg-button-hover-verba flex gap-2"
                >
                  <MdOutlineSimCardDownload />
                  <p className="sm:hidden md:flex text-xs text-text-verba">
                    {showWholeDocument
                      ? "Show Only Context"
                      : "Show Whole Document"}
                  </p>
                </button>
              </div>
            )}
            {currentDocument.link !== "" && (
              <div className="flex">
                <button
                  onClick={handleSourceClick}
                  className="btn border-none text-text-verba bg-button-verba hover:bg-button-hover-verba flex gap-2"
                >
                  <FaExternalLinkAlt />
                  <p className="sm:hidden md:flex text-xs text-text-verba">
                    Go To Source
                  </p>
                </button>
              </div>
            )}
            {deletable && !production && (
              <div className="flex">
                <button
                  onClick={openDeleteModal}
                  className="btn border-none text-text-verba bg-warning-verba hover:bg-button-hover-verba flex gap-2"
                >
                  <MdDelete />
                  <p className="sm:hidden md:flex text-xs text-text-verba">
                    Delete Document
                  </p>
                </button>
              </div>
            )}
          </div>
        </div>

        {/*Text*/}
        {formattedDocument && (
          <div className="flex flex-col gap-5">
            {showWholeDocument && formattedDocument.beginning !== "" && (
              <ReactMarkdown
                className="prose max-w-prose md:prose-base sm:prose-sm p-3 prose-pre:bg-bg-alt-verba"
                components={{
                  code({ node, inline, className, children, ...props }) {
                    const match = /language-(\w+)/.exec(className || "");
                    return !inline && match ? (
                      <SyntaxHighlighter
                        style={
                          settingConfig.Customization.settings.theme === "dark"
                            ? (oneDark as any)
                            : (oneLight as any)
                        }
                        language={match[1]}
                        PreTag="div"
                        {...props}
                      >
                        {String(children).replace(/\n$/, "")}
                      </SyntaxHighlighter>
                    ) : (
                      <code className={className} {...props}>
                        {children}
                      </code>
                    );
                  },
                }}
              >
                {formattedDocument.beginning}
              </ReactMarkdown>
            )}
            {formattedDocument.substring !== "" && (
              <div
                ref={chunkRef}
                className=" border-secondary-verba border-2 rounded-lg shadow-lg flex gap-2 flex-col p-3"
              >
                <div className="flex w-1/3">
                  <div
                    className={`p-2 flex gap-1 rounded-lg text-text-verba text-sm bg-secondary-verba }`}
                  >
                    <HiMiniSparkles />
                    <p className={`text-xs text-text-verba}`}>Context Used</p>
                  </div>
                </div>
                <ReactMarkdown
                  className="prose md:prose-base sm:prose-sm p-3 prose-pre:bg-bg-alt-verba"
                  components={{
                    code({ node, inline, className, children, ...props }) {
                      const match = /language-(\w+)/.exec(className || "");
                      return !inline && match ? (
                        <SyntaxHighlighter
                          style={
                            settingConfig.Customization.settings.theme ===
                            "dark"
                              ? (oneDark as any)
                              : (oneLight as any)
                          }
                          language={match[1]}
                          PreTag="div"
                          {...props}
                        >
                          {String(children).replace(/\n$/, "")}
                        </SyntaxHighlighter>
                      ) : (
                        <code className={className} {...props}>
                          {children}
                        </code>
                      );
                    },
                  }}
                >
                  {formattedDocument.substring}
                </ReactMarkdown>
              </div>
            )}
            {showWholeDocument && formattedDocument.ending !== "" && (
              <ReactMarkdown
                className="prose md:prose-base sm:prose-sm p-3 prose-pre:bg-bg-alt-verba"
                components={{
                  code({ node, inline, className, children, ...props }) {
                    const match = /language-(\w+)/.exec(className || "");
                    return !inline && match ? (
                      <SyntaxHighlighter
                        style={
                          settingConfig.Customization.settings.theme === "dark"
                            ? (oneDark as any)
                            : (oneLight as any)
                        }
                        language={match[1]}
                        PreTag="div"
                        {...props}
                      >
                        {String(children).replace(/\n$/, "")}
                      </SyntaxHighlighter>
                    ) : (
                      <code className={className} {...props}>
                        {children}
                      </code>
                    );
                  },
                }}
              >
                {formattedDocument.ending}
              </ReactMarkdown>
            )}
          </div>
        )}

        <UserModalComponent
          modal_id="delete_document_modal"
          title="Delete Document"
          text={"Do you want to delete " + currentDocument.name + "?"}
          triggerString="Delete"
          triggerValue={selectedChunk ? selectedChunk.doc_uuid : ""}
          triggerAccept={handleDeleteDocument}
        />
      </div>
    );
  }

  // Add this new return statement for the initial/empty state
  if (!currentDocument && !featureContent && !isFetching) {
    return (
      <div className="flex flex-col bg-bg-alt-verba rounded-lg shadow-lg p-5 text-text-verba sm:h-[53.5vh] lg:h-[65vh] overflow-auto">
        <div className="flex flex-col items-center justify-center h-full text-center">
          <svg className="w-12 h-12 mb-4 text-secondary-verba" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <h2 className="text-xl font-semibold mb-2 text-primary-verba">Welcome to the Document Viewer</h2>
          <p className="text-sm text-text-verba mb-3">Your gateway to insightful document analysis</p>
          <ul className="text-xs text-text-alt-verba">
            <li>• Select a document from the list</li>
            <li>• Use features like Summarize or Visualize</li>
            <li>• Explore context and gain insights</li>
          </ul>
        </div>
      </div>
    );
  }
};

export default DocumentComponent;