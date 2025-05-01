import React from 'react';
import './CoursesList.css';

function CoursesList({ courses, isDarkMode }) {
  return (
    <div className={`courses-container ${isDarkMode ? 'dark-mode' : 'light-mode'}`}>
      <h2>Meus Cursos</h2>
      {courses && courses.length > 0 ? (
        <div className="courses-grid">
          {courses.map((course, index) => (
            <div key={index} className="course-card">
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
