import React, { useState, useEffect } from 'react';
import './App.css';
import Login from './Login';
import Dashboard from './Dashboard';

//===========================================================================//
//  Componente Principal da Aplicação (Gerencia Login e Tema)                //
//===========================================================================//
function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [userData, setUserData] = useState(null); // Guarda dados do usuário/cursos
  const [isDarkMode, setIsDarkMode] = useState(() => {
    // Verifica preferência do usuário ou sistema ao carregar
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
      return savedTheme === 'dark';
    }
    return window.matchMedia?.('(prefers-color-scheme: dark)').matches || false;
  });

  // Aplica a classe de tema ao HTML e salva a preferência
  useEffect(() => {
    const root = window.document.documentElement;
    const currentTheme = isDarkMode ? 'dark' : 'light';
    const oldTheme = isDarkMode ? 'light' : 'dark';
    root.classList.remove(`${oldTheme}-mode`); // Remove a classe antiga
    root.classList.add(`${currentTheme}-mode`); // Adiciona a classe nova
    localStorage.setItem('theme', currentTheme); // Salva no localStorage
  }, [isDarkMode]);

  // Função para ser chamada pelo Login em caso de sucesso
  const handleLoginSuccess = (data) => {
    console.log("Login bem-sucedido no App principal, dados:", data);
    setUserData(data); // Armazena os dados retornados (cursos, username, etc.)
    setIsLoggedIn(true);
    // Opcional: Salvar estado de login (ex: sessionStorage para segurança um pouco maior)
    try {
      sessionStorage.setItem('isLoggedIn', 'true');
      sessionStorage.setItem('userData', JSON.stringify(data));
    } catch (error) {
        console.error("Falha ao salvar dados de sessão:", error)
    }

  };

  // Função de Logout
  const handleLogout = () => {
    setIsLoggedIn(false);
    setUserData(null);
    // Opcional: Limpar estado salvo
    sessionStorage.removeItem('isLoggedIn');
    sessionStorage.removeItem('userData');
    // Pode ser útil limpar o histórico do chat ao sair
    // setChatHistory([]); // Se o state do chat fosse gerenciado aqui
  };

  // Opcional: Verificar estado de login ao carregar a página
  useEffect(() => {
    const loggedInStatus = sessionStorage.getItem('isLoggedIn');
    const storedUserData = sessionStorage.getItem('userData');
    if (loggedInStatus === 'true' && storedUserData) {
      try {
        setUserData(JSON.parse(storedUserData));
        setIsLoggedIn(true);
        console.log("Sessão restaurada.");
      } catch (e) {
        console.error("Falha ao restaurar dados da sessão:", e);
        handleLogout(); // Limpa estado inválido
      }
    }
  }, []); // Executa apenas uma vez ao montar

  // Função para alternar o tema
  const toggleTheme = () => {
    setIsDarkMode(prev => !prev);
  };

  // --- Renderização Condicional ---
  if (!isLoggedIn) {
    return <Login onLoginSuccess={handleLoginSuccess} isDarkMode={isDarkMode} />;
  }

  return (
    <Dashboard 
      user={userData}
      onLogout={handleLogout}
      isDarkMode={isDarkMode}
      toggleDarkMode={toggleTheme}
    />
  );
}

export default App;