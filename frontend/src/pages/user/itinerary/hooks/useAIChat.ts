import { useState, useEffect, useCallback, useRef } from 'react';
import type { ChatMessage, StreamEvent } from '@/types/chat';
import { chatService } from '@/services/chatService';

interface UseAIChatOptions {
  onDraftReceived?: (draftData: any[]) => void;
}

export const useAIChat = (tripId: string, options?: UseAIChatOptions) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [currentThought, setCurrentThought] = useState<string>('');
  const [isThinking, setIsThinking] = useState<boolean>(false);

  // Refs for simulating smooth typewriter streaming
  const eventSourceRef = useRef<EventSource | null>(null);
  const streamBufferRef = useRef<string>('');
  const flushIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const isStreamCompleteRef = useRef<boolean>(false);

  useEffect(() => {
    let mounted = true;
    const fetchHistory = async () => {
      try {
        const history = await chatService.getChatHistory(tripId);
        if (mounted) {
          setMessages(history.messages);
        }
      } catch (err) {
        console.error("Failed to fetch chat history", err);
      }
    };
    fetchHistory();
    
    return () => {
      mounted = false;
    };
  }, [tripId]);

  const connectStream = useCallback(() => {
    if (eventSourceRef.current && eventSourceRef.current.readyState !== EventSource.CLOSED) {
      return;
    }
    // Assuming backend FastAPI runs on an accessible route. We might need to proxy this or use full URL.
    const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
    const token = localStorage.getItem('access_token');
    const sseUrl = `${baseUrl}/api/v1/ai-stream/chat/${tripId}/stream${token ? `?token=${token}` : ''}`;

    eventSourceRef.current = new EventSource(sseUrl);

    eventSourceRef.current.onopen = () => {
      console.log("[SSE] Connection opened to:", sseUrl);
    };

    eventSourceRef.current.onerror = (error) => {
      console.error("[SSE] Connection error:", error);
    };

    eventSourceRef.current.onmessage = (event) => {
      console.log("[SSE] Raw event received:", event.data);
      try {
        const data: StreamEvent = JSON.parse(event.data);
        console.log("[SSE] Parsed event:", data.type, data);

        switch (data.type) {
          case 'thought':
            setIsThinking(true);
            setCurrentThought((prev) => prev + '\n' + data.content);
            break;

          case 'token':
            setIsThinking(true); // Ensure thinking stays true until 'done'
            streamBufferRef.current += data.content;
            
            // Start the typewriter loop if it's not already running
            if (!flushIntervalRef.current) {
              flushIntervalRef.current = setInterval(() => {
                if (streamBufferRef.current.length > 0) {
                  // Pop 2 characters at a time for a natural reading speed
                  const chars = streamBufferRef.current.substring(0, 2);
                  streamBufferRef.current = streamBufferRef.current.substring(2);
                  
                  setMessages((prev) => {
                    const lastMsg = prev[prev.length - 1];
                    if (lastMsg && lastMsg.role === 'agent' && lastMsg.isStreaming) {
                      const updated = [...prev];
                      updated[updated.length - 1] = {
                        ...lastMsg,
                        content: lastMsg.content + chars
                      };
                      return updated;
                    } else {
                      return [...prev, { id: crypto.randomUUID(), role: 'agent', content: chars, isStreaming: true }];
                    }
                  });
                } else if (isStreamCompleteRef.current) {
                  // Buffer is empty AND stream is done -> finalize the bubble
                  setMessages((prev) => {
                    const updated = [...prev];
                    if (updated.length > 0 && updated[updated.length - 1].isStreaming) {
                      updated[updated.length - 1].isStreaming = false;
                    }
                    return updated;
                  });
                  if (flushIntervalRef.current) {
                    clearInterval(flushIntervalRef.current);
                    flushIntervalRef.current = null;
                  }
                  isStreamCompleteRef.current = false;
                }
              }, 15); // 15ms per 2 chars is smoother and prevents huge backlogs
            }
            break;

          case 'draft_update':
            try {
              const draftData = JSON.parse(data.content);
              if (options?.onDraftReceived) {
                options.onDraftReceived(draftData);
              }
            } catch (e) {
              console.error("Failed to parse draft_update", e);
            }
            break;

          case 'new_run':
            // Instantly flush the remaining buffer for the OLD run, so the new run gets a fresh bubble
            if (streamBufferRef.current.length > 0) {
              const remaining = streamBufferRef.current;
              streamBufferRef.current = '';
              setMessages((prev) => {
                const updated = [...prev];
                if (updated.length > 0 && updated[updated.length - 1].isStreaming) {
                  const lastMsg = updated[updated.length - 1];
                  updated[updated.length - 1] = {
                    ...lastMsg,
                    content: lastMsg.content + remaining,
                    isStreaming: false
                  };
                }
                return updated;
              });
            } else {
              setMessages((prev) => {
                const updated = [...prev];
                if (updated.length > 0 && updated[updated.length - 1].isStreaming) {
                  updated[updated.length - 1].isStreaming = false;
                }
                return updated;
              });
            }
            break;

          case 'done':
            // Just mark the stream as complete. The interval will drain the buffer and close it naturally.
            isStreamCompleteRef.current = true;
            setIsThinking(false);
            setCurrentThought('');
            if (eventSourceRef.current) {
              eventSourceRef.current.close();
            }
            break;

          case 'tool_call':
            setIsThinking(true);
            setCurrentThought((prev) => prev + `\n> Calling Tool: ${data.content}...`);
            break;

          case 'error':
            setIsThinking(false);
            setMessages((prev) => [...prev, { id: crypto.randomUUID(), role: 'agent', content: `**Error:** ${data.content}` }]);
            break;

          // In a full implementation, we might listen for an "end" event to set isStreaming to false.
        }
      } catch (err) {
        console.error("Error parsing SSE data", err);
      }
    };

    eventSourceRef.current.onerror = (err) => {
      console.error("SSE Connection Error", err);
      // Let it automatically reconnect
    };
  }, [tripId]);

  useEffect(() => {
    connectStream();
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
      if (flushIntervalRef.current) {
        clearInterval(flushIntervalRef.current);
        flushIntervalRef.current = null;
      }
    };
  }, [connectStream]);

  const sendMessage = useCallback(async (text: string, workspaceDraft?: any) => {
    // Optimistically add user message
    setMessages(prev => [...prev, { id: crypto.randomUUID(), role: 'user', content: text }]);

    // Finalize any currently streaming agent message
    setMessages(prev => {
      const updated = [...prev];
      if (updated.length > 0 && updated[updated.length - 1].isStreaming) {
        updated[updated.length - 1].isStreaming = false;
      }
      return updated;
    });

    try {
      connectStream();
      await chatService.sendMessage(tripId, text, workspaceDraft);
    } catch (err) {
      console.error("Failed to send message", err);
      setMessages(prev => [...prev, { id: crypto.randomUUID(), role: 'agent', content: "**System Error:** Could not reach AI backend." }]);
    }
  }, [tripId, connectStream]);

  const approveDraft = useCallback(async () => {
    // This is now replaced by the global "Save AI Drafts" button in ItineraryDetailPage
  }, [tripId]);

  return {
    messages,
    currentThought,
    isThinking,
    sendMessage,
    approveDraft
  };
};
