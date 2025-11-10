import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import type { Course } from '@/types';
import { api } from '@/services/api';
import { toast } from 'sonner';

interface AuthContextType {
  isAuthenticated: boolean;
  user: { username: string } | null;
  courses: Course[];
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const STORAGE_KEYS = {
  USER: 'chat_edu_user',
  COURSES: 'chat_edu_courses',
  AUTH: 'chat_edu_auth',
};

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState<{ username: string } | null>(null);
  const [courses, setCourses] = useState<Course[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Restaurar sessão do localStorage ao carregar
  useEffect(() => {
    try {
      const storedAuth = localStorage.getItem(STORAGE_KEYS.AUTH);
      const storedUser = localStorage.getItem(STORAGE_KEYS.USER);
      const storedCourses = localStorage.getItem(STORAGE_KEYS.COURSES);

      if (storedAuth === 'true' && storedUser && storedCourses) {
        setIsAuthenticated(true);
        setUser(JSON.parse(storedUser));
        setCourses(JSON.parse(storedCourses));
      }
    } catch (error) {
      console.error('Erro ao restaurar sessão:', error);
      // Limpar dados corrompidos
      localStorage.removeItem(STORAGE_KEYS.AUTH);
      localStorage.removeItem(STORAGE_KEYS.USER);
      localStorage.removeItem(STORAGE_KEYS.COURSES);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const login = async (username: string, password: string) => {
    try {
      const response = await api.login(username, password);
      
      if (response.success && response.cursos) {
        const userData = { username };
        
        setIsAuthenticated(true);
        setUser(userData);
        setCourses(response.cursos);

        // Persistir no localStorage
        localStorage.setItem(STORAGE_KEYS.AUTH, 'true');
        localStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(userData));
        localStorage.setItem(STORAGE_KEYS.COURSES, JSON.stringify(response.cursos));

        toast.success('Login realizado com sucesso!');
      } else {
        throw new Error(response.message || 'Falha no login');
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Erro ao fazer login';
      toast.error(errorMessage);
      throw error;
    }
  };

  const logout = () => {
    setIsAuthenticated(false);
    setUser(null);
    setCourses([]);

    // Limpar localStorage
    localStorage.removeItem(STORAGE_KEYS.AUTH);
    localStorage.removeItem(STORAGE_KEYS.USER);
    localStorage.removeItem(STORAGE_KEYS.COURSES);

    toast.success('Logout realizado com sucesso!');
  };

  return (
    <AuthContext.Provider value={{ isAuthenticated, user, courses, login, logout, isLoading }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
