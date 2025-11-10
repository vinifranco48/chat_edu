import type { LoginResponse, ChatResponse, Flashcard, MindMapData } from '@/types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const api = {
  login: async (username: string, password: string): Promise<LoginResponse> => {
    // Backend espera query params, não body JSON
    const response = await fetch(
      `${API_BASE_URL}/login/?username=${encodeURIComponent(username)}&password=${encodeURIComponent(password)}`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      }
    );
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.message || 'Falha na autenticação');
    }
    
    return response.json();
  },

  sendChatMessage: async (text: string, courseId: string): Promise<ChatResponse> => {
    const response = await fetch(`${API_BASE_URL}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, courseId }),
    });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Erro ao enviar mensagem');
    }
    
    return response.json();
  },

  generateFlashcards: async (courseId: string): Promise<Flashcard[]> => {
    const response = await fetch(
      `${API_BASE_URL}/flashcards/${courseId}?vector_size=768`,
      { 
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      }
    );
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Erro ao gerar flashcards');
    }
    
    return response.json();
  },

  generateMindMap: async (courseId: string, courseName: string): Promise<MindMapData> => {
    const response = await fetch(
      `${API_BASE_URL}/mindmaps/${courseId}?course_name=${encodeURIComponent(courseName)}`,
      { 
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      }
    );
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Erro ao gerar mapa mental');
    }
    
    return response.json();
  },

  getRetrieverEmbeddings: async (courseId: string): Promise<any[]> => {
    const response = await fetch(
      `${API_BASE_URL}/retriever/${courseId}`,
      { 
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      }
    );
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Erro ao buscar embeddings');
    }
    
    const data = await response.json();
    return data.embeddings || [];
  },
};
