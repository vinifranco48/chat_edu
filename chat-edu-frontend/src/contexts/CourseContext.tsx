import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import type { Course } from '@/types';

interface CourseContextType {
  selectedCourse: Course | null;
  setSelectedCourse: (course: Course | null) => void;
}

const CourseContext = createContext<CourseContextType | undefined>(undefined);

const STORAGE_KEY = 'chat_edu_selected_course';

export const CourseProvider = ({ children }: { children: ReactNode }) => {
  const [selectedCourse, setSelectedCourse] = useState<Course | null>(null);

  // Restaurar curso selecionado do localStorage
  useEffect(() => {
    try {
      const storedCourse = localStorage.getItem(STORAGE_KEY);
      if (storedCourse) {
        setSelectedCourse(JSON.parse(storedCourse));
      }
    } catch (error) {
      console.error('Erro ao restaurar curso selecionado:', error);
      localStorage.removeItem(STORAGE_KEY);
    }
  }, []);

  // Persistir curso selecionado no localStorage
  const handleSetSelectedCourse = (course: Course | null) => {
    setSelectedCourse(course);
    if (course) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(course));
    } else {
      localStorage.removeItem(STORAGE_KEY);
    }
  };

  return (
    <CourseContext.Provider value={{ selectedCourse, setSelectedCourse: handleSetSelectedCourse }}>
      {children}
    </CourseContext.Provider>
  );
};

export const useCourse = () => {
  const context = useContext(CourseContext);
  if (context === undefined) {
    throw new Error('useCourse must be used within a CourseProvider');
  }
  return context;
};
