import React, { useState } from 'react';
import './Dashboard.css'; // Vamos criar este arquivo de estilo em seguida

// Componentes individuais para cada seção
import UserProfile from './UserProfile';
import CoursesList from './CoursesList';
import ChatInterface from './ChatInterface';

function Dashboard({ user, onLogout, isDarkMode, toggleDarkMode }) {
  const [activeSection, setActiveSection] = useState('chat'); // Começar com o chat ativo
  const [selectedCourse, setSelectedCourse] = useState(null);
  const [courseEmbeddings, setCourseEmbeddings] = useState(null);
  
  // Verifica se o usuário tem cursos
  const hasCourses = user?.cursos && user.cursos.length > 0;

  const handleCourseSelect = (courseId, embeddings) => {
    setSelectedCourse(courseId);
    setCourseEmbeddings(embeddings);
    setActiveSection('chat'); // Troca automaticamente para o chat
  };
  
  const renderContent = () => {
    switch (activeSection) {
      case 'profile':
        return <UserProfile 
                 user={user} 
                 isDarkMode={isDarkMode} 
               />;
      case 'courses':
        return <CoursesList 
                 courses={user?.cursos || []} 
                 isDarkMode={isDarkMode}
                 onCourseSelect={handleCourseSelect}
               />;
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
      default:
        return <UserProfile 
                 user={user} 
                 isDarkMode={isDarkMode} 
               />;
    }
  };

  return (
    <div className={`dashboard-container ${isDarkMode ? 'dark-mode' : 'light-mode'}`}>
      {/* Menu Lateral */}
      <div className="dashboard-sidebar">
        <div className="dashboard-logo">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="logo-icon">
            <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"></path>
          </svg>
          <h1>Chat Edu</h1>
        </div>
        
        <nav className="dashboard-nav">
          <button 
            className={`nav-item ${activeSection === 'profile' ? 'active' : ''}`} 
            onClick={() => setActiveSection('profile')}
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
              <circle cx="12" cy="7" r="4"></circle>
            </svg>
            <span>Perfil</span>
          </button>
          
          {hasCourses && (
            <button 
              className={`nav-item ${activeSection === 'courses' ? 'active' : ''}`} 
              onClick={() => setActiveSection('courses')}
            >
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path>
                <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path>
              </svg>
              <span>Cursos</span>
            </button>
          )}
          
          <button 
            className={`nav-item ${activeSection === 'chat' ? 'active' : ''}`} 
            onClick={() => setActiveSection('chat')}
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
            </svg>
            <span>Chat</span>
          </button>
        </nav>
        
        <div className="dashboard-footer">
          <button className="theme-toggle" onClick={toggleDarkMode}>
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
      
      {/* Conteúdo Principal */}
      <div className="dashboard-content">
        {renderContent()}
      </div>
    </div>
  );
}

export default Dashboard;