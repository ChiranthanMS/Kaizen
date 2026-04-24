import React from 'react';
import Navigation from './Navigation';

const Layout = ({ children }) => {
  return (
    <div style={{ 
      minHeight: '100vh', 
      background: 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)',
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
    }}>
      <Navigation />
      <main style={{ 
        padding: '0',
        minHeight: 'calc(100vh - 80px)',
        position: 'relative'
      }}>
        {/* Background decoration */}
        <div style={{
          position: 'fixed',
          top: '50%',
          right: '5%',
          fontSize: '200px',
          opacity: '0.03',
          transform: 'translateY(-50%) rotate(15deg)',
          zIndex: 0,
          pointerEvents: 'none'
        }}>🤖</div>
        
        <div style={{
          position: 'fixed',
          bottom: '10%',
          left: '5%',
          fontSize: '150px',
          opacity: '0.03',
          transform: 'rotate(-15deg)',
          zIndex: 0,
          pointerEvents: 'none'
        }}>📄</div>
        
        <div style={{ position: 'relative', zIndex: 1 }}>
          {children}
        </div>
      </main>
    </div>
  );
};

export default Layout;