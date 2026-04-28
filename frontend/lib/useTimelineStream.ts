'use client';

import { useCallback, useEffect, useRef } from 'react';
import { timelineWsEndpoint } from './api';

export type TimelineEvent = {
  event: 'created' | 'updated' | string;
  item_id: number;
};

/**
 * Opens a WebSocket connection to the backend timeline stream and calls
 * `onEvent` whenever a new event is received.
 *
 * The connection is automatically re-established when the component mounts
 * and torn down when it unmounts. Reconnect is attempted after a delay if
 * the connection drops unexpectedly.
 */
export function useTimelineStream(onEvent: (e: TimelineEvent) => void): void {
  const onEventRef = useRef(onEvent);

  useEffect(() => {
    onEventRef.current = onEvent;
  }, [onEvent]);

  useEffect(() => {
    let ws: WebSocket | null = null;
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
    let cancelled = false;

    function connect(): void {
      ws = new WebSocket(timelineWsEndpoint());

      ws.onmessage = (msg) => {
        try {
          const data = JSON.parse(msg.data as string) as TimelineEvent;
          onEventRef.current(data);
        } catch {
          // ignore malformed frames
        }
      };

      ws.onclose = () => {
        if (!cancelled) {
          reconnectTimer = setTimeout(connect, 3000);
        }
      };
    }

    connect();

    return () => {
      cancelled = true;
      if (reconnectTimer) clearTimeout(reconnectTimer);
      ws?.close();
    };
  }, []);
}

/**
 * Returns a stable callback that wraps `fn` so callers can pass it as a
 * dependency without causing re-subscriptions.
 */
export function useStableCallback<T extends (...args: never[]) => unknown>(fn: T): T {
  const ref = useRef(fn);
  ref.current = fn;
  return useCallback((...args: Parameters<T>) => ref.current(...args), []) as T;
}
