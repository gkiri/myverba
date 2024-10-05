import React, { useState, useEffect, useRef } from "react";
import PulseLoader from "react-spinners/PulseLoader";
import { IoMdSend } from "react-icons/io";
import { IoIosRefresh } from "react-icons/io";
import { AiFillRobot } from "react-icons/ai";
import { DocumentChunk } from "../Document/types";
import { Message, QueryPayload } from "../Chat/types";
import { getWebSocketApiHost } from "../Chat/util";
import ChatMessage from "../Chat/ChatMessage";
import { SettingsConfiguration } from "../Settings/types";
import StatusLabel from "../Chat/StatusLabel";
import ComponentStatus from "../Status/ComponentStatus";
import { RAGConfig } from "../RAG/types";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

interface AIMentorChatInterfaceProps {
  settingConfig: SettingsConfiguration;
  APIHost: string | null;
  setCurrentPage: (p: any) => void;
  RAGConfig: RAGConfig | null;
  production: boolean;
  initialMessage: string;
  isInitialMessage: boolean;
}

const AIMentorChatInterface: React.FC<AIMentorChatInterfaceProps> = ({
  APIHost,
  settingConfig,
  setCurrentPage,
  RAGConfig,
  production,
  initialMessage,
  isInitialMessage,
}) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      type: "system",
      content: "Welcome to AI Mentor! How can I assist you with your UPSC preparation today?",
    },
  ]);
  const [userInput, setUserInput] = useState("");
  const [isFetching, setIsFetching] = useState(false);
  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [previewText, setPreviewText] = useState("");
  const lastMessageRef = useRef<null | HTMLDivElement>(null);
  const [fetchingStatus, setFetchingStatus] = useState<"DONE" | "CHUNKS" | "RESPONSE">("DONE");
  const [showNotification, setShowNotification] = useState(false);
  const [notificationText, setNotificationText] = useState("");
  const [notificationState, setNotificationState] = useState<"GOOD" | "BAD">("GOOD");

  useEffect(() => {
    if (isInitialMessage && initialMessage) {
      const greetingMessage = "Welcome to AI Mentor! How can I assist you with your UPSC preparation today?";
      const combinedMessage = `${greetingMessage}\n\n${initialMessage}`;
      setMessages([
        {
          type: "system",
          content: combinedMessage,
        },
      ]);
    }
  }, [isInitialMessage, initialMessage]);

  useEffect(() => {
    const socketHost = getWebSocketApiHost();
    const localSocket = new WebSocket(socketHost);

    localSocket.onopen = () => {
      console.log("WebSocket connection opened to " + socketHost);
      triggerNotification("WebSocket Online");
    };

    localSocket.onmessage = (event) => {
      let data;
      try {
        data = JSON.parse(event.data);
      } catch (e) {
        console.error("Received data is not valid JSON:", event.data);
        return;
      }
      const newMessageContent = data.message;
      setPreviewText((prev) => prev + newMessageContent);

      if (data.finish_reason === "stop") {
        setIsFetching(false);
        setFetchingStatus("DONE");
        const full_text = data.full_text;
        const newMessage: Message = {
          type: "system",
          content: full_text,
          cached: data.cached,
          distance: data.distance,
        };
        setMessages((prev) => [...prev, newMessage]);
        setPreviewText("");
      }
    };

    localSocket.onerror = (error) => {
      console.error("WebSocket Error:", error);
      triggerNotification("WebSocket Error: " + error, true);
      setIsFetching(false);
      setFetchingStatus("DONE");
    };

    localSocket.onclose = (event) => {
      if (event.wasClean) {
        console.log(
          `WebSocket connection closed cleanly, code=${event.code}, reason=${event.reason}`
        );
      } else {
        console.error("WebSocket connection died");
      }
      triggerNotification("WebSocket Connection Offline", true);
      setIsFetching(false);
      setFetchingStatus("DONE");
    };

    setSocket(localSocket);

    return () => {
      if (localSocket.readyState !== WebSocket.CLOSED) {
        localSocket.close();
      }
    };
  }, []);

  useEffect(() => {
    if (lastMessageRef.current) {
      lastMessageRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages]);

  const triggerNotification = (text: string, warning?: boolean) => {
    if (warning) {
      setNotificationState("BAD");
    } else {
      setNotificationState("GOOD");
    }

    setNotificationText(text);
    setShowNotification(true);

    setTimeout(() => {
      setShowNotification(false);
      setNotificationText("");
    }, 3000);
  };

  const handleSendMessage = async () => {
    if (APIHost === null || isFetching || !userInput.trim()) return;

    setMessages((prev) => [...prev, { type: "user", content: userInput }]);
    setUserInput("");

    try {
      setIsFetching(true);
      setFetchingStatus("CHUNKS");

      const response = await fetch(`${APIHost}/api/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: userInput }),
      });

      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

      const data: QueryPayload = await response.json();

      if (data) {
        if (data.error !== "") {
          triggerNotification(data.error, true);
        }

        if (data.context) {
          streamResponses(userInput, data.context);
          setFetchingStatus("DONE");
        }
      } else {
        triggerNotification("Failed to fetch from API: No data received", true);
        setIsFetching(false);
        setFetchingStatus("DONE");
      }
    } catch (error) {
      console.error("Failed to fetch from API:", error);
      triggerNotification("Failed to fetch from API: " + error, true);
      setIsFetching(false);
      setFetchingStatus("DONE");
    }
  };

  const streamResponses = (query?: string, context?: string) => {
    if (socket?.readyState === WebSocket.OPEN) {
      const data = JSON.stringify({
        query: query,
        context: context,
        conversation: messages,
      });
      socket.send(data);
    } else {
      console.error("WebSocket is not open. ReadyState:", socket?.readyState);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="flex flex-col h-full w-full bg-white dark:bg-gray-800 shadow-2xl rounded-xl overflow-hidden font-sans">
      <div className="flex flex-col h-full">
        <div className="bg-white dark:bg-gray-800 bg-opacity-70 dark:bg-opacity-70 backdrop-blur-sm p-2 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              {RAGConfig && (
                <ComponentStatus
                  disable={production}
                  component_name={RAGConfig ? RAGConfig["Generator"].selected : ""}
                  Icon={AiFillRobot}
                  changeTo={"RAG"}
                  changePage={setCurrentPage}
                />
              )}
              <StatusLabel
                status={APIHost !== null && socket !== null && socket.readyState === WebSocket.OPEN}
                true_text="Online"
                false_text="Connecting..."
              />
            </div>
          </div>
        </div>

        <div className="flex-grow overflow-y-auto p-3 space-y-3">
          {messages.map((message, index) => (
            <div
              key={index}
              ref={index === messages.length - 1 ? lastMessageRef : null}
              className={`flex ${message.type === "user" ? "justify-end" : "justify-start"} mb-4`}
            >
              <ChatMessage
                message={message}
                handleCopyToBillboard={() => {}}
                settingConfig={settingConfig}
              />
            </div>
          ))}
          {previewText && (
            <div className="flex justify-start">
              <ChatMessage
                settingConfig={settingConfig}
                message={{ type: "system", content: previewText, cached: false }}
                handleCopyToBillboard={() => {}}
              />
            </div>
          )}
          {isFetching && (
            <div className="flex items-center justify-center space-x-2 text-gray-500 dark:text-gray-400">
              <PulseLoader
                color={settingConfig.Customization.settings.text_color.color}
                loading={true}
                size={8}
                speedMultiplier={0.75}
              />
              <p className="text-sm">
                {fetchingStatus === "CHUNKS" ? "Retrieving chunks" : "Generating answer"}
              </p>
            </div>
          )}
        </div>

        <div className="bg-white dark:bg-gray-800 bg-opacity-70 dark:bg-opacity-70 backdrop-blur-sm p-4 border-t border-gray-200 dark:border-gray-700">
          <form
            className="flex items-center space-x-2"
            onSubmit={(e) => {
              e.preventDefault();
              handleSendMessage();
            }}
          >
            <Input
              placeholder="Ask AI Mentor about UPSC preparation..."
              value={userInput}
              onChange={(e) => setUserInput(e.target.value)}
              onKeyDown={handleKeyDown}
              className="flex-grow bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 rounded-full py-2 px-4 font-sans text-sm"
            />
            <Button type="submit" size="icon" className="bg-indigo-600 hover:bg-indigo-700 text-white rounded-full">
              <IoMdSend size={18} />
            </Button>
            <Button
              type="button"
              size="icon"
              variant="outline"
              onClick={() => {
                setMessages([
                  {
                    type: "system",
                    content: "Welcome to AI Mentor! How can I assist you with your UPSC preparation today?",
                  },
                ]);
                setUserInput("");
              }}
              className="border-gray-300 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-full"
            >
              <IoIosRefresh size={18} />
            </Button>
          </form>
        </div>
      </div>

      {showNotification && (
        <div
          className={`animate-pop-in fixed bottom-4 right-4 ${
            notificationState === "GOOD" ? "bg-green-500" : "bg-red-500"
          } text-white p-3 rounded-lg text-sm shadow-lg`}
        >
          <p>{notificationText}</p>
        </div>
      )}
    </div>
  );
};

export default AIMentorChatInterface;