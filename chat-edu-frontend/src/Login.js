import React, { useState } from 'react';
import { Eye, EyeOff, LogIn, AlertCircle } from 'lucide-react';
import './Login.css';

const Login = ({ onLoginSuccess, isDarkMode }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showPassword, setShowPassword] = useState(false);

  const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

  const handleLoginSubmit = async e => {
    e.preventDefault();
    if (!username || !password) {
      setError('Por favor, preencha o usuário e a senha.');
      return;
    }
    setIsLoading(true);
    setError(null);
    try {
      const loginUrl = `${API_BASE_URL}/login/?username=${encodeURIComponent(username)}&password=${encodeURIComponent(password)}`;
      const response = await fetch(loginUrl, {
        method: 'POST',
        credentials: 'include',
      });
      let data;
      const ct = response.headers.get('content-type') || '';
      if (ct.includes('application/json')) data = await response.json();
      else {
        const text = await response.text();
        data = text ? { message: text } : null;
      }
      if (!response.ok) {
        const msg = data?.detail || data?.message || `Erro ${response.status}`;
        throw new Error(msg);
      }
      onLoginSuccess({ username, ...data });
    } catch (err) {
      setError(err.message || 'Erro inesperado.');
    } finally {
      setIsLoading(false);
    }
  };

  const togglePasswordVisibility = () => setShowPassword(v => !v);

  return (
    <div className={`login-page-container ${isDarkMode ? 'dark-mode' : 'light-mode'}`}>
      <div className="login-content-wrapper">
        <header className="login-header">
          <div className="logo-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 ..." />
            </svg>
          </div>
          <h1 className="login-title">Chat Edu</h1>
          <p>Faça login para continuar</p>
        </header>

        {error && <div className="login-error-message"><AlertCircle className="icon" />{error}</div>}

        <form className="login-form" onSubmit={handleLoginSubmit}>
          <div className="login-input-group">
            <label htmlFor="username">Usuário</label>
            <input
              id="username"
              type="text"
              className="login-input"
              placeholder="Digite seu usuário"
              value={username}
              onChange={e => setUsername(e.target.value)}
              disabled={isLoading}
              autoComplete="username"
              autoFocus
            />
          </div>

          <div className="login-input-group">
            <label htmlFor="password">Senha</label>
            <div className="relative-container">
              <input
                id="password"
                type={showPassword ? 'text' : 'password'}
                className="login-input"
                placeholder="Digite sua senha"
                value={password}
                onChange={e => setPassword(e.target.value)}
                disabled={isLoading}
                autoComplete="current-password"
              />
              <button type="button" className="toggle-password" onClick={togglePasswordVisibility}>
                {showPassword ? <EyeOff /> : <Eye />}
              </button>
            </div>
          </div>

          <button type="submit" className="login-button" disabled={isLoading}>
            {isLoading
              ? <div className="button-loading-indicator">
                  <span className="dot" />
                  <span className="dot" />
                  <span className="dot" />
                </div>
              : <><LogIn className="mr-2" />Entrar</>
            }
          </button>
        </form>

        <div className="login-footer-links">
          <a href="#forgot">Esqueci a senha</a> • <a href="#register">Criar conta</a>
        </div>
      </div>
    </div>
  );
};

export default Login;