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

  const eventSourceRef = useRef<EventSource | null>(null);

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
            
            // Instantly append to the streaming agent message
            setMessages((prev) => {
              const lastMsg = prev[prev.length - 1];
              if (lastMsg && lastMsg.role === 'agent' && lastMsg.isStreaming) {
                const updated = [...prev];
                updated[updated.length - 1] = {
                  ...lastMsg,
                  content: lastMsg.content + data.content
                };
                return updated;
              } else {
                return [...prev, { id: crypto.randomUUID(), role: 'agent', content: data.content, isStreaming: true }];
              }
            });
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
            // Not used anymore by backend, but safe to keep handler as a no-op finalize
            setMessages((prev) => {
              const updated = [...prev];
              if (updated.length > 0 && updated[updated.length - 1].isStreaming) {
                updated[updated.length - 1].isStreaming = false;
              }
              return updated;
            });
            break;

          case 'done':
            setIsThinking(false);
            setCurrentThought('');
            setMessages((prev) => {
              const updated = [...prev];
              if (updated.length > 0 && updated[updated.length - 1].isStreaming) {
                updated[updated.length - 1].isStreaming = false;
              }
              return updated;
            });
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
