// src/App.js (ou src/App.tsx)
import React, { useState, useRef, useEffect, useCallback } from 'react';
import './App.css'; // Importa os estilos

// (Opcional, se usar TypeScript)
// interface ChatMessage {
//   type: 'question' | 'answer' | 'error';
//   content: string;
//   sources?: Array<{ source: string; page: number }>;
// }

function App() {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [chatHistory, setChatHistory] = useState([]); // ChatMessage[] se TS
  const chatHistoryRef = useRef(null); // Ref para o container do histórico
  const textareaRef = useRef(null); // Ref para o textarea

  // --- Auto-scroll ---
  useEffect(() => {
    if (chatHistoryRef.current) {
      chatHistoryRef.current.scrollTop = chatHistoryRef.current.scrollHeight;
    }
  }, [chatHistory, loading]); // Roda quando histórico muda ou loading começa/termina

  // --- Auto-resize Textarea ---
  useEffect(() => {
    const adjustHeight = () => {
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto'; // Reset height
        textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`; // Set to scroll height
      }
    };
    adjustHeight(); // Adjust on initial render and query change
  }, [query]);

  // --- API Call Logic ---
  const fetchChatResponse = useCallback(async (text) => { // useCallback para evitar recriação desnecessária
    setLoading(true);
    const userMessage = { type: 'question', content: text }; // : ChatMessage se TS
    // Atualiza estado mostrando a pergunta *antes* da chamada da API
    setChatHistory((prevHistory) => [...prevHistory, userMessage]);
    setQuery(''); // Limpa input imediatamente

    try {
      const response = await fetch('http://localhost:8000/chat/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: text }),
      });

      let data;
      try {
        data = await response.json();
      } catch (jsonError) {
        if (!response.ok) {
          throw new Error(`Erro HTTP ${response.status}: ${response.statusText}. Resposta inválida do servidor.`);
        }
        console.error("Falha ao parsear JSON:", jsonError);
        throw new Error("Resposta inválida do servidor.");
      }

      if (!response.ok) {
        const errorMsg = data?.detail || data?.error || `Erro HTTP ${response.status}`;
        throw new Error(errorMsg);
      }

      if (data.error) {
         console.error('Erro da API:', data.error);
         setChatHistory((prevHistory) => [
           ...prevHistory,
           { type: 'error', content: `Erro: ${data.error}` }, // : ChatMessage se TS
         ]);
      } else if (data.response) {
         setChatHistory((prevHistory) => [
           ...prevHistory,
           {
             type: 'answer',
             content: data.response,
             sources: data.retrieved_sources || [],
           }, // : ChatMessage se TS
         ]);
      } else {
        console.error('Resposta inesperada:', data);
        setChatHistory((prevHistory) => [
          ...prevHistory,
          { type: 'error', content: 'Resposta inesperada do servidor.' }, // : ChatMessage se TS
        ]);
      }

    } catch (error) {
      console.error('Falha na comunicação:', error);
      const errorMessage = error instanceof Error ? error.message : 'Erro desconhecido.';
      setChatHistory((prevHistory) => [
        ...prevHistory,
        { type: 'error', content: `Erro: ${errorMessage}` }, // : ChatMessage se TS
      ]);
    } finally {
      setLoading(false);
      // Foca no textarea novamente após a resposta (ou erro)
      textareaRef.current?.focus();
    }
  }, []); // Sem dependências, pois usa setChatHistory funcional e não depende de props/state externos

  // --- Form Submission ---
  const handleSubmit = (e) => { // (e?: React.FormEvent<HTMLFormElement>) se TS
    e?.preventDefault(); // Previne recarregamento (opcional se chamado por Enter)
    const trimmedQuery = query.trim();
    if (!trimmedQuery || loading) return;
    fetchChatResponse(trimmedQuery);
  };

  // --- Handle Enter Key ---
  const handleKeyDown = (e) => { // (e: React.KeyboardEvent<HTMLTextAreaElement>) se TS
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault(); // Previne nova linha no textarea
      handleSubmit(); // Envia o formulário
    }
  };

  // --- Render Sources ---
  const renderSources = (sources) => { // (sources: Array<{ source: string; page: number }> | undefined) se TS
    if (!sources || sources.length === 0) return null;

    const uniqueSources = sources.reduce((acc, current) => {
      const key = `${current.source}-${current.page}`;
      if (!acc.find(item => `${item.source}-${item.page}` === key)) {
        acc.push(current);
      }
      return acc;
    }, []); // : Array<{ source: string; page: number }> se TS

    return (
      <div className="sources-container">
        <strong>Fontes:</strong>
        <ul>
          {uniqueSources.map((source, index) => (
            <li key={index}>
              {source.source.split(/[\\/]/).pop() || source.source}
              {source.page !== -1 && ` (p. ${source.page + 1})`}
            </li>
          ))}
        </ul>
      </div>
    );
  };

  // --- Component Render ---
  return (
    <div className="chat-app">
      {/* O cabeçalho é opcional no estilo ChatGPT, pode ser removido ou simplificado */}
      {/* <header className="app-header">
        <h1>Chat Edu 🎓</h1>
        <p className="subtitle">Assistente educacional RAG</p>
      </header> */}

      <div className="chat-history-wrapper" ref={chatHistoryRef}>
        {chatHistory.length === 0 && !loading && (
          <div className="welcome-message">
            {/* Pode colocar um logo ou ícone aqui */}
            <h2>Como posso ajudar?</h2>
            <p>Faça sua pergunta sobre o conteúdo.</p>
            {/* <p>Ex: "Quais são os principais tópicos?"</p> */}
          </div>
        )}

        {chatHistory.map((message, index) => (
          <div key={index} className={`message ${message.type}-message`}>
            <div className={`avatar ${message.type}-avatar`}>
              {message.type === 'question' && '👤'}
              {message.type === 'answer' && '🤖'}
              {message.type === 'error' && '❗️'}
            </div>
            <div className="message-content-wrapper">
              <div className="message-content">{message.content}</div>
              {message.type === 'answer' && renderSources(message.sources)}
            </div>
          </div>
        ))}

        {loading && (
          <div className="message bot-message loading">
            <div className="avatar bot-avatar">🤖</div>
            <div className="message-content-wrapper">
              <div className="message-content">
                <div className="typing-indicator">
                  <span></span><span></span><span></span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div> {/* Fim de chat-history-wrapper */}

      <footer className="input-area-footer">
        <form className="input-form" onSubmit={handleSubmit}>
          <textarea
            ref={textareaRef}
            placeholder="Envie uma mensagem..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={loading}
            className="query-textarea"
            rows={1} // Começa com 1 linha, CSS/JS cuidam do ajuste
            aria-label="Campo de mensagem"
          />
          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="send-button"
            title="Enviar mensagem"
          >
             {/* Ícone de envio (pode ser um SVG) */}
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" width="1.2em" height="1.2em">
              <path d="M3.478 2.405a.75.75 0 00-.926.94l2.432 7.905H13.5a.75.75 0 010 1.5H4.984l-2.432 7.905a.75.75 0 00.926.94 60.519 60.519 0 0018.445-8.986.75.75 0 000-1.218A60.517 60.517 0 003.478 2.405z" />
            </svg>
          </button>
        </form>
        {/* Mensagem de rodapé opcional, como no ChatGPT */}
        <p className="footer-disclaimer">
          Chat Edu pode cometer erros. Considere verificar informações importantes.
        </p>
      </footer>
    </div> // Fim de chat-app
  );
}

export default App;