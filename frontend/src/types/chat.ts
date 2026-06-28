export interface ChatMessage {
  id: string;
  role: 'user' | 'agent';
  content: string;
  isStreaming?: boolean;
}

export interface StreamEvent {
  type: 'thought' | 'token' | 'tool_call' | 'error' | 'draft_update' | 'done' | 'new_run';
  content: string;
}

export interface DraftStop {
  google_place_id: string;
  day_number: number;
  name: string;
  stop_type: string;
  user_notes?: string;
  arrival_time?: string;
  departure_time?: string;
  estimated_cost?: string;
}
