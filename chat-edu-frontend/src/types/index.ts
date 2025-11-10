export interface Course {
  id: string;
  nome: string;
  url: string;
  descricao?: string;
}

export interface Message {
  id: string;
  type: 'user' | 'bot';
  text: string;
  sources?: Source[];
  timestamp: Date;
}

export interface Source {
  source: string;
  page: number;
}

export interface Flashcard {
  question: string;
  answer: string;
  category?: string;
}

export interface MindMapNode {
  id: string;
  type: string;
  data: { label: string };
  position: { x: number; y: number };
}

export interface MindMapEdge {
  id: string;
  source: string;
  target: string;
}

export interface MindMapData {
  nodes: MindMapNode[];
  edges: MindMapEdge[];
}

export interface LoginResponse {
  success: boolean;
  cursos?: Course[];
  message?: string;
}

export interface ChatResponse {
  response: string | null;
  retrieved_sources: Source[];
  error: string | null;
}
