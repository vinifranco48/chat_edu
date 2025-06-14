import React, { useState, useEffect, useCallback, useRef } from 'react';
// NOVAS IMPORTAÇÕES
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import 'katex/dist/katex.min.css'; // Importe o CSS do KaTeX

function ChatInterface({ userData, isDarkMode, toggleTheme, onLogout, selectedCourse, courseEmbeddings }) {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [chatHistory, setChatHistory] = useState([]);
  const chatHistoryRef = useRef(null);
  const textareaRef = useRef(null);
  // eslint-disable-next-line no-unused-vars
  const [clearChat, setClearChat] = useState(false);

  // Auto-scroll para novas mensagens
  useEffect(() => {
    if (chatHistoryRef.current) {
      chatHistoryRef.current.scrollTop = chatHistoryRef.current.scrollHeight;
    }
  }, [chatHistory, loading]);

  // Auto-resize do textarea
  useEffect(() => {
    const adjustHeight = () => {
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
        textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 150)}px`;
      }
    };
    adjustHeight();
  }, [query]);

  const fetchChatResponse = useCallback(async (text) => {
    setLoading(true);
    const userMessage = { type: 'question', content: text };
    setChatHistory((prevHistory) => [...prevHistory, userMessage]);
    setQuery('');

    try {
      const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
        console.log('[ChatInterface] Enviando para /chat com courseId:', selectedCourse)
      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${userData.token}`
        },
        body: JSON.stringify({ 
          text: text,
          courseId: selectedCourse?.id
        })
      });

      let data;
      try {
        data = await response.json();
      } catch (jsonError) {
        throw new Error("Resposta inválida do servidor.");
      }

      if (!response.ok) {
        throw new Error(data?.detail || `Erro ${response.status}`);
      }

      if (data.error) {
        setChatHistory(prev => [...prev, { 
          type: 'error', 
          content: `Erro: ${data.error}` 
        }]);
      } else if (data.response) {
        setChatHistory(prev => [...prev, {
          type: 'answer',
          content: data.response,
          sources: data.retrieved_sources || []
        }]);
      }
    } catch (error) {
      setChatHistory(prev => [...prev, {
        type: 'error',
        content: `Erro ao comunicar com o chat: ${error.message}`
      }]);
    } finally {
      setLoading(false);
      textareaRef.current?.focus();
    }
  }, [userData, selectedCourse]);

  const handleSubmit = (e) => {
    e?.preventDefault();
    const trimmedQuery = query.trim();
    if (!trimmedQuery || loading) return;
    fetchChatResponse(trimmedQuery);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };



  // FUNÇÃO ATUALIZADA PARA RENDERIZAR MARKDOWN E LATEX
  const formatMessageContent = (content) => {
    return (
      <ReactMarkdown
        remarkPlugins={[remarkGfm, remarkMath]}
        rehypePlugins={[rehypeKatex]}
        // Você pode personalizar componentes se necessário, por exemplo, para links ou cabeçalhos
        // components={{
        //   a: ({node, ...props}) => <a {...props} target="_blank" rel="noopener noreferrer" />
        // }}
      >
        {content}
      </ReactMarkdown>
    );
  };

  return (
    <div className="chat-interface">
      <div className="chat-container">
        <div className="chat-history" ref={chatHistoryRef}>
          {/* Mensagem de Boas Vindas */}
          {chatHistory.length === 0 && !loading && (
            <div className="welcome-container">
              {/* ... seu código de boas vindas ... */}
                 <div className="welcome-header">
                   <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="welcome-icon"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>
                   <h2>Assistente Educacional</h2>
                 </div>
                 <p className="welcome-text">Como posso ajudar nos seus estudos hoje?</p>
                 <div className="example-prompts">
                   <button className="example-prompt" onClick={() => setQuery("Quais são os principais tópicos do material?")}>
                     "Quais são os principais tópicos do material?"
                   </button>
                   <button className="example-prompt" onClick={() => setQuery("Você pode me explicar o conceito de...?")}>
                     "Você pode me explicar o conceito de...?"
                   </button>
                   <button className="example-prompt" onClick={() => setQuery("Resuma o conteúdo de forma simples.")}>
                     "Resuma o conteúdo de forma simples."
                   </button>
                 </div>
            </div>
          )}

          {/* Chat History */}
          {chatHistory.map((message, index) => (
            <div key={index} className={`message-wrapper ${message.type}-wrapper`}>
              <div className="message-container">
                <div className={`message-avatar ${message.type}-avatar`}>
                  {/* Avatar icons - você pode adicionar SVGs ou imagens aqui */}
                </div>
                <div className="message-content">
                  <div className="message-text">
                    {/* AQUI A FUNÇÃO É CHAMADA */}
                    {formatMessageContent(message.content)}
                  </div>
                </div>
              </div>
            </div>
          ))}

          {/* Loading Indicator */}
          {loading && (
            <div className="message-wrapper answer-wrapper">
              {/* ... seu indicador de loading ... */}
                <div className="message-container">
                   <div className="message-avatar answer-avatar"></div>
                   <div className="message-content">
                     <div className="message-text">
                       <div className="typing-indicator"><span></span><span></span><span></span></div>
                     </div>
                   </div>
                </div>
            </div>
          )}
        </div>

        {/* Chat Input */}
        <footer className="chat-input-container">
          {/* ... seu formulário de input ... */}
           <form className="chat-form" onSubmit={handleSubmit}>
             <div className="textarea-wrapper">
               <textarea
                 ref={textareaRef}
                 placeholder="Envie uma mensagem..."
                 value={query}
                 onChange={(e) => setQuery(e.target.value)}
                 onKeyDown={handleKeyDown}
                 disabled={loading}
                 className="chat-input"
                 rows={1}
                 aria-label="Campo de mensagem"
               ></textarea>
               <button
                 type="submit"
                 disabled={loading || !query.trim()}
                 className="send-button"
                 title="Enviar mensagem"
               >
                 <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                   <line x1="22" y1="2" x2="11" y2="13"></line>
                   <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
                 </svg>
               </button>
             </div>
           </form>
           <p className="disclaimer">
             Chat Edu pode cometer erros. Considere verificar informações importantes.
           </p>
        </footer>
      </div>
    </div>
  );
}

export default ChatInterface;