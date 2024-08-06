"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { createClient } from "@/utils/supabase/client";
import Navbar from "./components/Navigation/NavbarComponent";
import SettingsComponent from "./components/Settings/SettingsComponent";
import ChatComponent from "./components/Chat/ChatComponent";
import DocumentViewerComponent from "./components/Document/DocumentViewerComponent";
import StatusComponent from "./components/Status/StatusComponent";
import { Settings, BaseSettings } from "./components/Settings/types";
import RAGComponent from "./components/RAG/RAGComponent";
import { HealthPayload } from "./components/Status/types";
import { RAGConfig, RAGResponse } from "./components/RAG/types";
import { detectHost } from "./api";
import { GoogleAnalytics } from "@next/third-parties/google";
import { fonts, FontKey } from "./info";
import PulseLoader from "react-spinners/PulseLoader";
import MockExamPage from "./mock-exam/page";
import MockExamStartPage from "./components/MockExam/MockExamStartPage";
import AddMocksPage from "./add-mocks/page";

export default function Home() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(null);

  // Page States
  const [currentPage, setCurrentPage] = useState<
    "CHAT" | "DOCUMENTS" | "STATUS" | "ADD" | "SETTINGS" | "RAG" | "MOCK_EXAM_START" | "MOCK_EXAM" | "ADD_MOCKS"
  >("CHAT");

  const [production, setProduction] = useState(false);
  const [gtag, setGtag] = useState("");

  // Settings
  const [settingTemplate, setSettingTemplate] = useState("Default");
  const [baseSetting, setBaseSetting] = useState<Settings | null>(null);

  // RAG Config
  const [RAGConfig, setRAGConfig] = useState<RAGConfig | null>(null);

  const [APIHost, setAPIHost] = useState<string | null>(null);

  const fontKey = baseSetting
    ? (baseSetting[settingTemplate].Customization.settings.font
        .value as FontKey)
    : null;
  const fontClassName = fontKey ? fonts[fontKey]?.className || "" : "";

  useEffect(() => {
    const checkAuth = async () => {
      const supabase = createClient();
      const { data: { session } } = await supabase.auth.getSession();
      
      if (!session) {
        router.push('/login');
      } else {
        setIsAuthenticated(true);
        setUser(session.user);
        await fetchHost();
      }
      setIsLoading(false);
    };

    checkAuth();
  }, [router]);

  const fetchHost = async () => {
    try {
      const host = await detectHost();
      setAPIHost(host);
      if (host === "" || host === "http://localhost:8000") {
        await fetchHealthData(host);
        await fetchConfigData(host);
      }
    } catch (error) {
      console.error("Error detecting host:", error);
      setAPIHost(null);
    }
  };

  const fetchHealthData = async (host: string) => {
    try {
      const health_response = await fetch(host + "/api/health", {
        method: "GET",
      });
      const health_data: HealthPayload = await health_response.json();
      if (health_data) {
        setProduction(health_data.production);
        setGtag(health_data.gtag);
      } else {
        console.warn("Could not retrieve health data");
      }
    } catch (error) {
      console.error("Failed to fetch health data:", error);
    }
  };

  const fetchConfigData = async (host: string) => {
    try {
      const response = await fetch(host + "/api/config", {
        method: "GET",
      });
      const data: RAGResponse = await response.json();
      if (data) {
        if (data.error) {
          console.error(data.error);
        }
        if (data.data.RAG) {
          setRAGConfig(data.data.RAG);
        }
        if (data.data.SETTING.themes) {
          setBaseSetting(data.data.SETTING.themes);
          setSettingTemplate(data.data.SETTING.selectedTheme);
        } else {
          setBaseSetting(BaseSettings);
          setSettingTemplate("Default");
        }
      } else {
        console.warn("Configuration could not be retrieved");
      }
    } catch (error) {
      console.error("Failed to fetch configuration:", error);
      setRAGConfig(null);
    }
  };

  useEffect(() => {
    if (baseSetting) {
      updateDocumentStyles();
    }
  }, [baseSetting, settingTemplate]);

  const updateDocumentStyles = () => {
    if (!baseSetting) return;
    const settings = baseSetting[settingTemplate].Customization.settings;
    document.documentElement.style.setProperty("--primary-verba", settings.primary_color.color);
    document.documentElement.style.setProperty("--secondary-verba", settings.secondary_color.color);
    document.documentElement.style.setProperty("--warning-verba", settings.warning_color.color);
    document.documentElement.style.setProperty("--bg-verba", settings.bg_color.color);
    document.documentElement.style.setProperty("--bg-alt-verba", settings.bg_alt_color.color);
    document.documentElement.style.setProperty("--text-verba", settings.text_color.color);
    document.documentElement.style.setProperty("--text-alt-verba", settings.text_alt_color.color);
    document.documentElement.style.setProperty("--button-verba", settings.button_color.color);
    document.documentElement.style.setProperty("--button-hover-verba", settings.button_hover_color.color);
    document.documentElement.style.setProperty("--bg-console-verba", settings.bg_console.color);
    document.documentElement.style.setProperty("--text-console-verba", settings.text_console.color);
  };

  const importConfig = async () => {
    if (!APIHost || !baseSetting) {
      return;
    }

    try {
      const payload = {
        config: {
          RAG: RAGConfig,
          SETTING: { selectedTheme: settingTemplate, themes: baseSetting },
        },
      };

      await fetch(APIHost + "/api/set_config", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });
    } catch (error) {
      console.error("Failed to update config:", error);
    }
  };

  useEffect(() => {
    importConfig();
  }, [baseSetting, settingTemplate]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen gap-2">
        <PulseLoader loading={true} size={12} speedMultiplier={0.75} />
        <p>Loading Verba</p>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null; // or a custom "Access Denied" component
  }

  return (
    <main
      className={`min-h-screen p-5 bg-bg-verba text-text-verba ${fontClassName}`}
      data-theme={
        baseSetting
          ? baseSetting[settingTemplate].Customization.settings.theme
          : "light"
      }
    >
      {gtag !== "" && <GoogleAnalytics gaId={gtag} />}

      {baseSetting && (
        <div>
          <Navbar
            APIHost={APIHost}
            production={production}
            title={
              baseSetting[settingTemplate].Customization.settings.title.text
            }
            subtitle={
              baseSetting[settingTemplate].Customization.settings.subtitle.text
            }
            imageSrc={
              baseSetting[settingTemplate].Customization.settings.image.src
            }
            version="v1.0.0"
            currentPage={currentPage}
            setCurrentPage={setCurrentPage}
            isAuthenticated={isAuthenticated}
            user={user}
          />

          {currentPage === "CHAT" && (
            <ChatComponent
              production={production}
              settingConfig={baseSetting[settingTemplate]}
              APIHost={APIHost}
              RAGConfig={RAGConfig}
              setCurrentPage={setCurrentPage}
            />
          )}

          {currentPage === "DOCUMENTS" && (
            <DocumentViewerComponent
              RAGConfig={RAGConfig}
              production={production}
              setCurrentPage={setCurrentPage}
              settingConfig={baseSetting[settingTemplate]}
              APIHost={APIHost}
            />
          )}

          {currentPage === "STATUS" && !production && (
            <StatusComponent
              fetchHost={fetchHost}
              settingConfig={baseSetting[settingTemplate]}
              APIHost={APIHost}
            />
          )}

          {currentPage === "ADD" && !production && (
            <RAGComponent
              baseSetting={baseSetting}
              settingTemplate={settingTemplate}
              buttonTitle="Import"
              settingConfig={baseSetting[settingTemplate]}
              APIHost={APIHost}
              RAGConfig={RAGConfig}
              setRAGConfig={setRAGConfig}
              setCurrentPage={setCurrentPage}
              showComponents={["Reader", "Chunker", "Embedder"]}
            />
          )}

          {currentPage === "RAG" && !production && (
            <RAGComponent
              baseSetting={baseSetting}
              settingTemplate={settingTemplate}
              buttonTitle="Save"
              settingConfig={baseSetting[settingTemplate]}
              APIHost={APIHost}
              RAGConfig={RAGConfig}
              setRAGConfig={setRAGConfig}
              setCurrentPage={setCurrentPage}
              showComponents={["Embedder", "Retriever", "Generator"]}
            />
          )}

          {currentPage === "SETTINGS" && !production && (
            <SettingsComponent
              settingTemplate={settingTemplate}
              setSettingTemplate={setSettingTemplate}
              baseSetting={baseSetting}
              setBaseSetting={setBaseSetting}
            />
          )}

          {currentPage === 'MOCK_EXAM_START' && (
            <MockExamStartPage 
              APIHost={APIHost} 
              setCurrentPage={setCurrentPage} 
            />
          )}

          {currentPage === "MOCK_EXAM" && (
            <MockExamPage 
              production={production}
              settingConfig={baseSetting[settingTemplate]} 
              APIHost={APIHost} 
            />
          )}

          {currentPage === "ADD_MOCKS" && !production && (
            <AddMocksPage 
              settingConfig={baseSetting[settingTemplate]} 
              APIHost={APIHost} 
            />
          )}

          <footer className="footer footer-center p-1 mt-2 bg-bg-verba text-text-alt-verba">
            <aside>
              <p>Built with ♥ and Weaviate © 2024</p>
            </aside>
          </footer>
        </div>
      )}
    </main>
  );
}