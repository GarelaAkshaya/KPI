import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import LoginPage from './pages/LoginPage';
import HomePage from './pages/HomePage';
import KPIDashboardPage from './pages/KPIDashboardPage';
import StudentUploadPage from './pages/StudentUploadPage';
import FacultyDataPage from './pages/FacultyDataPage';
import StudentFeedbackPage from './pages/StudentFeedbackPage';
import FeedbackDashboardPage from './pages/FeedbackDashboardPage';
import DepartmentOverviewPage from './pages/DepartmentOverviewPage';
import { getStoredAuthToken } from './api';

function ProtectedRoute({ children }) {
  const token = getStoredAuthToken();
  return token ? children : <Navigate to="/" replace />;
}

function PublicRoute({ children }) {
  const token = getStoredAuthToken();
  return token ? <Navigate to="/home" replace /> : children;
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<PublicRoute><LoginPage /></PublicRoute>} />
      <Route path="/home" element={<ProtectedRoute><HomePage /></ProtectedRoute>} />
      <Route path="/upload-students" element={<ProtectedRoute><StudentUploadPage /></ProtectedRoute>} />
      <Route path="/faculty" element={<ProtectedRoute><FacultyDataPage /></ProtectedRoute>} />
      <Route path="/departments" element={<ProtectedRoute><DepartmentOverviewPage /></ProtectedRoute>} />
      <Route path="/dashboard" element={<ProtectedRoute><KPIDashboardPage /></ProtectedRoute>} />
      <Route path="/feedback" element={<ProtectedRoute><StudentFeedbackPage /></ProtectedRoute>} />
      <Route path="/feedback/dashboard" element={<ProtectedRoute><FeedbackDashboardPage /></ProtectedRoute>} />
      {/* Catch-all fallback route */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
