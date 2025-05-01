import React, { useState } from 'react';
import './App.css'; // Reutiliza o CSS existente

// Props esperadas:
// - onLoginSuccess: Função chamada com os dados do usuário (cursos) após login bem-sucedido.
// - isDarkMode: Booleano para aplicar o tema correto (opcional, mas recomendado para consistência)
function Login({ onLoginSuccess, isDarkMode }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  // URL base do backend - pode ser configurada via variável de ambiente
  // ou definida explicitamente para desenvolvimento/produção
  const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

  const handleLoginSubmit = async (e) => {
    e.preventDefault(); // Impede o recarregamento da página
    if (!username || !password) {
      setError('Por favor, preencha o usuário e a senha.');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      // Ajustando o endpoint para incluir a barra no final (/login/)
      // FastAPI espera os parâmetros como query parameters, não como form data
      const response = await fetch(`${API_BASE_URL}/login/?username=${encodeURIComponent(username)}&password=${encodeURIComponent(password)}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include', // Importante para lidar com cookies de autenticação
      });

      // Tenta pegar dados da resposta, mesmo se não for OK
      let data;
      const contentType = response.headers.get('content-type');
      
      if (contentType && contentType.includes('application/json')) {
        data = await response.json();
      } else {
        // Se não for JSON, trata como texto ou vazio
        const textContent = await response.text();
        data = textContent ? { message: textContent } : null;
      }

      if (!response.ok) {
        // Se o backend retornar um JSON de erro com 'detail' (comum no FastAPI)
        const errorMessage = data?.detail || data?.message || `Credenciais inválidas ou erro no servidor (Status: ${response.status}).`;
        throw new Error(errorMessage);
      }

      // Login bem-sucedido!
      console.log("Login bem-sucedido, dados recebidos:", data);
      
      // Verifica a estrutura dos dados retornados pelo backend
      // FastAPI OAuth provavelmente retorna um token e talvez dados do usuário
      const userData = {
        username: username,
        ...(data || {}) // Incorpora todos os dados retornados pelo backend, se houver
      };
      
      onLoginSuccess(userData);

    } catch (err) {
      console.error("Erro no login:", err);
      setError(err instanceof Error ? err.message : 'Ocorreu um erro desconhecido.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    // Adiciona a classe de tema dinamicamente
    <div className={`login-page-container ${isDarkMode ? 'dark-mode' : 'light-mode'}`}>
      <div className="login-form-wrapper">
        {/* Reutiliza o logo e título do chat */}
        <div className="login-header">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="logo-icon">
                <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"></path>
            </svg>
            <h1 className="login-title">Chat Edu - Login</h1>
        </div>

        <form onSubmit={handleLoginSubmit} className="login-form">
          <div className="login-input-group">
            <label htmlFor="username">Usuário</label>
            <input
              type="text"
              id="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Seu usuário"
              className="login-input"
              disabled={isLoading}
              aria-label="Campo de usuário"
            />
          </div>
          <div className="login-input-group">
            <label htmlFor="password">Senha</label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Sua senha"
              className="login-input"
              disabled={isLoading}
              aria-label="Campo de senha"
            />
          </div>

          {error && <p className="login-error-message">{error}</p>}

          <button
            type="submit"
            className="login-button"
            disabled={isLoading || !username || !password}
          >
            {isLoading ? (
              <div className="button-loading-indicator">
                <span></span><span></span><span></span>
              </div>
            ) : (
              'Entrar'
            )}
          </button>
        </form>
      </div>
    </div>
  );
}

export default Login;