import React from 'react';
import './CoursesList.css';

function CoursesList({ courses, isDarkMode, onCourseSelect }) {
  const handleCourseClick = async (courseId) => {
    try {      const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
      const response = await fetch(`${API_BASE_URL}/retriever/${courseId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`Erro ${response.status}`);
      }

      const result = await response.json();
      onCourseSelect && onCourseSelect(courseId, result);
    } catch (error) {
      console.error('Erro ao carregar embeddings do curso:', error);
      // Podemos adicionar uma notificação visual do erro aqui se desejarmos
    }
  };

  return (
    <div className={`courses-container ${isDarkMode ? 'dark-mode' : 'light-mode'}`}>
      <h2>Meus Cursos</h2>
      {courses && courses.length > 0 ? (
        <div className="courses-grid">
          {courses.map((course, index) => (
            <div 
              key={index} 
              className="course-card"
              onClick={() => handleCourseClick(course.id)}
              role="button"
              tabIndex={0}
            >
              <div className="course-info">
                <h3>{course.nome || course.name}</h3>
                <p>{course.descricao || course.description}</p>
              </div>
              <div className="course-footer">
                <span className="course-progress">
                  {course.progresso || course.progress || 0}% completo
                </span>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="empty-courses">
          <p>Nenhum curso disponível no momento.</p>
        </div>
      )}
    </div>
  );
}

export default CoursesList;
