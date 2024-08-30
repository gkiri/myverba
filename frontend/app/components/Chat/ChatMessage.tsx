"use client";

import React from "react";
import { Message } from "./types";
import ReactMarkdown from "react-markdown";
import { FaDatabase } from "react-icons/fa";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import {
  oneDark,
  oneLight,
} from "react-syntax-highlighter/dist/cjs/styles/prism";
import { SettingsConfiguration } from "../Settings/types";

interface ChatMessageProps {
  message: Message;
  handleCopyToBillboard: (m: string) => void;
  settingConfig: SettingsConfiguration;
}

const ChatMessage: React.FC<ChatMessageProps> = ({
  message,
  handleCopyToBillboard,
  settingConfig,
}) => {
  return (
    <div
      className={`flex ${
        message.type === "user" ? "justify-end" : "justify-start"
      } mb-4`}
    >
      <div
        className={`max-w-3/4 p-3 rounded-lg ${
          message.type === "user"
            ? "bg-gray-200 text-gray-800"
            : "bg-blue-100 text-gray-800 dark:bg-blue-800 dark:text-gray-200"
        } shadow-md animate-press-in text-base font-sans`}
      >
        {message.cached && <FaDatabase size={12} className="text-text-verba" />}
        {message.type === "system" ? (
          <ReactMarkdown
            components={{
              code({ node, inline, className, children, ...props }) {
                const match = /language-(\w+)/.exec(className || "");
                return !inline && match ? (
                  <SyntaxHighlighter
                    {...props}
                    style={
                      settingConfig.Customization.settings.theme === "dark"
                        ? oneDark
                        : oneLight
                    }
                    language={match[1]}
                    PreTag="div"
                  >
                    {String(children).replace(/\n$/, "")}
                  </SyntaxHighlighter>
                ) : (
                  <code {...props} className={className}>
                    {children}
                  </code>
                );
              },
            }}
          >
            {message.content}
          </ReactMarkdown>
        ) : (
          <div className="whitespace-pre-wrap">{message.content}</div> // Use whitespace-pre-wrap for user messages
        )}
      </div>
      {message.type === "system" && (
        <button
          onClick={() => handleCopyToBillboard(message.content)}
          className="ml-2 text-sm text-indigo-600 hover:text-indigo-800 dark:text-indigo-400 dark:hover:text-indigo-200 font-sans"
        >
          Copy
        </button>
      )}
    </div>
  );
};

export default ChatMessage;
