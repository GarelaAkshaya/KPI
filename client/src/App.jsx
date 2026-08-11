import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import LoginPage from './pages/LoginPage';
import HomePage from './pages/HomePage';
import KPIDashboardPage from './pages/KPIDashboardPage';
import StudentUploadPage from './pages/StudentUploadPage';
import FacultyDataPage from './pages/FacultyDataPage';

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<LoginPage />} />
      <Route path="/home" element={<HomePage />} />
      <Route path="/upload-students" element={<StudentUploadPage />} />
      <Route path="/faculty" element={<FacultyDataPage />} />
      <Route path="/dashboard" element={<KPIDashboardPage />} />
      {/* Catch-all fallback route */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
