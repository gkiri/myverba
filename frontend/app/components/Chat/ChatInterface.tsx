"use client";
import React, { useState, useEffect, useRef } from "react";
import PulseLoader from "react-spinners/PulseLoader";
import { IoMdSend } from "react-icons/io";
import { DocumentChunk } from "../Document/types";
import { Message, QueryPayload } from "./types";
import { getWebSocketApiHost } from "./util";
import ChatMessage from "./ChatMessage";
import { SettingsConfiguration } from "../Settings/types";
import { IoIosRefresh } from "react-icons/io";
import { AiFillRobot } from "react-icons/ai";
import StatusLabel from "./StatusLabel";
import ComponentStatus from "../Status/ComponentStatus";
import { RAGConfig } from "../RAG/types";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

interface ChatInterfaceComponentProps {
  settingConfig: SettingsConfiguration;
  APIHost: string | null;
  setChunks: (c: DocumentChunk[]) => void;
  setChunkTime: (t: number) => void;
  setCurrentPage: (p: any) => void;
  setContext: (c: string) => void;
  RAGConfig: RAGConfig | null;
  production: boolean;
  setMessages: React.Dispatch<React.SetStateAction<Message[]>>;
  messages: Message[];
}

const ChatInterfaceComponent: React.FC<ChatInterfaceComponentProps> = ({
  APIHost,
  settingConfig,
  setChunks,
  setChunkTime,
  setCurrentPage,
  setContext,
  production,
  RAGConfig,
  setMessages,
  messages,
}) => {
  const [previewText, setPreviewText] = useState("");
  const lastMessageRef = useRef<null | HTMLDivElement>(null);
  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [userInput, setUserInput] = useState("");
  const [isFetching, setIsFetching] = useState(false);
  const [fetchingStatus, setFetchingStatus] = useState<"DONE" | "CHUNKS" | "RESPONSE">("DONE");
  const [isFetchingSuggestion, setIsFetchingSuggestions] = useState(false);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [showNotification, setShowNotification] = useState(false);
  const [notificationText, setNotificationText] = useState("");
  const [notificationState, setNotificationState] = useState<"GOOD" | "BAD">(
    "GOOD"
  );

  useEffect(() => {
    setMessages(getMessagesFromLocalStorage("VERBA_CONVERSATION"));
    setChunks(getChunksFromLocalStorage("VERBA_CHUNKS"));
    setContext(getContextFromLocalStorage("VERBA_CONTEXT"));

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
    if (messages.length > 1) {
      saveMessagesToLocalStorage("VERBA_CONVERSATION", messages);
    }
    if (lastMessageRef.current) {
      lastMessageRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages]);

  const handleCopyToBillboard = (text: string) => {
    navigator.clipboard.writeText(text).then(
      function () {
        triggerNotification("Copied message");
      },
      function (err) {
        console.error("Unable to copy text: ", err);
      }
    );
  };

  const triggerNotification = (text: string, warning?: boolean) => {
    if (warning) {
      setNotificationState("BAD");
    } else {
      setNotificationState("GOOD");
    }

    if (showNotification) {
      setNotificationText(text);
      return;
    }

    setNotificationText(text);
    setShowNotification(true);

    setTimeout(() => {
      setShowNotification(false);
      setNotificationText("");
    }, 3000);
  };

  const handleSuggestionClick = async (suggestion: string) => {
    setUserInput(suggestion);
    setSuggestions([]);
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

  const saveMessagesToLocalStorage = (key: string, value: Message[]) => {
    if (typeof window !== "undefined") {
      localStorage.setItem(key, JSON.stringify(value));
    }
  };

  const saveContextToLocalStorage = (key: string, value: string) => {
    if (typeof window !== "undefined") {
      localStorage.setItem(key, value);
    }
  };

  const getMessagesFromLocalStorage = (key: string) => {
    if (typeof window !== "undefined") {
      const saved = localStorage.getItem(key);
      if (saved && JSON.parse(saved).length > 0) {
        return JSON.parse(saved);
      }
    }
    return [
      {
        type: "system",
        content: settingConfig.Customization.settings.intro_message.text,
      },
    ];
  };

  const removeMessagesFromLocalStorage = (key: string) => {
    if (typeof window !== "undefined") {
      localStorage.removeItem(key);
    }
  };

  const saveChunksToLocalStorage = (key: string, value: DocumentChunk[]) => {
    if (typeof window !== "undefined") {
      localStorage.setItem(key, JSON.stringify(value));
    }
  };

  const getChunksFromLocalStorage = (key: string) => {
    try {
      if (typeof window !== "undefined") {
        const saved = localStorage.getItem(key);
        if (saved && JSON.parse(saved).length > 0) {
          return JSON.parse(saved);
        }
      }
    } catch (e) {
      console.error("Failed to load chunks from local storage:", e);
      return [];
    }
    return [];
  };

  const getContextFromLocalStorage = (key: string) => {
    try {
      if (typeof window !== "undefined") {
        const saved = localStorage.getItem(key);
        if (saved) {
          return saved;
        }
      }
    } catch (e) {
      console.error("Failed to load context from local storage:", e);
      return "";
    }
    return "";
  };

  const removeChunksFromLocalStorage = (key: string) => {
    if (typeof window !== "undefined") {
      localStorage.removeItem(key);
    }
  };

  const handleSendMessage = async () => {
    if (APIHost === null) {
      triggerNotification("No connection to server");
      return;
    }

    if (isFetching) {
      return;
    }

    const sendInput = userInput;

    if (sendInput.trim()) {
      setMessages((prev) => [...prev, { type: "user", content: sendInput }]);
      setUserInput("");

      const textarea = document.getElementById("reset");
      if (textarea !== null) {
        textarea.style.height = "";
        textarea.style.width = "";
      } else {
        console.error('The element with ID "reset" was not found in the DOM.');
      }

      try {
        setIsFetching(true);
        setFetchingStatus("CHUNKS");

        const response = await fetch(APIHost + "/api/query", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ query: sendInput }),
        });

        const data: QueryPayload = await response.json();

        if (data) {
          if (data.error !== "") {
            triggerNotification(data.error, true);
          }

          setChunks(data.chunks);
          saveChunksToLocalStorage("VERBA_CHUNKS", data.chunks);
          setSuggestions([]);
          setChunkTime(data.took);

          if (data.context) {
            streamResponses(sendInput, data.context);
            setContext(data.context);
            saveContextToLocalStorage("VERBA_CONTEXT", data.context);
            setFetchingStatus("RESPONSE");
          }
        } else {
          triggerNotification(
            "Failed to fetch from API: No data received",
            true
          );
          setIsFetching(false);
          setFetchingStatus("DONE");
        }
      } catch (error) {
        console.error("Failed to fetch from API:", error);
        triggerNotification("Failed to fetch from API: " + error, true);
        setIsFetching(false);
        setFetchingStatus("DONE");
      }
    }
  };

  const fetchSuggestions = async (query: string) => {
    if (
      isFetchingSuggestion ||
      query === "" ||
      isFetching ||
      !settingConfig.Chat.settings.suggestion.checked
    ) {
      setSuggestions([]);
      return;
    }

    try {
      setIsFetchingSuggestions(true);
      const response = await fetch(APIHost + "/api/suggestions", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ query }),
      });

      const data = await response.json();

      if (data) {
        setSuggestions(data.suggestions);
        setIsFetchingSuggestions(false);
      } else {
        setIsFetchingSuggestions(false);
      }
    } catch (error) {
      console.error("Failed to fetch suggestions:", error);
      setIsFetchingSuggestions(false);
    }
  };

  const escapeRegExp = (string: string) => {
    return string.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  };

  const renderBoldedSuggestion = (suggestion: string, userInput: string) => {
    const escapedUserInput = escapeRegExp(userInput);
    const parts = suggestion.split(new RegExp(`(${escapedUserInput})`, "gi"));
    return (
      <div className="flex flex-row gap-1">
        {parts.map((part, i) => (
          <p
            key={i}
            className={
              part.toLowerCase() === userInput.toLowerCase()
                ? "font-bold text-sm"
                : ""
            }
          >
            {part}
          </p>
        ))}
      </div>
    );
  };

