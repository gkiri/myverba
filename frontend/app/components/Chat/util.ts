export const getWebSocketApiHost = () => {
  if (process.env.NEXT_PUBLIC_WS_HOST) {
    return process.env.NEXT_PUBLIC_WS_HOST;
  }

  if (typeof window !== 'undefined') {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = window.location.host;
    return `${protocol}//${host}`;
  }

  // Fallback for server-side rendering
  return "ws://localhost:8000";
};


