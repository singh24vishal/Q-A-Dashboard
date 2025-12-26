
import { useEffect, useRef } from "react";

export default function WebSocketClient({ onEvent }) {
  const wsRef = useRef(null);
  const reconnectTimerRef = useRef(null);

  useEffect(() => {
    const base = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000";
    const url = `${base.replace(/\/$/, "")}/ws`;

    let shouldReconnect = true;

    const connect = () => {
      console.debug("[WS] connecting to", url);
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        console.debug("[WS] connected");
      };

      ws.onmessage = (evt) => {
        try {
          const parsed = JSON.parse(evt.data);
          if (parsed && parsed.event) {
            onEvent(parsed.event, parsed.payload);
          } else {
            onEvent("new_question", parsed);
          }
        } catch (err) {
          onEvent("raw", evt.data);
        }
      };

      ws.onerror = (err) => {
        console.error("[WS] error", err);
      };

      ws.onclose = (e) => {
        console.warn("[WS] closed", e.code, e.reason);
        if (shouldReconnect) {
          if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current);
          reconnectTimerRef.current = setTimeout(connect, 1500);
        }
      };
    };

    connect();

    return () => {
      shouldReconnect = false;
      if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current);
      try { wsRef.current && wsRef.current.close(); } catch (e) {}
    };
  }, [onEvent]);

  return null;
}