return (
  <Card className="flex flex-col h-[calc(100vh-2rem)] bg-gradient-to-br from-indigo-50 to-blue-100 dark:from-gray-900 dark:to-indigo-900 shadow-2xl rounded-xl overflow-hidden">
    <CardContent className="flex flex-col h-full p-0">
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
          <div className="flex items-center space-x-2">
            <StatusLabel
              status={settingConfig.Chat.settings.caching.checked}
              true_text="Caching"
              false_text="No Caching"
            />
            <StatusLabel
              status={settingConfig.Chat.settings.suggestion.checked}
              true_text="Suggestions"
              false_text="No Suggestions"
            />
          </div>
        </div>
      </div>

      <div className="flex-grow overflow-auto p-3 space-y-3">
        {messages.map((message, index) => (
          <div
            key={index}
            ref={index === messages.length - 1 ? lastMessageRef : null}
            className={`flex ${message.type === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-3/4 p-3 rounded-lg ${
                message.type === "user"
                  ? "bg-blue-500 text-white"
                  : "bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-200"
              } shadow-md`}
            >
              <ChatMessage
                message={message}
                handleCopyToBillboard={handleCopyToBillboard}
                settingConfig={settingConfig}
              />
            </div>
          </div>
        ))}
        {previewText && (
          <div className="flex justify-start">
            <div className="max-w-3/4 p-3 rounded-lg bg-gray-100 dark:bg-gray-600 text-gray-800 dark:text-gray-200 shadow-md">
              <ChatMessage
                settingConfig={settingConfig}
                message={{ type: "system", content: previewText, cached: false }}
                handleCopyToBillboard={handleCopyToBillboard}
              />
            </div>
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

      <div className="bg-white dark:bg-gray-800 bg-opacity-70 dark:bg-opacity-70 backdrop-blur-sm p-2 border-t border-gray-200 dark:border-gray-700">
        <form
          className="flex items-center space-x-2"
          onSubmit={(e) => {
            e.preventDefault();
            handleSendMessage();
          }}
        >
          <Input
            id="reset"
            placeholder={`Ask ${settingConfig.Customization.settings.title.text} anything`}
            value={userInput}
            onChange={(e) => {
              setUserInput(e.target.value);
              fetchSuggestions(e.target.value);
            }}
            onKeyDown={handleKeyDown}
            className="flex-grow bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 rounded-full py-2 px-4"
          />
          <Button type="submit" size="icon" className="bg-blue-500 hover:bg-blue-600 text-white rounded-full">
            <IoMdSend size={18} />
          </Button>
          <Button
            type="button"
            size="icon"
            variant="outline"
            onClick={() => {
              removeMessagesFromLocalStorage("VERBA_CONVERSATION");
              removeChunksFromLocalStorage("VERBA_CHUNKS");
              removeChunksFromLocalStorage("VERBA_CONTEXT");
              setChunks([]);
              setMessages([
                {
                  type: "system",
                  content: settingConfig.Customization.settings.intro_message.text,
                },
              ]);
              setUserInput("");
              setSuggestions([]);
              setContext("");
            }}
            className="border-gray-300 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-full"
          >
            <IoIosRefresh size={18} />
          </Button>
        </form>
      </div>
    </CardContent>

    {suggestions.length > 0 && (
      <div className="bg-white dark:bg-gray-800 bg-opacity-70 dark:bg-opacity-70 backdrop-blur-sm p-2 border-t border-gray-200 dark:border-gray-700">
        <div className="flex flex-wrap gap-2">
          {suggestions.map((suggestion, index) => (
            <Button
              key={index + suggestion}
              variant="secondary"
              size="sm"
              className="bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-200 rounded-full text-xs"
              onClick={() => handleSuggestionClick(suggestion)}
            >
              {renderBoldedSuggestion(suggestion, userInput)}
            </Button>
          ))}
        </div>
      </div>
    )}

    {showNotification && (
      <div
        className={`animate-pop-in fixed bottom-4 right-4 ${
          notificationState === "GOOD" ? "bg-green-500" : "bg-red-500"
        } text-white p-3 rounded-lg text-sm shadow-lg`}
      >
        <p>{notificationText}</p>
      </div>
    )}
  </Card>
);
};

export default ChatInterfaceComponent;
