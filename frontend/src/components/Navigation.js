import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';

const Navigation = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const navItems = [
    { path: '/profile', label: '👤 Profile', icon: '👤' },
    { path: '/upload', label: '🚀 Upload Bill', icon: '📄' },
    { path: '/budget', label: '🧳 Trip Budget', icon: '🧳' },
    { path: '/team-bills', label: '👥 Team Bills', icon: '📊' },
  ];

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/login');
  };

  return (
    <nav style={{
      background: 'linear-gradient(135deg, #388e3c 0%, #2e7d32 100%)',
      padding: '16px 24px',
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      boxShadow: '0 4px 20px rgba(56, 142, 60, 0.2)',
      position: 'sticky',
      top: 0,
      zIndex: 1000,
      backdropFilter: 'blur(10px)'
    }}>
      <div style={{
        color: 'white',
        fontSize: '24px',
        fontWeight: '700',
        textShadow: '0 2px 4px rgba(0,0,0,0.1)',
        display: 'flex',
        alignItems: 'center',
        cursor: 'pointer'
      }}
      onClick={() => navigate('/upload')}>
        <span style={{ marginRight: '12px', fontSize: '28px' }}>🤖</span>
        AI Expense Manager
      </div>
      
      <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
        {navItems.map((item) => (
          <button
            key={item.path}
            onClick={() => navigate(item.path)}
            style={{
              background: location.pathname === item.path 
                ? 'rgba(255,255,255,0.25)' 
                : 'rgba(255,255,255,0.1)',
              color: 'white',
              border: location.pathname === item.path 
                ? '2px solid rgba(255,255,255,0.5)' 
                : '2px solid rgba(255,255,255,0.2)',
              padding: '10px 20px',
              borderRadius: '25px',
              cursor: 'pointer',
              fontSize: '15px',
              fontWeight: '600',
              transition: 'all 0.3s ease',
              textShadow: '0 1px 2px rgba(0,0,0,0.1)',
              boxShadow: location.pathname === item.path 
                ? '0 4px 12px rgba(255,255,255,0.2)' 
                : '0 2px 8px rgba(0,0,0,0.1)',
              transform: location.pathname === item.path ? 'scale(1.05)' : 'scale(1)'
            }}
            onMouseEnter={(e) => {
              if (location.pathname !== item.path) {
                e.target.style.background = 'rgba(255,255,255,0.2)';
                e.target.style.transform = 'scale(1.02)';
                e.target.style.boxShadow = '0 4px 12px rgba(255,255,255,0.15)';
              }
            }}
            onMouseLeave={(e) => {
              if (location.pathname !== item.path) {
                e.target.style.background = 'rgba(255,255,255,0.1)';
                e.target.style.transform = 'scale(1)';
                e.target.style.boxShadow = '0 2px 8px rgba(0,0,0,0.1)';
              }
            }}
          >
            {item.label}
          </button>
        ))}
        
        <div style={{ width: '1px', height: '30px', backgroundColor: 'rgba(255,255,255,0.3)', margin: '0 8px' }}></div>
        
        <button
          onClick={handleLogout}
          style={{
            background: 'linear-gradient(135deg, #f44336 0%, #d32f2f 100%)',
            color: 'white',
            border: '2px solid rgba(255,255,255,0.2)',
            padding: '10px 20px',
            borderRadius: '25px',
            cursor: 'pointer',
            fontSize: '15px',
            fontWeight: '600',
            transition: 'all 0.3s ease',
            textShadow: '0 1px 2px rgba(0,0,0,0.1)',
            boxShadow: '0 4px 12px rgba(244, 67, 54, 0.3)'
          }}
          onMouseEnter={(e) => {
            e.target.style.transform = 'scale(1.05)';
            e.target.style.boxShadow = '0 6px 16px rgba(244, 67, 54, 0.4)';
          }}
          onMouseLeave={(e) => {
            e.target.style.transform = 'scale(1)';
            e.target.style.boxShadow = '0 4px 12px rgba(244, 67, 54, 0.3)';
          }}
        >
          🚪 Logout
        </button>
      </div>
    </nav>
  );
};

export default Navigation;