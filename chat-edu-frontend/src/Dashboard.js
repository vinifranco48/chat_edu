// src/Dashboard.js
import React, { useState } from 'react';
import './Dashboard.css';

// Componentes individuais para cada seção
import UserProfile from './UserProfile';
import ChatInterface from './ChatInterface';
import FlashcardInterface from './FlashcardInterface';
import MindMapInterface from './MindMapInterface';

function Dashboard({ user, onLogout, isDarkMode, toggleDarkMode }) {
  // Sempre começa no perfil
  const [activeSection, setActiveSection] = useState('profile');
  const [selectedCourse, setSelectedCourse] = useState(null);
  const [courseEmbeddings, setCourseEmbeddings] = useState(null);
  
  // Função para lidar com a seleção de um curso
  const handleCourseSelect = (courseId, embeddings) => {
    const courseDetails = user?.cursos?.find(c => String(c.id) === String(courseId));
    setSelectedCourse(courseDetails || { id: courseId, nome: `Curso ${courseId}` }); 
    setCourseEmbeddings(embeddings);
    setActiveSection('chat'); // Muda automaticamente para o chat após selecionar
  };

  // Função para voltar ao perfil (desselecionar curso)
  const handleBackToProfile = () => {
    setSelectedCourse(null);
    setCourseEmbeddings(null);
    setActiveSection('profile');
  };
  
  // Renderiza o conteúdo da seção ativa
  const renderContent = () => {
    switch (activeSection) {
      case 'profile':
        return (
          <UserProfile 
            user={user} 
            isDarkMode={isDarkMode} 
            onCourseSelect={handleCourseSelect}
          />
        );
      case 'chat':
        return (
          <ChatInterface 
            userData={user} 
            isDarkMode={isDarkMode} 
            toggleTheme={toggleDarkMode} 
            onLogout={onLogout} 
            selectedCourse={selectedCourse} 
            courseEmbeddings={courseEmbeddings} 
          />
        );
      case 'flashcards':
        return <FlashcardInterface selectedCourse={selectedCourse} isDarkMode={isDarkMode} />;
      case 'mindmaps':
        return <MindMapInterface selectedCourse={selectedCourse} isDarkMode={isDarkMode} />;
      default:
        return (
          <UserProfile 
            user={user} 
            isDarkMode={isDarkMode} 
            onCourseSelect={handleCourseSelect}
          />
        );
    }
  };

  return (
    <div className={`dashboard-container ${isDarkMode ? 'dark-mode' : 'light-mode'}`}>
      {/* Menu Lateral (Sidebar) */}
      <div className="dashboard-sidebar">
        <div className="dashboard-logo">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="logo-icon">
            <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"></path>
          </svg>
          <h1>Chat Edu</h1>
        </div>
        
        <nav className="dashboard-nav">
          {/* Botão Perfil - sempre visível */}
          <button 
            className={`nav-item ${activeSection === 'profile' ? 'active' : ''}`} 
            onClick={handleBackToProfile}
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
              <circle cx="12" cy="7" r="4"></circle>
            </svg>
            <span>Perfil</span>
          </button>
          
          {/* Separador visual quando há curso selecionado */}
          {selectedCourse && (
            <div className="nav-separator">
              <div className="separator-line"></div>
              <div className="course-name">{selectedCourse.nome || selectedCourse.name}</div>
            </div>
          )}
          
          {/* Botões que só aparecem quando um curso está selecionado */}
          {selectedCourse && (
            <>
              <button 
                className={`nav-item ${activeSection === 'chat' ? 'active' : ''}`} 
                onClick={() => setActiveSection('chat')}
              >
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                </svg>
                <span>Chat</span>
              </button>

              <button
                className={`nav-item ${activeSection === 'flashcards' ? 'active' : ''}`}
                onClick={() => setActiveSection('flashcards')}
              >
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <rect x="2" y="2" width="20" height="20" rx="2" ry="2"></rect>
                  <line x1="12" y1="2" x2="12" y2="22"></line>
                  <line x1="2" y1="12" x2="7" y2="12"></line>
                  <line x1="17" y1="12" x2="22" y2="12"></line>
                </svg>
                <span>Flashcards</span>
              </button>

              <button
                className={`nav-item ${activeSection === 'mindmaps' ? 'active' : ''}`}
                onClick={() => setActiveSection('mindmaps')}
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M3 6s1.21-1.17 3.17-1.17S9.33 6 9.33 6M3 18s1.21 1.17 3.17 1.17S9.33 18 9.33 18M14.67 6s1.21-1.17 3.17-1.17S21 6 21 6M14.67 18s1.21 1.17 3.17 1.17S21 18 21 18M12 4.5v15M6.17 6H3M6.17 18H3M17.83 6H21M17.83 18H21M9.33 6h5.34M9.33 18h5.34"/>
                </svg>
                <span>Mapa Mental</span>
              </button>
            </>
          )}
        </nav>
        
        {/* Rodapé do Sidebar */}
        <div className="dashboard-footer">
          <button className="theme-toggle" onClick={toggleDarkMode} aria-label="Alternar tema">
            {isDarkMode ? (
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="5"></circle>
                <line x1="12" y1="1" x2="12" y2="3"></line>
                <line x1="12" y1="21" x2="12" y2="23"></line>
                <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line>
                <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line>
                <line x1="1" y1="12" x2="3" y2="12"></line>
                <line x1="21" y1="12" x2="23" y2="12"></line>
                <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line>
                <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>
              </svg>
            ) : (
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>
              </svg>
            )}
          </button>
          <button className="logout-button" onClick={onLogout}>
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
              <polyline points="16 17 21 12 16 7"></polyline>
              <line x1="21" y1="12" x2="9" y2="12"></line>
            </svg>
            <span>Sair</span>
          </button>
        </div>
      </div>
      
      {/* Conteúdo Principal do Dashboard */}
      <div className="dashboard-content">
        {renderContent()}
      </div>
    </div>
  );
}

export default Dashboard;