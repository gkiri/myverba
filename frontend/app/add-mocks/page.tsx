"use client";

import React from 'react';
import AddMocksPageClient from './AddMocksPageClient';
import { SettingsConfiguration } from '@/types/settings';
import { useEffect, useState } from 'react';
import { detectHost } from "../api";

export default function AddMocksPage() {
  const [APIHost, setAPIHost] = useState<string | null>(null);
  const [settingConfig, setSettingConfig] = useState<SettingsConfiguration | null>(null);

  useEffect(() => {
    const fetchHostAndConfig = async () => {
      const host = await detectHost();
      setAPIHost(host);

      // Fetch settingConfig here if needed
      // For now, we'll use a placeholder
      setSettingConfig({
        APIHost: host,
        Customization: {
          settings: {
            text_color: {
              color: '#000000',
            },
          },
        },
      });
    };

    fetchHostAndConfig();
  }, []);

  if (!settingConfig || !APIHost) {
    return <div>Loading...</div>;
  }

  return <AddMocksPageClient settingConfig={settingConfig} APIHost={APIHost} />;
}
