import { useState, useEffect, useCallback, useRef } from 'react';

export interface RealtimeMarketData {
  timestamp?: string;
  stock_id?: number;
  symbol?: string;
  current_price?: number;
  price_change?: number;
  prediction?: {
    current_price?: number;
    predictions?: Array<{
      hour?: number;
      price?: number;
      confidence?: number;
      upper_bound?: number;
      lower_bound?: number;
    }>;
    technical_analysis?: {
      trend?: number;
      volatility?: number;
      rsi?: number;
      momentum?: number;
    };
    recommendation?: "BUY" | "SELL" | "HOLD";
    model_version?: string;
  };
  sentiment?: {
    overall_sentiment?: number;
    sentiment_label?: string;
    positive_articles?: number;
    negative_articles?: number;
    neutral_articles?: number;
    total_articles?: number;
    analyzed_at?: string;
  };
}

export type UseRealtimeMarketDataArgs = {
  stockId?: number;
  enabled?: boolean;
  onData?: (data: RealtimeMarketData) => void;
  onError?: (error: Error) => void;
};

/**
 * React hook for WebSocket real-time market data streaming
 * 
 * @param stockId - Stock ID to stream data for (optional). If not provided, won't connect
 * @param enabled - Whether to enable the connection (default: true)
 * @param onData - Callback when new data arrives
 * @param onError - Callback when error occurs
 * 
 * @returns Object with { data, isConnected, error }
 */
export function useRealtimeMarketData({
  stockId,
  enabled = true,
  onData,
  onError,
}: UseRealtimeMarketDataArgs = {}) {
  const [data, setData] = useState<RealtimeMarketData | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<number | undefined>();

  const connect = useCallback(() => {
    // Don't connect if not enabled or no stockId
    if (!enabled || !stockId) {
      return;
    }

    // Avoid duplicate connections
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    try {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/ws/market-data/${stockId}`;
      
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        console.log(`✓ WebSocket connected for stock ${stockId}`);
        setIsConnected(true);
        setError(null);
      };

      ws.onmessage = (event) => {
        try {
          const newData: RealtimeMarketData = JSON.parse(event.data);
          setData(newData);
          onData?.(newData);
        } catch (err) {
          const parseError = new Error(`Failed to parse WebSocket message: ${err}`);
          setError(parseError);
          onError?.(parseError);
        }
      };

      ws.onerror = () => {
        const wsError = new Error(`WebSocket error for stock ${stockId}`);
        setError(wsError);
        onError?.(wsError);
        setIsConnected(false);
      };

      ws.onclose = () => {
        console.log(`⚠️ WebSocket disconnected for stock ${stockId}`);
        setIsConnected(false);

        // Attempt to reconnect after 3 seconds
        if (enabled && stockId) {
          reconnectTimeoutRef.current = setTimeout(() => {
            console.log(`🔄 Attempting to reconnect to stock ${stockId}...`);
            connect();
          }, 3000);
        }
      };

      wsRef.current = ws;
    } catch (err) {
      const connectError = new Error(`Failed to establish WebSocket connection: ${err}`);
      setError(connectError);
      onError?.(connectError);
    }
  }, [enabled, stockId, onData, onError]);

  useEffect(() => {
    connect();

    return () => {
      // Cleanup
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [connect]);

  return {
    data,
    isConnected,
    error,
  };
}

/**
 * React hook for batch real-time market data (all stocks)
 */
export interface BatchRealtimeMarketData {
  timestamp?: number;
  stocks?: Array<{
    stock_id?: number;
    symbol?: string;
    current_price?: number;
    prediction_recommendation?: "BUY" | "SELL" | "HOLD";
    sentiment_label?: string;
  }>;
}

export type UseBatchRealtimeMarketDataArgs = {
  enabled?: boolean;
  onData?: (data: BatchRealtimeMarketData) => void;
  onError?: (error: Error) => void;
};

export function useBatchRealtimeMarketData({
  enabled = true,
  onData,
  onError,
}: UseBatchRealtimeMarketDataArgs = {}) {
  const [data, setData] = useState<BatchRealtimeMarketData | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<number | undefined>();

  const connect = useCallback(() => {
    if (!enabled) {
      return;
    }

    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    try {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/ws/market-data/batch/all`;
      
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        console.log('✓ Batch WebSocket connected for all stocks');
        setIsConnected(true);
        setError(null);
      };

      ws.onmessage = (event) => {
        try {
          const newData: BatchRealtimeMarketData = JSON.parse(event.data);
          setData(newData);
          onData?.(newData);
        } catch (err) {
          const parseError = new Error(`Failed to parse batch WebSocket message: ${err}`);
          setError(parseError);
          onError?.(parseError);
        }
      };

      ws.onerror = () => {
        const wsError = new Error('Batch WebSocket error');
        setError(wsError);
        onError?.(wsError);
        setIsConnected(false);
      };

      ws.onclose = () => {
        console.log('⚠️ Batch WebSocket disconnected');
        setIsConnected(false);

        if (enabled) {
          reconnectTimeoutRef.current = setTimeout(() => {
            console.log('🔄 Attempting to reconnect to batch...');
            connect();
          }, 3000);
        }
      };

      wsRef.current = ws;
    } catch (err) {
      const connectError = new Error(`Failed to establish batch WebSocket connection: ${err}`);
      setError(connectError);
      onError?.(connectError);
    }
  }, [enabled, onData, onError]);

  useEffect(() => {
    connect();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [connect]);

  return {
    data,
    isConnected,
    error,
  };
}
