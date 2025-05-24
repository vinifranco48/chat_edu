import React, { useState, useEffect, useCallback } from 'react';
import './FlashcardInterface.css'; // Criaremos este arquivo em seguida

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function FlashcardInterface({ selectedCourse, isDarkMode }) {
  const [flashcards, setFlashcards] = useState([]);
  const [currentCardIndex, setCurrentCardIndex] = useState(0);
  const [showAnswer, setShowAnswer] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchFlashcards = useCallback(async (courseId) => {
    if (!courseId) {
      setFlashcards([]);
      setError(null);
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    setError(null);
    setShowAnswer(false); // Reseta ao carregar novos flashcards
    setCurrentCardIndex(0); // Reseta o índice

    try {
      const response = await fetch(`${API_BASE_URL}/flashcards/${courseId}`, {
        method: 'POST', // Conforme definido no backend
        headers: {
          'Content-Type': 'application/json',
          // Adicionar quaisquer outros headers necessários, como autenticação, se houver.
        },
        // Embora seja POST, o corpo não parece ser necessário para este endpoint específico,
        // já que o ID do curso está na URL. Se fosse necessário, seria adicionado aqui.
        // body: JSON.stringify({ course_id: courseId })
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: `Erro HTTP ${response.status}` }));
        throw new Error(errorData.detail || `Falha ao buscar flashcards`);
      }

      const data = await response.json();
      if (Array.isArray(data) && data.length > 0) {
        setFlashcards(data);
      } else {
        setFlashcards([]);
        // Considerar uma mensagem de "Nenhum flashcard encontrado" em vez de erro técnico
        setError("Nenhum flashcard encontrado para este curso ou formato de resposta inesperado.");
      }
    } catch (err) {
      console.error("Erro ao buscar flashcards:", err);
      setError(err.message || "Ocorreu um erro desconhecido.");
      setFlashcards([]);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (selectedCourse && selectedCourse.id) {
      fetchFlashcards(selectedCourse.id);
    } else {
      // Limpa os flashcards se nenhum curso estiver selecionado
      setFlashcards([]);
      setError(null);
      setCurrentCardIndex(0);
      setShowAnswer(false);
    }
  }, [selectedCourse, fetchFlashcards]);

  const handleNextCard = () => {
    setShowAnswer(false);
    setCurrentCardIndex((prevIndex) => (prevIndex + 1) % flashcards.length);
  };

  const handlePrevCard = () => {
    setShowAnswer(false);
    setCurrentCardIndex((prevIndex) => (prevIndex - 1 + flashcards.length) % flashcards.length);
  };

  const toggleShowAnswer = () => {
    setShowAnswer(!showAnswer);
  };

  if (!selectedCourse || !selectedCourse.id) {
    return (
      <div className={`flashcard-interface ${isDarkMode ? 'dark-mode' : 'light-mode'}`}>
        <div className="flashcard-container empty-state">
          <p>Por favor, selecione um curso na aba "Cursos" para ver os flashcards.</p>
        </div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className={`flashcard-interface ${isDarkMode ? 'dark-mode' : 'light-mode'}`}>
        <div className="flashcard-container loading-state">
          <p>Carregando flashcards...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`flashcard-interface ${isDarkMode ? 'dark-mode' : 'light-mode'}`}>
        <div className="flashcard-container error-state">
          <p>Erro: {error}</p>
          <button onClick={() => fetchFlashcards(selectedCourse.id)} className="retry-button">
            Tentar Novamente
          </button>
        </div>
      </div>
    );
  }

  if (flashcards.length === 0) {
    return (
      <div className={`flashcard-interface ${isDarkMode ? 'dark-mode' : 'light-mode'}`}>
        <div className="flashcard-container empty-state">
          <p>Nenhum flashcard disponível para este curso.</p>
        </div>
      </div>
    );
  }

  const currentCard = flashcards[currentCardIndex];

  return (
    <div className={`flashcard-interface ${isDarkMode ? 'dark-mode' : 'light-mode'}`}>
      <h2>Flashcards: {selectedCourse.nome || selectedCourse.name}</h2>
      <div className="flashcard-container">
        <div className="flashcard-counter">
          {currentCardIndex + 1} / {flashcards.length}
        </div>
        <div className={`flashcard ${showAnswer ? 'show-answer' : ''}`} onClick={toggleShowAnswer}>
          <div className="flashcard-inner">
            <div className="flashcard-front">
              <p className="flashcard-label">Pergunta:</p>
              <p className="flashcard-text">{currentCard?.pergunta}</p>
            </div>
            <div className="flashcard-back">
              <p className="flashcard-label">Resposta:</p>
              <p className="flashcard-text">{currentCard?.resposta}</p>
            </div>
          </div>
        </div>
        <div className="flashcard-controls">
          <button onClick={handlePrevCard} disabled={flashcards.length <= 1}>
            Anterior
          </button>
          <button onClick={toggleShowAnswer} className="show-answer-button">
            {showAnswer ? 'Ocultar Resposta' : 'Mostrar Resposta'}
          </button>
          <button onClick={handleNextCard} disabled={flashcards.length <= 1}>
            Próximo
          </button>
        </div>
      </div>
    </div>
  );
}

export default FlashcardInterface;