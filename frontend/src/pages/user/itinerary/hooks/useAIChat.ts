import { useState, useEffect, useCallback, useRef } from 'react';
import type { ChatMessage, StreamEvent } from '@/types/chat';
import { chatService } from '@/services/chatService';

export const useAIChat = (tripId: string) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [currentThought, setCurrentThought] = useState<string>('');
  const [isThinking, setIsThinking] = useState<boolean>(false);
  const [pendingDraft, setPendingDraft] = useState<any[] | null>(null);

  // Ref to hold EventSource so we can clean it up
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

  useEffect(() => {
    // We establish the SSE connection when the component mounts
    // Assuming backend FastAPI runs on an accessible route. We might need to proxy this or use full URL.
    const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
    const token = localStorage.getItem('access_token');
    const sseUrl = `${baseUrl}/ai/chat/${tripId}/stream${token ? `?token=${token}` : ''}`;

    eventSourceRef.current = new EventSource(sseUrl);

    eventSourceRef.current.onmessage = (event) => {
      try {
        const data: StreamEvent = JSON.parse(event.data);

        switch (data.type) {
          case 'thought':
            setIsThinking(true);
            setCurrentThought((prev) => prev + '\n' + data.content);
            break;

          case 'token':
            setIsThinking(true); // Ensure thinking stays true until 'done'
            setMessages((prev) => {
              // Find if we have an ongoing 'agent' streaming message
              const lastMsg = prev[prev.length - 1];
              if (lastMsg && lastMsg.role === 'agent' && lastMsg.isStreaming) {
                const updated = [...prev];
                updated[updated.length - 1].content += data.content;
                return updated;
              } else {
                // Create new agent message
                return [...prev, { id: crypto.randomUUID(), role: 'agent', content: data.content, isStreaming: true }];
              }
            });
            break;

          case 'draft_update':
            try {
              const draftData = JSON.parse(data.content);
              setPendingDraft(draftData);
            } catch (e) {
              console.error("Failed to parse draft_update", e);
            }
            break;

          case 'clear_bubble':
            // Finalize the current bubble without unlocking the UI
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

    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, [tripId]);

  const sendMessage = useCallback(async (text: string) => {
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
      await chatService.sendMessage(tripId, text);
    } catch (err) {
      console.error("Failed to send message", err);
      setMessages(prev => [...prev, { id: crypto.randomUUID(), role: 'agent', content: "**System Error:** Could not reach AI backend." }]);
    }
  }, [tripId]);

  const approveDraft = useCallback(async () => {
    setIsThinking(true);
    setCurrentThought("> Committing draft to database...");
    try {
      await chatService.approveDraft(tripId);
      setMessages(prev => [...prev, { id: crypto.randomUUID(), role: 'agent', content: "Draft successfully committed to your itinerary!" }]);
      setPendingDraft(null); // Clear draft on success
    } catch (err) {
      console.error("Failed to approve draft", err);
      setMessages(prev => [...prev, { id: crypto.randomUUID(), role: 'agent', content: "**System Error:** Failed to commit draft." }]);
    } finally {
      setIsThinking(false);
      setCurrentThought("");
    }
  }, [tripId]);

  return {
    messages,
    currentThought,
    isThinking,
    pendingDraft,
    sendMessage,
    approveDraft
  };
};
