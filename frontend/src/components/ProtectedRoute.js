import React, { useEffect } from "react";
import { useNavigate } from "react-router-dom";

function ProtectedRoute({ children }) {
  const navigate = useNavigate();

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) {
      navigate("/login");
    }
  }, [navigate]);

  const token = localStorage.getItem("token");
  
  // If no token, don't render children (will redirect in useEffect)
  if (!token) {
    return null;
  }

  return children;
}

export default ProtectedRoute;