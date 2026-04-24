import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";

function AuthPage() {
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loginIdentifier, setLoginIdentifier] = useState(""); // username or email 
  const [message, setMessage] = useState("");
  const [googleUser, setGoogleUser] = useState(null);
  const [currentPage, setCurrentPage] = useState("login"); // "login" or "register"
  const [showForgot, setShowForgot] = useState(false);
  const [resetStep, setResetStep] = useState(1); // 1: send code, 2: enter code + new pw
  const [resetEmail, setResetEmail] = useState("");
  const [resetCode, setResetCode] = useState("");
  const [resetNewPassword, setResetNewPassword] = useState("");
  const [resetConfirmNewPassword, setResetConfirmNewPassword] = useState("");
  
  // Registration extras
  const [role, setRole] = useState("employee"); // 'employee' or 'manager'
  const [fullName, setFullName] = useState("");
  const [department, setDepartment] = useState("");
  const [managerId, setManagerId] = useState("");
  const [designation, setDesignation] = useState("associate");
  const [workCity, setWorkCity] = useState("");
  const [employeeId, setEmployeeId] = useState("");
  
  // Loading states
  const [isLoading, setIsLoading] = useState(false);
  const [isLoginLoading, setIsLoginLoading] = useState(false);
  const [isRegisterLoading, setIsRegisterLoading] = useState(false);
  const [isResetLoading, setIsResetLoading] = useState(false);

  // Check if user is already logged in
  useEffect(() => {
    const token = localStorage.getItem("token");
    if (token) {
      navigate("/profile");
    }
  }, [navigate]);

  // Validation helpers
  const isEmailValid = (value) => /[^\s@]+@[^\s@]+\.[^\s@]+/.test(value);
  const passHasLen = password.length >= 8;
  const passHasUpper = /[A-Z]/.test(password);
  const passHasLower = /[a-z]/.test(password);
  const passHasNumber = /\d/.test(password);
  const passHasSpecial = /[^A-Za-z0-9]/.test(password);
  const isPasswordStrong = passHasLen && passHasUpper && passHasLower && passHasNumber && passHasSpecial;

  // Reset password validators
  const rPassHasLen = resetNewPassword.length >= 8;
  const rPassHasUpper = /[A-Z]/.test(resetNewPassword);
  const rPassHasLower = /[a-z]/.test(resetNewPassword);
  const rPassHasNumber = /\d/.test(resetNewPassword);
  const rPassHasSpecial = /[^A-Za-z0-9]/.test(resetNewPassword);
  const isResetPasswordStrong = rPassHasLen && rPassHasUpper && rPassHasLower && rPassHasNumber && rPassHasSpecial;

  // Utilities to normalize messages (objects, arrays, error shapes) to string
  const toMessageText = (value) => {
    if (value == null || value === undefined) return "";
    if (typeof value === "string") return value;
    if (typeof value === "number" || typeof value === "boolean") return String(value);
    
    try {
      if (typeof value === "object") {
        if (typeof value.detail === "string") return value.detail;
        if (typeof value.message === "string") return value.message;
        // FastAPI/DRF validation errors can be arrays or objects
        if (Array.isArray(value) && value.length > 0) {
          // Try to surface the first human-friendly message
          const first = value[0];
          if (typeof first === "string") return first;
          if (first && typeof first.msg === "string") return first.msg;
        }
      }
      return JSON.stringify(value);
    } catch {
      return String(value || "");
    }
  };

  // Show success message with auto-clear
  const showSuccessMessage = (msg) => {
    const text = toMessageText(msg) || "Success";
    setMessage(text);
    setTimeout(() => setMessage(""), 5000);
  };

  // Show error message with auto-clear
  const showErrorMessage = (msg) => {
    const text = toMessageText(msg) || "An error occurred";
    setMessage(text);
    setTimeout(() => setMessage(""), 7000);
  };

  const register = async () => {
    if (!username || !email || !password || !confirmPassword) {
      showErrorMessage("All fields are required");
      return;
    }

    if (!isEmailValid(email)) {
      showErrorMessage("Please enter a valid email address");
      return;
    }

    if (password !== confirmPassword) {
      showErrorMessage("Passwords do not match");
      return;
    }

    if (!isPasswordStrong) {
      showErrorMessage("Please meet the password requirements below");
      return;
    }

    setIsRegisterLoading(true);
    try {
      await axios.post("http://localhost:8000/register", {
        username,
        email,
        password,
        role,
        full_name: fullName,
        department,
        manager_id: managerId || null,
        designation,
        work_city: workCity,
        employee_id: employeeId || null,
      });
      
      // Show success message and redirect to login page
      showSuccessMessage("Registration successful! Please login with your credentials.");
      setCurrentPage("login");
      
      // Clear form fields
      setUsername("");
      setEmail("");
      setPassword("");
      setConfirmPassword("");
      
    } catch (err) {
      showErrorMessage(err.response?.data?.detail || "Error registering");
    } finally {
      setIsRegisterLoading(false);
    }
  };

  const login = async () => {
    if (!loginIdentifier || !password) {
      showErrorMessage("Please enter your username or email and password");
      return;
    }
    
    setIsLoginLoading(true);
    try {
      const payload = loginIdentifier.includes("@")
        ? { email: loginIdentifier, password }
        : { username: loginIdentifier, password };
      const res = await axios.post("http://localhost:8000/login", payload);
      
      // Save token
      const { access_token, message: resMessage } = res.data;
      if (!access_token) {
        throw new Error("Empty access token received");
      }
      localStorage.setItem("token", access_token);
      showSuccessMessage(resMessage);
      
      // Fetch profile to determine role and route accordingly
      const profileRes = await axios.get("http://localhost:8000/profile", {
        headers: { Authorization: `Bearer ${access_token}` }
      });
      const role = profileRes?.data?.role || "employee";
      
      if (role === "manager") {
        navigate("/team-bills");
      } else {
        navigate("/profile");
      }
    } catch (err) {
      const detail = err.response?.data?.detail || err.message || "Error logging in";
      showErrorMessage(detail);
      // Ensure no stale/empty token blocks routing
      localStorage.removeItem("token");
    } finally {
      setIsLoginLoading(false);
    }
  };

  // Forgot password flow
  const sendResetCode = async () => {
    if (!resetEmail || !isEmailValid(resetEmail)) {
      showErrorMessage("Enter a valid email to receive a code");
      return;
    }
    
    setIsResetLoading(true);
    try {
      await axios.post("http://localhost:8000/forgot-password", { email: resetEmail });
      showSuccessMessage("If the email exists, a reset code has been sent. Check your inbox.");
      setResetStep(2);
    } catch (err) {
      // Always generic
      showSuccessMessage("If the email exists, a reset code has been sent. Check your inbox.");
      setResetStep(2);
    } finally {
      setIsResetLoading(false);
    }
  };

  const resetPassword = async () => {
    if (!resetCode || !resetNewPassword || !resetConfirmNewPassword) {
      showErrorMessage("All fields are required");
      return;
    }
    if (resetNewPassword !== resetConfirmNewPassword) {
      showErrorMessage("Passwords do not match");
      return;
    }
    if (!isResetPasswordStrong) {
      showErrorMessage("Please meet the password requirements below");
      return;
    }
    
    setIsResetLoading(true);
    try {
      await axios.post("http://localhost:8000/reset-password", {
        email: resetEmail,
        code: resetCode,
        new_password: resetNewPassword,
      });
      showSuccessMessage("Password reset successful. Please login with your new password.");
      // Reset forgot state and go back to login
      setShowForgot(false);
      setCurrentPage("login");
      setLoginIdentifier(resetEmail); // prefill email
      setResetEmail("");
      setResetCode("");
      setResetNewPassword("");
      setResetConfirmNewPassword("");
    } catch (err) {
      showErrorMessage(err.response?.data?.detail || "Unable to reset password. Check your code and try again.");
    } finally {
      setIsResetLoading(false);
    }
  };

  // Handle Google Sign-In response
  const handleGoogleResponse = async (response) => {
    setIsLoading(true);
    try {
      const credential = response.credential;
      const payload = JSON.parse(atob(credential.split('.')[1]));
      
      // Extract user info from the JWT payload
      const googleUserInfo = {
        email: payload.email,
        name: payload.name
      };
      
      setGoogleUser(googleUserInfo);
      
      // Send to backend
      const res = await axios.post("http://localhost:8000/google-login", googleUserInfo);
      
      // Save token
      const { access_token, message: resMessage } = res.data;
      localStorage.setItem("token", access_token);
      showSuccessMessage(resMessage);
      
      // Redirect to profile page
      navigate("/profile");
    } catch (err) {
      showErrorMessage(err.response?.data?.detail || "Error with Google Sign-In");
    } finally {
      setIsLoading(false);
    }
  };

  // Initialize Google Sign-In
  useEffect(() => {
    // Fetch Google Client ID from backend
    const fetchGoogleClientId = async () => {
      try {
        const response = await axios.get("http://localhost:8000/google-client-id");
        const clientId = response.data.client_id;
        
        if (window.google && clientId) {
          window.google.accounts.id.initialize({
            client_id: clientId,
            callback: handleGoogleResponse,
          });

          window.google.accounts.id.renderButton(
            document.getElementById("google-signin"),
            { theme: "outline", size: "large", text: "signin_with", shape: "rectangular" }
          );
        }
      } catch (err) {
        console.error("Error fetching Google Client ID:", err);
        showErrorMessage("Error initializing Google Sign-In");
      }
    };

    fetchGoogleClientId();
  }, []);

  // Determine message class based on content (robust against non-strings)
  const getMessageClass = () => {
    if (!message) return "";
    const text = typeof message === "string" ? message : toMessageText(message);
    // Ensure text is always a string before calling toLowerCase
    const safeText = typeof text === "string" ? text : String(text || "");
    const lower = safeText.toLowerCase();
    return (lower.includes("error") || lower.includes("fail") || lower.includes("invalid"))
      ? "message error"
      : "message success";
  };

  // Clear message when switching pages
  const switchToPage = (page) => {
    setCurrentPage(page);
    setMessage("");
    setUsername("");
    setEmail("");
    setPassword("");
    setConfirmPassword("");
    setLoginIdentifier("");
    setShowForgot(false);
    setResetStep(1);
    setResetEmail("");
    setResetCode("");
    setResetNewPassword("");
    setResetConfirmNewPassword("");
    setRole("employee");
    setFullName("");
    setDepartment("");
    setManagerId("");
    setDesignation("associate");
    setWorkCity("");
    setEmployeeId("");
  };

  // Enhanced loading spinner component
  const LoadingSpinner = () => (
    <div style={{
      display: 'inline-flex',
      alignItems: 'center',
      gap: '8px'
    }}>
      <div style={{
        width: '20px',
        height: '20px',
        border: '3px solid rgba(255, 255, 255, 0.3)',
        borderTop: '3px solid white',
        borderRadius: '50%',
        animation: 'spin 0.8s linear infinite'
      }}></div>
      <div style={{
        display: 'flex',
        gap: '3px'
      }}>
        <div style={{
          width: '4px',
          height: '4px',
          backgroundColor: 'rgba(255, 255, 255, 0.8)',
          borderRadius: '50%',
          animation: 'pulse 1.4s ease-in-out infinite'
        }}></div>
        <div style={{
          width: '4px',
          height: '4px',
          backgroundColor: 'rgba(255, 255, 255, 0.8)',
          borderRadius: '50%',
          animation: 'pulse 1.4s ease-in-out 0.2s infinite'
        }}></div>
        <div style={{
          width: '4px',
          height: '4px',
          backgroundColor: 'rgba(255, 255, 255, 0.8)',
          borderRadius: '50%',
          animation: 'pulse 1.4s ease-in-out 0.4s infinite'
        }}></div>
      </div>
    </div>
  );

  return (
    <>
      {/* Enhanced CSS Animations */}
      <style>
        {`
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
          
          @keyframes pulse {
            0%, 100% { 
              opacity: 0.4;
              transform: scale(0.8);
            }
            50% { 
              opacity: 1;
              transform: scale(1.2);
            }
          }
          
          @keyframes slideInUp {
            from {
              opacity: 0;
              transform: translateY(30px);
            }
            to {
              opacity: 1;
              transform: translateY(0);
            }
          }
          
          @keyframes fadeInScale {
            from {
              opacity: 0;
              transform: scale(0.95);
            }
            to {
              opacity: 1;
              transform: scale(1);
            }
          }
          
          .enhanced-container {
            animation: fadeInScale 0.6s ease-out;
            max-width: 900px;
            width: 100%;
            margin: 40px auto;
            background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
            border-radius: 24px;
            box-shadow: 0 20px 60px rgba(76, 175, 80, 0.1), 0 8px 32px rgba(0, 0, 0, 0.05);
            padding: 48px;
            text-align: center;
            border: 2px solid rgba(76, 175, 80, 0.1);
            position: relative;
            overflow: hidden;
          }
          
          .enhanced-container::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 6px;
            background: linear-gradient(135deg, #388e3c 0%, #2e7d32 100%);
            border-radius: 24px 24px 0 0;
          }
          
          .enhanced-container::after {
            content: '🤖';
            position: absolute;
            top: 30px;
            right: 30px;
            font-size: 48px;
            opacity: 0.05;
            transform: rotate(15deg);
            pointer-events: none;
          }
          
          .enhanced-title {
            color: #2e7d32;
            font-size: 42px;
            margin-bottom: 16px;
            font-weight: 700;
            letter-spacing: -0.5px;
            background: linear-gradient(135deg, #388e3c 0%, #2e7d32 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            position: relative;
            z-index: 1;
          }
          
          .enhanced-subtitle {
            color: #4CAF50;
            font-size: 18px;
            margin-bottom: 40px;
            font-weight: 500;
            opacity: 0.9;
          }
        `}
      </style>
      
      <div className="enhanced-container">
        <h1 className="enhanced-title">🚀 AI Expense Manager</h1>
        <p className="enhanced-subtitle">Intelligent bill processing with 90%+ accuracy</p>
      
      {/* Enhanced Page Navigation */}
      <div style={{
        display: 'flex',
        marginBottom: '40px',
        borderRadius: '16px',
        background: 'rgba(76, 175, 80, 0.1)',
        padding: '6px',
        border: '1px solid rgba(76, 175, 80, 0.2)',
        position: 'relative',
        zIndex: 1
      }}>
        <button 
          style={{
            flex: 1,
            padding: '14px 24px',
            border: 'none',
            background: currentPage === "login" 
              ? 'linear-gradient(135deg, #4CAF50 0%, #45a049 100%)' 
              : 'transparent',
            color: currentPage === "login" ? 'white' : '#4CAF50',
            fontSize: '16px',
            fontWeight: '600',
            cursor: 'pointer',
            transition: 'all 0.3s ease',
            borderRadius: '12px',
            boxShadow: currentPage === "login" 
              ? '0 4px 12px rgba(76, 175, 80, 0.3)' 
              : 'none',
            transform: currentPage === "login" ? 'scale(1.02)' : 'scale(1)',
            textShadow: currentPage === "login" ? '0 1px 2px rgba(0,0,0,0.1)' : 'none'
          }}
          onClick={() => switchToPage("login")}
          disabled={isLoading}
          onMouseEnter={(e) => {
            if (currentPage !== "login") {
              e.target.style.background = 'rgba(76, 175, 80, 0.15)';
              e.target.style.transform = 'scale(1.01)';
            }
          }}
          onMouseLeave={(e) => {
            if (currentPage !== "login") {
              e.target.style.background = 'transparent';
              e.target.style.transform = 'scale(1)';
            }
          }}
        >
          🔐 Login
        </button>
        <button 
          style={{
            flex: 1,
            padding: '14px 24px',
            border: 'none',
            background: currentPage === "register" 
              ? 'linear-gradient(135deg, #4CAF50 0%, #45a049 100%)' 
              : 'transparent',
            color: currentPage === "register" ? 'white' : '#4CAF50',
            fontSize: '16px',
            fontWeight: '600',
            cursor: 'pointer',
            transition: 'all 0.3s ease',
            borderRadius: '12px',
            boxShadow: currentPage === "register" 
              ? '0 4px 12px rgba(76, 175, 80, 0.3)' 
              : 'none',
            transform: currentPage === "register" ? 'scale(1.02)' : 'scale(1)',
            textShadow: currentPage === "register" ? '0 1px 2px rgba(0,0,0,0.1)' : 'none'
          }}
          onClick={() => switchToPage("register")}
          disabled={isLoading}
          onMouseEnter={(e) => {
            if (currentPage !== "register") {
              e.target.style.background = 'rgba(76, 175, 80, 0.15)';
              e.target.style.transform = 'scale(1.01)';
            }
          }}
          onMouseLeave={(e) => {
            if (currentPage !== "register") {
              e.target.style.background = 'transparent';
              e.target.style.transform = 'scale(1)';
            }
          }}
        >
          📝 Register
        </button>
      </div>

      {currentPage === "login" ? (
        // Login or Forgot Password Page
        <div className="auth-page">
          {!showForgot ? (
            <>
              <h2 className="page-title">Welcome Back!</h2>
              <p className="page-description">Sign in with your username or email</p>
              
              <div className="input-group">
                <label className="input-label">Username or Email</label>
                <input
                  className="input-field"
                  placeholder="Enter your username or email"
                  value={loginIdentifier}
                  onChange={(e) => setLoginIdentifier(e.target.value)}
                  disabled={isLoginLoading}
                />
              </div>
              
              <div className="input-group">
                <label className="input-label">Password</label>
                <input
                  className="input-field"
                  type="password"
                  placeholder="Enter your password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  disabled={isLoginLoading}
                />
              </div>
              
              <button 
                style={{
                  width: '100%',
                  padding: '16px 24px',
                  border: 'none',
                  borderRadius: '12px',
                  fontSize: '18px',
                  fontWeight: '600',
                  cursor: isLoginLoading ? 'not-allowed' : 'pointer',
                  transition: 'all 0.3s ease',
                  background: isLoginLoading 
                    ? 'linear-gradient(135deg, #bdbdbd 0%, #9e9e9e 100%)' 
                    : 'linear-gradient(135deg, #4CAF50 0%, #45a049 100%)',
                  color: 'white',
                  boxShadow: isLoginLoading 
                    ? '0 4px 12px rgba(0, 0, 0, 0.1)' 
                    : '0 6px 20px rgba(76, 175, 80, 0.3)',
                  transform: isLoginLoading ? 'scale(0.98)' : 'scale(1)',
                  textShadow: '0 1px 2px rgba(0, 0, 0, 0.1)',
                  position: 'relative',
                  overflow: 'hidden',
                  marginBottom: '20px'
                }}
                onClick={login}
                disabled={isLoginLoading}
                onMouseEnter={(e) => {
                  if (!isLoginLoading) {
                    e.target.style.transform = 'scale(1.02)';
                    e.target.style.boxShadow = '0 8px 25px rgba(76, 175, 80, 0.4)';
                  }
                }}
                onMouseLeave={(e) => {
                  if (!isLoginLoading) {
                    e.target.style.transform = 'scale(1)';
                    e.target.style.boxShadow = '0 6px 20px rgba(76, 175, 80, 0.3)';
                  }
                }}
              >
                {isLoginLoading ? (
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '12px' }}>
                    <LoadingSpinner />
                    <span>Signing In...</span>
                  </div>
                ) : (
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
                    <span>🚀</span>
                    <span>Sign In</span>
                  </div>
                )}
              </button>

              <div style={{ textAlign: 'center', marginBottom: '20px' }}>
                <button 
                  style={{
                    background: 'none',
                    border: 'none',
                    color: '#4CAF50',
                    fontSize: '14px',
                    fontWeight: '500',
                    cursor: 'pointer',
                    textDecoration: 'underline',
                    transition: 'all 0.3s ease',
                    padding: '8px 16px',
                    borderRadius: '8px'
                  }}
                  onClick={() => { setShowForgot(true); setMessage(""); }}
                  disabled={isLoading}
                  onMouseEnter={(e) => {
                    e.target.style.color = '#2e7d32';
                    e.target.style.background = 'rgba(76, 175, 80, 0.1)';
                    e.target.style.textDecoration = 'none';
                  }}
                  onMouseLeave={(e) => {
                    e.target.style.color = '#4CAF50';
                    e.target.style.background = 'none';
                    e.target.style.textDecoration = 'underline';
                  }}
                >
                  🔑 Forgot password?
                </button>
              </div>
              
              <div style={{
                display: 'flex',
                alignItems: 'center',
                textAlign: 'center',
                margin: '30px 0',
                color: '#4CAF50',
                fontSize: '14px',
                fontWeight: '600'
              }}>
                <div style={{
                  flex: 1,
                  height: '1px',
                  background: 'linear-gradient(to right, transparent, rgba(76, 175, 80, 0.3), transparent)'
                }}></div>
                <span style={{ 
                  padding: '0 20px',
                  background: 'rgba(76, 175, 80, 0.1)',
                  borderRadius: '20px',
                  border: '1px solid rgba(76, 175, 80, 0.2)'
                }}>OR</span>
                <div style={{
                  flex: 1,
                  height: '1px',
                  background: 'linear-gradient(to left, transparent, rgba(76, 175, 80, 0.3), transparent)'
                }}></div>
              </div>
              
              <div className="google-signin-container">
                <div id="google-signin"></div>
              </div>
            </>
          ) : (
            <>
              <h2 className="page-title">Reset your password</h2>
              {resetStep === 1 ? (
                <>
                  <p className="page-description">Enter your account email to receive a 6-digit code</p>
                  <div className="input-group">
                    <label className="input-label">Email</label>
                    <input
                      className="input-field"
                      type="email"
                      placeholder="you@example.com"
                      value={resetEmail}
                      onChange={(e) => setResetEmail(e.target.value)}
                      disabled={isResetLoading}
                    />
                  </div>
                  <button 
                    className="btn btn-primary login-btn" 
                    onClick={sendResetCode}
                    disabled={isResetLoading}
                  >
                    {isResetLoading ? <LoadingSpinner /> : "Send Reset Code"}
                  </button>
                  <div className="login-link">
                    <button 
                      className="link-button" 
                      onClick={() => setShowForgot(false)}
                      disabled={isLoading}
                    >
                      Back to login
                    </button>
                  </div>
                </>
              ) : (
                <>
                  <p className="page-description">Enter the code sent to your email and set a new password</p>
                  <div className="input-group">
                    <label className="input-label">Verification Code</label>
                    <input
                      className="input-field"
                      placeholder="6-digit code"
                      value={resetCode}
                      onChange={(e) => setResetCode(e.target.value)}
                      disabled={isResetLoading}
                    />
                  </div>
                  <div className="input-group">
                    <label className="input-label">New Password</label>
                    <input
                      className="input-field"
                      type="password"
                      placeholder="Create a strong password"
                      value={resetNewPassword}
                      onChange={(e) => setResetNewPassword(e.target.value)}
                      disabled={isResetLoading}
                    />
                    <ul className="requirements-list">
                      <li className={`req-item ${rPassHasLen ? 'pass' : 'fail'}`}>At least 8 characters</li>
                      <li className={`req-item ${rPassHasUpper ? 'pass' : 'fail'}`}>One uppercase letter (A-Z)</li>
                      <li className={`req-item ${rPassHasLower ? 'pass' : 'fail'}`}>One lowercase letter (a-z)</li>
                      <li className={`req-item ${rPassHasNumber ? 'pass' : 'fail'}`}>One number (0-9)</li>
                      <li className={`req-item ${rPassHasSpecial ? 'pass' : 'fail'}`}>One special character (!@#$…)</li>
                    </ul>
                  </div>
                  <div className="input-group">
                    <label className="input-label">Confirm New Password</label>
                    <input
                      className="input-field"
                      type="password"
                      placeholder="Confirm your new password"
                      value={resetConfirmNewPassword}
                      onChange={(e) => setResetConfirmNewPassword(e.target.value)}
                      disabled={isResetLoading}
                    />
                  </div>
                  <button 
                    className="btn btn-primary login-btn" 
                    onClick={resetPassword}
                    disabled={isResetLoading}
                  >
                    {isResetLoading ? <LoadingSpinner /> : "Reset Password"}
                  </button>
                  <div className="login-link">
                    <button 
                      className="link-button" 
                      onClick={() => { setShowForgot(false); setResetStep(1); }}
                      disabled={isLoading}
                    >
                      Back to login
                    </button>
                  </div>
                </>
              )}
            </>
          )}
        </div>
      ) : (
        // Register Page
        <div className="auth-page">
          <h2 className="page-title">Create Account</h2>
          <p className="page-description">Join us and start your journey</p>
          
          <div className="input-group">
            <label className="input-label">Username</label>
            <input
              className="input-field"
              placeholder="Choose a username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              disabled={isRegisterLoading}
            />
          </div>

          <div className="input-group">
            <label className="input-label">Email</label>
            <input
              className="input-field"
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={isRegisterLoading}
            />
            {email && (
              <div className={`helper-text ${isEmailValid(email) ? 'valid' : 'invalid'}`}>
                {isEmailValid(email) ? '✓ Email looks good' : '✗ Enter a valid email address'}
              </div>
            )}
          </div>

          {/* Role selection */}
          <div className="input-group">
            <label className="input-label">Role</label>
            <select
              className="input-field"
              value={role}
              onChange={(e) => setRole(e.target.value)}
              disabled={isRegisterLoading}
            >
              <option value="employee">Employee</option>
              <option value="manager">Manager</option>
            </select>
          </div>

          {/* Optional profile fields */}
          <div className="input-group">
            <label className="input-label">Full Name (optional)</label>
            <input
              className="input-field"
              placeholder="Your name"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              disabled={isRegisterLoading}
            />
          </div>

          <div className="input-group">
            <label className="input-label">Department (optional)</label>
            <input
              className="input-field"
              placeholder="e.g., Sales, Engineering"
              value={department}
              onChange={(e) => setDepartment(e.target.value)}
              disabled={isRegisterLoading}
            />
          </div>

          <div className="input-group">
            <label className="input-label">Designation</label>
            <select
              className="input-field"
              value={designation}
              onChange={(e) => setDesignation(e.target.value)}
              disabled={isRegisterLoading}
            >
              <option value="intern">Intern</option>
              <option value="associate">Associate</option>
              <option value="senior_associate">Senior Associate</option>
              <option value="manager">Manager</option>
              <option value="senior_manager">Senior Manager</option>
              <option value="director">Director</option>
              <option value="senior_director">Senior Director</option>
              <option value="vp">Vice President</option>
              <option value="svp">Senior Vice President</option>
            </select>
          </div>

          <div className="input-group">
            <label className="input-label">Work City</label>
            <input
              className="input-field"
              placeholder="e.g., Mumbai, Delhi, Bangalore"
              value={workCity}
              onChange={(e) => setWorkCity(e.target.value)}
              disabled={isRegisterLoading}
            />
          </div>

          <div className="input-group">
            <label className="input-label">Employee ID (optional)</label>
            <input
              className="input-field"
              placeholder="Company employee ID"
              value={employeeId}
              onChange={(e) => setEmployeeId(e.target.value)}
              disabled={isRegisterLoading}
            />
          </div>

          {role === "employee" && (
            <div className="input-group">
              <label className="input-label">Manager ID (optional)</label>
              <input
                className="input-field"
                placeholder="Manager user id"
                value={managerId}
                onChange={(e) => setManagerId(e.target.value)}
                disabled={isRegisterLoading}
              />
            </div>
          )}
          
          <div className="input-group">
            <label className="input-label">Password</label>
            <input
              className="input-field"
              type="password"
              placeholder="Create a strong password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={isRegisterLoading}
            />
            <ul className="requirements-list">
              <li className={`req-item ${passHasLen ? 'pass' : 'fail'}`}>At least 8 characters</li>
              <li className={`req-item ${passHasUpper ? 'pass' : 'fail'}`}>One uppercase letter (A-Z)</li>
              <li className={`req-item ${passHasLower ? 'pass' : 'fail'}`}>One lowercase letter (a-z)</li>
              <li className={`req-item ${passHasNumber ? 'pass' : 'fail'}`}>One number (0-9)</li>
              <li className={`req-item ${passHasSpecial ? 'pass' : 'fail'}`}>One special character (!@#$…)</li>
            </ul>
          </div>

          <div className="input-group">
            <label className="input-label">Confirm Password</label>
            <input
              className="input-field"
              type="password"
              placeholder="Confirm your password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              disabled={isRegisterLoading}
            />
            {confirmPassword && (
              <div className={`helper-text ${password && confirmPassword === password ? 'valid' : 'invalid'}`}>
                {password && confirmPassword === password ? '✓ Passwords match' : '✗ Passwords do not match'}
              </div>
            )}
          </div>
          
          <button 
            style={{
              width: '100%',
              padding: '16px 24px',
              border: 'none',
              borderRadius: '12px',
              fontSize: '18px',
              fontWeight: '600',
              cursor: isRegisterLoading ? 'not-allowed' : 'pointer',
              transition: 'all 0.3s ease',
              background: isRegisterLoading 
                ? 'linear-gradient(135deg, #bdbdbd 0%, #9e9e9e 100%)' 
                : 'linear-gradient(135deg, #4CAF50 0%, #45a049 100%)',
              color: 'white',
              boxShadow: isRegisterLoading 
                ? '0 4px 12px rgba(0, 0, 0, 0.1)' 
                : '0 6px 20px rgba(76, 175, 80, 0.3)',
              transform: isRegisterLoading ? 'scale(0.98)' : 'scale(1)',
              textShadow: '0 1px 2px rgba(0, 0, 0, 0.1)',
              position: 'relative',
              overflow: 'hidden',
              marginBottom: '20px'
            }}
            onClick={register}
            disabled={isRegisterLoading}
            onMouseEnter={(e) => {
              if (!isRegisterLoading) {
                e.target.style.transform = 'scale(1.02)';
                e.target.style.boxShadow = '0 8px 25px rgba(76, 175, 80, 0.4)';
              }
            }}
            onMouseLeave={(e) => {
              if (!isRegisterLoading) {
                e.target.style.transform = 'scale(1)';
                e.target.style.boxShadow = '0 6px 20px rgba(76, 175, 80, 0.3)';
              }
            }}
          >
            {isRegisterLoading ? (
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '12px' }}>
                <LoadingSpinner />
                <span>Creating Account...</span>
              </div>
            ) : (
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
                <span>✨</span>
                <span>Create Account</span>
              </div>
            )}
          </button>
          
          <p style={{ 
            textAlign: 'center', 
            color: '#666', 
            fontSize: '14px', 
            marginTop: '20px' 
          }}>
            Already have an account?{" "}
            <button 
              style={{
                background: 'none',
                border: 'none',
                color: '#4CAF50',
                fontSize: '14px',
                fontWeight: '600',
                cursor: 'pointer',
                textDecoration: 'underline',
                transition: 'all 0.3s ease',
                padding: '4px 8px',
                borderRadius: '6px'
              }}
              onClick={() => switchToPage("login")}
              disabled={isLoading}
              onMouseEnter={(e) => {
                e.target.style.color = '#2e7d32';
                e.target.style.background = 'rgba(76, 175, 80, 0.1)';
                e.target.style.textDecoration = 'none';
              }}
              onMouseLeave={(e) => {
                e.target.style.color = '#4CAF50';
                e.target.style.background = 'none';
                e.target.style.textDecoration = 'underline';
              }}
            >
              Sign in here
            </button>
          </p>
        </div>
      )}
      
      {googleUser && (
        <div style={{
          background: 'rgba(76, 175, 80, 0.1)',
          border: '2px solid rgba(76, 175, 80, 0.3)',
          borderRadius: '16px',
          padding: '24px',
          marginTop: '20px',
          textAlign: 'center'
        }}>
          <h3 style={{ color: '#2e7d32', margin: '0 0 12px 0' }}>✅ Signed in Successfully</h3>
          <p style={{ margin: '0 0 8px 0', color: '#4CAF50' }}>Welcome, <strong>{googleUser.name}</strong></p>
          <p style={{ margin: '0', color: '#666', fontSize: '14px' }}>{googleUser.email}</p>
        </div>
      )}
      
      {/* Enhanced Message Display */}
      {message && (
        <div style={{
          marginTop: '24px',
          padding: '16px 20px',
          borderRadius: '12px',
          fontSize: '14px',
          fontWeight: '500',
          textAlign: 'center',
          background: message.toLowerCase().includes('error') || message.toLowerCase().includes('fail') 
            ? 'rgba(244, 67, 54, 0.1)' 
            : 'rgba(76, 175, 80, 0.1)',
          border: message.toLowerCase().includes('error') || message.toLowerCase().includes('fail')
            ? '1px solid rgba(244, 67, 54, 0.3)'
            : '1px solid rgba(76, 175, 80, 0.3)',
          color: message.toLowerCase().includes('error') || message.toLowerCase().includes('fail')
            ? '#d32f2f'
            : '#2e7d32',
          animation: 'slideInUp 0.3s ease-out'
        }}>
          {message.toLowerCase().includes('error') || message.toLowerCase().includes('fail') ? '❌' : '✅'} {message}
        </div>
      )}
      </div>
    </>
  );
}

export default AuthPage;