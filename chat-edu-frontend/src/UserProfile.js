import React from 'react';
import './UserProfile.css';

function UserProfile({ user, isDarkMode }) {
  // Número de cursos do usuário
  const coursesCount = user?.cursos?.length || 0;
  
  return (
    <div className={`user-profile ${isDarkMode ? 'dark-mode' : 'light-mode'}`}>
      <div className="profile-header">
        <div className="profile-avatar">
          {/* Avatar com as iniciais do nome do usuário */}
          <div className="avatar-initials">
            {user.username ? user.username.substring(0, 2).toUpperCase() : 'U'}
          </div>
        </div>
        <div className="profile-info">
          <h2 className="profile-name">{user.username || 'Usuário'}</h2>
          <p className="profile-meta">Aluno | {coursesCount} curso{coursesCount !== 1 ? 's' : ''} matriculado{coursesCount !== 1 ? 's' : ''}</p>
        </div>
      </div>
      
      <div className="profile-stats">
        <div className="stat-card">
          <div className="stat-value">{coursesCount}</div>
          <div className="stat-label">Cursos</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">0</div>
          <div className="stat-label">Completos</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">0</div>
          <div className="stat-label">Certificados</div>
        </div>
      </div>
      
      <div className="profile-section">
        <h3 className="section-title">Atividade Recente</h3>
        
        {coursesCount > 0 ? (
          <div className="activity-list">
            <div className="activity-card">
              <div className="activity-icon">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                  <polyline points="14 2 14 8 20 8"></polyline>
                  <line x1="16" y1="13" x2="8" y2="13"></line>
                  <line x1="16" y1="17" x2="8" y2="17"></line>
                  <polyline points="10 9 9 9 8 9"></polyline>
                </svg>
              </div>
              <div className="activity-content">
                <h4>Bem-vindo ao Chat Edu!</h4>
                <p>Explore seus cursos e comece a aprender com assistência do nosso chat inteligente.</p>
                <div className="activity-time">Hoje</div>
              </div>
            </div>
            
            <div className="activity-card">
              <div className="activity-icon secondary">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path>
                  <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path>
                </svg>
              </div>
              <div className="activity-content">
                <h4>Lista de cursos atualizada</h4>
                <p>{coursesCount} curso{coursesCount !== 1 ? 's' : ''} disponível{coursesCount !== 1 ? 'is' : ''} para você.</p>
                <div className="activity-time">Hoje</div>
              </div>
            </div>
          </div>
        ) : (
          <div className="empty-state">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10"></circle>
              <line x1="12" y1="8" x2="12" y2="12"></line>
              <line x1="12" y1="16" x2="12.01" y2="16"></line>
            </svg>
            <p>Você ainda não tem cursos matriculados</p>
          </div>
        )}
      </div>
      
      <div className="profile-section">
        <h3 className="section-title">Próximos Passos</h3>
        <div className="steps-list">
          <div className="step-item">
            <div className="step-check">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="20 6 9 17 4 12"></polyline>
              </svg>
            </div>
            <div className="step-content">
              <h4>Fazer login</h4>
              <p>Você já está logado. Bom trabalho!</p>
            </div>
          </div>
          
          <div className={`step-item ${coursesCount > 0 ? 'completed' : ''}`}>
            <div className="step-check">
              {coursesCount > 0 ? (
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="20 6 9 17 4 12"></polyline>
                </svg>
              ) : (
                <span className="step-number">2</span>
              )}
            </div>
            <div className="step-content">
              <h4>Explorar seus cursos</h4>
              <p>Veja os cursos disponíveis para você na aba Cursos</p>
            </div>
          </div>
          
          <div className="step-item">
            <div className="step-check">
              <span className="step-number">3</span>
            </div>
            <div className="step-content">
              <h4>Use o Chat Inteligente</h4>
              <p>Faça perguntas sobre o conteúdo dos seus cursos usando o Chat</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default UserProfile;