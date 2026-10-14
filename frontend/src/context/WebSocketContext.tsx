import React, { createContext, useContext, useEffect, useState, useRef, useCallback } from 'react';
import { useAuth } from './AuthContext';
import { DashboardKPIs, WebSocketLiveMessage } from '../types';

interface LiveAlertsSummary {
  near_expiry_count: number;
  low_stock_count: number;
  out_of_stock_count: number;
  expired_count?: number;
}

interface WebSocketContextType {
  isConnected: boolean;
  liveKpis: DashboardKPIs | null;
  liveAlertsSummary: LiveAlertsSummary | null;
  lastEvent: WebSocketLiveMessage | null;
  requestKpis: () => void;
  requestAlerts: () => void;
  reconnect: () => void;
}

const WebSocketContext = createContext<WebSocketContextType | undefined>(undefined);

export const WebSocketProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { token, isAuthenticated } = useAuth();
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [liveKpis, setLiveKpis] = useState<DashboardKPIs | null>(null);
  const [liveAlertsSummary, setLiveAlertsSummary] = useState<LiveAlertsSummary | null>(null);
  const [lastEvent, setLastEvent] = useState<WebSocketLiveMessage | null>(null);

  const socketRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const pingIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const reconnectAttemptsRef = useRef<number>(0);

  const connect = useCallback(() => {
    if (!isAuthenticated || !token) {
      if (socketRef.current) {
        socketRef.current.close();
        socketRef.current = null;
      }
      setIsConnected(false);
      return;
    }

    if (socketRef.current && (socketRef.current.readyState === WebSocket.OPEN || socketRef.current.readyState === WebSocket.CONNECTING)) {
      return;
    }

    try {
      const isSecure = window.location.protocol === 'https:';
      const wsProtocol = isSecure ? 'wss:' : 'ws:';
      // In Vite dev mode with proxy, window.location.host routes via port 5173
      const wsHost = window.location.host;
      const wsUrl = `${wsProtocol}//${wsHost}/api/v1/ws?token=${encodeURIComponent(token)}`;

      const ws = new WebSocket(wsUrl);
      socketRef.current = ws;

      ws.onopen = () => {
        setIsConnected(true);
        reconnectAttemptsRef.current = 0;

        // Start ping heartbeat
        if (pingIntervalRef.current) clearInterval(pingIntervalRef.current);
        pingIntervalRef.current = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'PING' }));
          }
        }, 25000);
      };

      ws.onmessage = (event) => {
        try {
          const message: WebSocketLiveMessage = JSON.parse(event.data);
          setLastEvent(message);

          if (message.type === 'CONNECTED') {
            setIsConnected(true);
          } else if (message.type === 'INITIAL_STATE' && message.data) {
            setIsConnected(true);
            if (message.data.kpis) {
              setLiveKpis(message.data.kpis);
            }
            if (message.data.alerts_summary) {
              setLiveAlertsSummary(message.data.alerts_summary);
            }
          } else if (message.type === 'KPIS_UPDATE' && message.data) {
            setLiveKpis(message.data);
          } else if (message.type === 'ALERTS_UPDATE' && message.data) {
            setLiveAlertsSummary(message.data);
          } else if (
            message.type === 'SALE_COMPLETED' ||
            message.type === 'SALE_CANCELLED' ||
            message.type === 'BATCH_RECEIVED' ||
            message.type === 'STOCK_ADJUSTED' ||
            message.type === 'ALERT_UPDATED'
          ) {
            // Live inventory mutation received: request fresh KPIs and alert summaries immediately
            if (ws.readyState === WebSocket.OPEN) {
              ws.send(JSON.stringify({ type: 'REQUEST_KPIS' }));
              ws.send(JSON.stringify({ type: 'REQUEST_ALERTS' }));
            }
          }
        } catch (err) {
          console.warn('Error parsing WebSocket message:', err);
        }
      };

      ws.onerror = () => {
        setIsConnected(false);
      };

      ws.onclose = () => {
        setIsConnected(false);
        if (pingIntervalRef.current) clearInterval(pingIntervalRef.current);

        // Exponential backoff reconnect (max 10s)
        if (isAuthenticated) {
          const timeout = Math.min(1000 * Math.pow(1.5, reconnectAttemptsRef.current), 10000);
          reconnectAttemptsRef.current += 1;
          if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, timeout);
        }
      };
    } catch (err) {
      console.warn('WebSocket connection attempt error:', err);
      setIsConnected(false);
    }
  }, [token, isAuthenticated]);

  useEffect(() => {
    // 50ms mount debounce prevents StrictMode double-mounting connection churn
    const timer = setTimeout(() => {
      connect();
    }, 50);

    return () => {
      clearTimeout(timer);
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
      if (pingIntervalRef.current) clearInterval(pingIntervalRef.current);
      if (socketRef.current) {
        socketRef.current.close();
        socketRef.current = null;
      }
      setIsConnected(false);
    };
  }, [connect]);

  const requestKpis = useCallback(() => {
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify({ type: 'REQUEST_KPIS' }));
    }
  }, []);

  const requestAlerts = useCallback(() => {
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify({ type: 'REQUEST_ALERTS' }));
    }
  }, []);

  const reconnect = useCallback(() => {
    if (socketRef.current) {
      socketRef.current.close();
    }
    reconnectAttemptsRef.current = 0;
    connect();
  }, [connect]);

  return (
    <WebSocketContext.Provider
      value={{
        isConnected,
        liveKpis,
        liveAlertsSummary,
        lastEvent,
        requestKpis,
        requestAlerts,
        reconnect,
      }}
    >
      {children}
    </WebSocketContext.Provider>
  );
};

export const useWebSocket = () => {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error('useWebSocket must be used within a WebSocketProvider');
  }
  return context;
};
