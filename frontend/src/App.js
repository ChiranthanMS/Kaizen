import React from "react";
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import { AuthPage, ProfilePage, ProtectedRoute } from "./components";
import ProfessionalEmployeeDashboard from "./components/ProfessionalEmployeeDashboard";
import ProfessionalManagerDashboard from "./components/ProfessionalManagerDashboard";
import RoleBasedRedirect from "./components/RoleBasedRedirect";
import TripDebugger from "./components/TripDebugger";
import "./styles.css";

function App() {
  return (
    <Router>
      <div className="App">
        <Routes>
          {/* Public Routes */}
          <Route path="/login" element={<AuthPage />} />
          <Route path="/register" element={<AuthPage />} />
          
          {/* Protected Routes */}
          <Route 
            path="/profile" 
            element={
              <ProtectedRoute>
                <ProfilePage />
              </ProtectedRoute>
            } 
          />
          
          {/* Employee Dashboard */}
          <Route 
            path="/employee-dashboard" 
            element={
              <ProtectedRoute>
                <ProfessionalEmployeeDashboard />
              </ProtectedRoute>
            } 
          />
          
          {/* Manager Dashboard */}
          <Route 
            path="/manager-dashboard" 
            element={
              <ProtectedRoute>
                <ProfessionalManagerDashboard />
              </ProtectedRoute>
            } 
          />
          
          {/* Legacy Routes - Redirect to new dashboards */}
          <Route path="/upload" element={<Navigate to="/employee-dashboard" replace />} />
          <Route path="/upload-bill" element={<Navigate to="/employee-dashboard" replace />} />
          <Route path="/enhanced-upload" element={<Navigate to="/employee-dashboard" replace />} />
          <Route path="/budget" element={<Navigate to="/employee-dashboard" replace />} />
          <Route path="/team-bills" element={<Navigate to="/manager-dashboard" replace />} />
          
          {/* Debug Route */}
          <Route 
            path="/debug" 
            element={
              <ProtectedRoute>
                <TripDebugger />
              </ProtectedRoute>
            } 
          />
          
          {/* Default redirect based on user role */}
          <Route 
            path="/" 
            element={
              <ProtectedRoute>
                <RoleBasedRedirect />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="*" 
            element={
              <ProtectedRoute>
                <RoleBasedRedirect />
              </ProtectedRoute>
            } 
          />
        </Routes>
      </div>
    </Router>
  );
}

export default App;