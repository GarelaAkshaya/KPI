import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import LoginPage from './pages/LoginPage';
import HomePage from './pages/HomePage';
import KPIDashboardPage from './pages/KPIDashboardPage';
import StudentDataPage from './pages/StudentDataPage';

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<LoginPage />} />
      <Route path="/home" element={<HomePage />} />
      <Route path="/dashboard" element={<KPIDashboardPage />} />
      <Route path="/students" element={<StudentDataPage />} />
      {/* Catch-all fallback route */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
