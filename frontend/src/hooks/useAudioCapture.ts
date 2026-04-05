import { useCallback, useEffect, useMemo, useRef, useState } from 'react';

export type TranscriptCard = {
  id: string;
  text: string;
  startTsMs: number;
  endTsMs: number;
  speaker: string;
  confidence: number;
  sessionId: string;
  dayId: string;
  provisional: boolean;
};

export type RecordingHealth = {
  status: 'idle' | 'connecting' | 'ok' | 'degraded' | 'reconnecting' | 'failed';
  rms?: number;
  active?: boolean;
  retryCount: number;
  lastError?: string;
};

const WS_PATH = '/ws/audio-stream';

const toPcm16Chunk = (input: Float32Array): ArrayBuffer => {
  const buffer = new ArrayBuffer(input.length * 2);
  const view = new DataView(buffer);
  let offset = 0;

  for (let i = 0; i < input.length; i += 1) {
    const sample = Math.max(-1, Math.min(1, input[i]));
    view.setInt16(offset, sample < 0 ? sample * 0x8000 : sample * 0x7fff, true);
    offset += 2;
  }

  return buffer;
};

export function useAudioCapture(sessionId?: string, dayId?: string) {
  const [cards, setCards] = useState<TranscriptCard[]>([]);
  const [isRecording, setIsRecording] = useState(false);
  const [health, setHealth] = useState<RecordingHealth>({ status: 'idle', retryCount: 0 });

  const wsRef = useRef<WebSocket | null>(null);
  const retryTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const retryCountRef = useRef(0);

  const streamRef = useRef<MediaStream | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const processorRef = useRef<ScriptProcessorNode | null>(null);

  const websocketUrl = useMemo(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const query = new URLSearchParams();
    if (sessionId) query.set('sessionId', sessionId);
    if (dayId) query.set('dayId', dayId);
    return `${protocol}//${host}${WS_PATH}?${query.toString()}`;
  }, [sessionId, dayId]);

  const upsertCard = useCallback((incoming: TranscriptCard) => {
    setCards((prev) => {
      if (incoming.provisional) {
        const existingIdx = prev.findIndex((card) => card.provisional);
        if (existingIdx >= 0) {
          const copy = [...prev];
          copy[existingIdx] = incoming;
          return copy;
        }
        return [...prev, incoming];
      }

      const withoutProvisional = prev.filter((card) => !card.provisional);
      return [...withoutProvisional, incoming];
    });
  }, []);

  const connectWebsocket = useCallback(() => {
    if (wsRef.current && wsRef.current.readyState <= WebSocket.OPEN) return;

    setHealth((h) => ({ ...h, status: retryCountRef.current > 0 ? 'reconnecting' : 'connecting' }));
    const ws = new WebSocket(websocketUrl);
    ws.binaryType = 'arraybuffer';

    ws.onopen = () => {
      retryCountRef.current = 0;
      setHealth((h) => ({ ...h, status: 'ok', retryCount: 0, lastError: undefined }));
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'segment' && data.segment) {
          upsertCard({
            id: `${data.segment.session_id}-${data.segment.start_ts_ms}-${data.segment.end_ts_ms}-${data.provisional ? 'p' : 'f'}`,
            text: data.segment.text,
            startTsMs: data.segment.start_ts_ms,
            endTsMs: data.segment.end_ts_ms,
            speaker: data.segment.speaker,
            confidence: data.segment.confidence,
            sessionId: data.segment.session_id,
            dayId: data.segment.day_id,
            provisional: Boolean(data.provisional),
          });
        }

        if (data.type === 'health') {
          setHealth((h) => ({
            ...h,
            status: data.status === 'ok' ? 'ok' : 'degraded',
            rms: data.rms,
            active: data.active,
            retryCount: data.retryCount ?? retryCountRef.current,
          }));
        }
      } catch (error) {
        setHealth((h) => ({ ...h, status: 'degraded', lastError: String(error) }));
      }
    };

    ws.onclose = () => {
      wsRef.current = null;
      if (!isRecording) return;

      const retries = retryCountRef.current + 1;
      retryCountRef.current = retries;
      const delay = Math.min(1000 * 2 ** Math.min(retries, 6), 15_000);
      setHealth((h) => ({ ...h, status: 'reconnecting', retryCount: retries }));

      retryTimerRef.current = setTimeout(() => {
        connectWebsocket();
      }, delay);
    };

    ws.onerror = () => {
      setHealth((h) => ({ ...h, status: 'degraded' }));
    };

    wsRef.current = ws;
  }, [isRecording, upsertCard, websocketUrl]);

  const start = useCallback(async () => {
    if (isRecording) return;

    connectWebsocket();

    const media = await navigator.mediaDevices.getUserMedia({
      audio: {
        channelCount: 1,
        sampleRate: 16000,
        echoCancellation: true,
        noiseSuppression: true,
      },
      video: false,
    });
    streamRef.current = media;

    const context = new AudioContext({ sampleRate: 16000 });
    audioContextRef.current = context;

    const source = context.createMediaStreamSource(media);
    const processor = context.createScriptProcessor(4096, 1, 1);
    processorRef.current = processor;

    processor.onaudioprocess = (event) => {
      if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
      const input = event.inputBuffer.getChannelData(0);
      wsRef.current.send(toPcm16Chunk(input));
    };

    source.connect(processor);
    processor.connect(context.destination);

    setIsRecording(true);
    setHealth((h) => ({ ...h, status: 'ok' }));
  }, [connectWebsocket, isRecording]);

  const stop = useCallback(() => {
    setIsRecording(false);

    if (processorRef.current) {
      processorRef.current.disconnect();
      processorRef.current.onaudioprocess = null;
      processorRef.current = null;
    }

    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }

    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }

    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'flush' }));
      wsRef.current.close();
    }

    if (retryTimerRef.current) {
      clearTimeout(retryTimerRef.current);
      retryTimerRef.current = null;
    }

    setHealth((h) => ({ ...h, status: 'idle' }));
  }, []);

  useEffect(() => {
    return () => {
      stop();
    };
  }, [stop]);

  return {
    cards,
    isRecording,
    health,
    start,
    stop,
  };
}
