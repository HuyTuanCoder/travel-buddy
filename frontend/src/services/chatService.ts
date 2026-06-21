import api from './api';

export const chatService = {
  /**
   * Starts a new chat message processing job on the backend.
   * We use 'any' for now since the backend is python FastAPI and we expect a 202 Accepted.
   */
  sendMessage: async (tripId: string, message: string): Promise<void> => {
    // Fire and forget, backend drops into RabbitMQ
    await api.post(`/ai/chat`, {
      trip_id: tripId,
      message: message
    });
  },

  /**
   * Triggers the backend to commit the current draft to the database.
   */
  approveDraft: async (tripId: string): Promise<void> => {
    await api.post(`/ai/chat/${tripId}/approve`);
  }
};
