const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

export interface ChatRequest {
  message: string;
}

export interface ChatResponse {
  response: string;
}

export const sendChatMessage = async (message: string): Promise<ChatResponse> => {
  const token = localStorage.getItem('access_token');
  
  if (!token) {
    throw new Error('Not authenticated');
  }

  const response = await fetch(`${BACKEND_URL}/api/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify({ message }),
  });

  if (!response.ok) {
    if (response.status === 401) {
      throw new Error('Session expired. Please login again.');
    }
    throw new Error(`Backend error: ${response.status}`);
  }

  return await response.json();
};
