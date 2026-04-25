import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";

// Create axios instance with auth header
const api = axios.create({
  baseURL: "http://localhost:8000",
});

// Add interceptor to include token and no-cache headers in requests
api.interceptors.request.use((config) => {
  const token = sessionStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
    config.headers['Cache-Control'] = 'no-cache';
    config.headers['Pragma'] = 'no-cache';
  }
  return config;
});

function ProfilePage() {
  const navigate = useNavigate();
  const [profile, setProfile] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [message, setMessage] = useState("");

  // Check authentication on component mount
  useEffect(() => {
    const token = sessionStorage.getItem("token");
    if (!token) {
      navigate("/login");
      return;
    }
    
    fetchProfile();
  }, [navigate]);

  const fetchProfile = async () => {
    setIsLoading(true);
    try {
      const res = await api.get("/profile");
      setProfile(res.data);
    } catch (err) {
      console.error("Error fetching profile:", err);
      if (err.response?.status === 401) {
        // Token expired or invalid
        sessionStorage.removeItem("token");
        navigate("/login");
      } else {
        setMessage("Error loading profile information.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    sessionStorage.removeItem("token");
    navigate("/login");
  };

  const goToEnhancedUpload = () => {
    navigate("/upload");
  };

  // Loading spinner component
  const LoadingSpinner = () => (
    <div className="loading-spinner">
      <div className="spinner"></div>
    </div>
  );

  return (
    <div className="container">
      {/* Header */}
      <div className="profile-header">
        <h1 className="app-title">Employee Dashboard</h1>
      </div>

      {/* Profile Content */}
      <div className="profile-content">
        {isLoading ? (
          <div className="loading-container">
            <LoadingSpinner />
            <p>Loading profile...</p>
          </div>
        ) : profile ? (
          <div className="profile-info">
            <div className="profile-card">
              <div className="profile-avatar">
                {profile.name ? profile.name.charAt(0).toUpperCase() : 
                 profile.username ? profile.username.charAt(0).toUpperCase() : 
                 profile.email ? profile.email.charAt(0).toUpperCase() : '?'}
              </div>
              
              <div className="profile-details">
                {profile.name && (
                  <div className="profile-field">
                    <label>Name:</label>
                    <span>{profile.name}</span>
                  </div>
                )}
                
                {profile.username && (
                  <div className="profile-field">
                    <label>Username:</label>
                    <span>{profile.username}</span>
                  </div>
                )}
                
                {profile.email && (
                  <div className="profile-field">
                    <label>Email:</label>
                    <span>{profile.email}</span>
                  </div>
                )}
                
                <div className="profile-field">
                  <label>Authentication Type:</label>
                  <span className={`auth-type ${profile.auth_type}`}>
                    {profile.auth_type === 'google' ? 'Google Account' : 'Regular Account'}
                  </span>
                </div>
                
                {profile.created_at && (
                  <div className="profile-field">
                    <label>Member Since:</label>
                    <span>{new Date(profile.created_at).toLocaleDateString()}</span>
                  </div>
                )}
              </div>
            </div>

            <div className="profile-actions">
              <div style={{
                background: 'linear-gradient(135deg, #e8f5e8 0%, #c8e6c9 100%)',
                border: '2px solid #4CAF50',
                borderRadius: '20px',
                padding: '32px',
                textAlign: 'center',
                boxShadow: '0 8px 32px rgba(76, 175, 80, 0.2)',
                transition: 'all 0.3s ease',
                cursor: 'pointer'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'translateY(-4px)';
                e.currentTarget.style.boxShadow = '0 12px 40px rgba(76, 175, 80, 0.3)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.boxShadow = '0 8px 32px rgba(76, 175, 80, 0.2)';
              }}
              onClick={goToEnhancedUpload}>
                <div style={{ fontSize: '48px', marginBottom: '16px' }}>🚀</div>
                <h2 style={{ 
                  margin: '0 0 16px 0', 
                  color: '#2e7d32', 
                  fontSize: '28px', 
                  fontWeight: '700' 
                }}>
                  AI-Powered Expense Management
                </h2>
                <p style={{ 
                  margin: '0 0 24px 0', 
                  color: '#4CAF50', 
                  fontSize: '16px', 
                  lineHeight: '1.6',
                  fontWeight: '500'
                }}>
                  Upload your receipts and bills for AI-powered processing with Gemini 2.0 Flash technology. 
                  Get 90%+ accuracy with automatic data extraction.
                </p>
                <button style={{
                  background: 'linear-gradient(135deg, #4CAF50 0%, #45a049 100%)',
                  color: 'white',
                  border: 'none',
                  padding: '16px 32px',
                  borderRadius: '50px',
                  fontSize: '18px',
                  fontWeight: '600',
                  cursor: 'pointer',
                  transition: 'all 0.3s ease',
                  boxShadow: '0 6px 20px rgba(76, 175, 80, 0.3)',
                  textShadow: '0 1px 2px rgba(0, 0, 0, 0.1)'
                }}
                onMouseEnter={(e) => {
                  e.target.style.transform = 'scale(1.05)';
                  e.target.style.boxShadow = '0 8px 25px rgba(76, 175, 80, 0.4)';
                }}
                onMouseLeave={(e) => {
                  e.target.style.transform = 'scale(1)';
                  e.target.style.boxShadow = '0 6px 20px rgba(76, 175, 80, 0.3)';
                }}>
                  🚀 Upload & Process Bill
                </button>
              </div>
            </div>
          </div>
        ) : (
          <div className="error-container">
            <p>Unable to load profile information.</p>
            <button className="btn btn-primary" onClick={fetchProfile}>
              Try Again
            </button>
          </div>
        )}
      </div>

      {/* Message Display */}
      {message && (
        <div className="message error">
          {message}
        </div>
      )}
    </div>
  );
}

export default ProfilePage;