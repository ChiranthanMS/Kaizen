import React, { useState } from 'react';
import axios from 'axios';

const TripDebugger = () => {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const testTripCreation = async () => {
    setLoading(true);
    setResult(null);

    const tripData = {
      trip_purpose: 'Debug test meeting',
      destination_city: 'Mumbai',
      start_date: '2025-08-23',
      end_date: '2025-08-26'
    };

    try {
      const token = localStorage.getItem('token');
      console.log('Token:', token ? `${token.substring(0, 20)}...` : 'No token found');
      console.log('Trip data:', tripData);

      const response = await axios.post(
        'http://localhost:8000/trip-budget/create-trip',
        tripData,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      );

      setResult({
        success: true,
        status: response.status,
        data: response.data
      });

    } catch (error) {
      console.error('Full error:', error);
      console.error('Error response:', error.response);
      
      setResult({
        success: false,
        status: error.response?.status || 'Network Error',
        error: error.response?.data || error.message,
        fullError: {
          message: error.message,
          response: error.response?.data,
          status: error.response?.status,
          headers: error.response?.headers
        }
      });
    } finally {
      setLoading(false);
    }
  };

  const checkAuth = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get('http://localhost:8000/profile', {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setResult({
        success: true,
        type: 'auth_check',
        data: response.data
      });
    } catch (error) {
      setResult({
        success: false,
        type: 'auth_check',
        error: error.response?.data || error.message
      });
    } finally {
      setLoading(false);
    }
  };

  const testDebugEndpoint = async () => {
    setLoading(true);
    setResult(null);

    const tripData = {
      trip_purpose: 'Debug test meeting',
      destination_city: 'Mumbai',
      start_date: '2025-08-23',
      end_date: '2025-08-26'
    };

    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(
        'http://localhost:8000/trip-budget/debug-request',
        tripData,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      );

      setResult({
        success: true,
        type: 'debug_endpoint',
        status: response.status,
        data: response.data
      });

    } catch (error) {
      setResult({
        success: false,
        type: 'debug_endpoint',
        status: error.response?.status || 'Network Error',
        error: error.response?.data || error.message
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: '20px', fontFamily: 'monospace' }}>
      <h2>🐛 Trip Creation Debugger</h2>
      
      <div style={{ marginBottom: '20px' }}>
        <button 
          onClick={checkAuth} 
          disabled={loading}
          style={{ marginRight: '10px', padding: '10px 20px' }}
        >
          🔐 Check Authentication
        </button>
        
        <button 
          onClick={testDebugEndpoint} 
          disabled={loading}
          style={{ marginRight: '10px', padding: '10px 20px' }}
        >
          🔍 Test Debug Endpoint
        </button>
        
        <button 
          onClick={testTripCreation} 
          disabled={loading}
          style={{ padding: '10px 20px' }}
        >
          🧳 Test Trip Creation
        </button>
      </div>

      {loading && <div>⏳ Loading...</div>}

      {result && (
        <div style={{ 
          background: result.success ? '#d4edda' : '#f8d7da', 
          border: `1px solid ${result.success ? '#c3e6cb' : '#f5c6cb'}`,
          borderRadius: '5px',
          padding: '15px',
          marginTop: '20px'
        }}>
          <h3>{result.success ? '✅ Success' : '❌ Error'}</h3>
          
          <div><strong>Status:</strong> {result.status}</div>
          
          {result.type === 'auth_check' && (
            <div>
              <h4>Authentication Check:</h4>
              <pre>{JSON.stringify(result.data || result.error, null, 2)}</pre>
            </div>
          )}
          
          {result.type === 'debug_endpoint' && (
            <div>
              <h4>Debug Endpoint Test:</h4>
              <pre>{JSON.stringify(result.data || result.error, null, 2)}</pre>
            </div>
          )}
          
          {result.success && result.data && (
            <div>
              <h4>Response Data:</h4>
              <pre>{JSON.stringify(result.data, null, 2)}</pre>
            </div>
          )}
          
          {!result.success && result.error && (
            <div>
              <h4>Error Details:</h4>
              <pre>{JSON.stringify(result.error, null, 2)}</pre>
            </div>
          )}
          
          {result.fullError && (
            <div>
              <h4>Full Error Object:</h4>
              <pre>{JSON.stringify(result.fullError, null, 2)}</pre>
            </div>
          )}
        </div>
      )}
      
      <div style={{ marginTop: '30px', fontSize: '12px', color: '#666' }}>
        <h4>Debug Info:</h4>
        <div>Token exists: {localStorage.getItem('token') ? 'Yes' : 'No'}</div>
        <div>Current URL: {window.location.href}</div>
        <div>User Agent: {navigator.userAgent}</div>
      </div>
    </div>
  );
};

export default TripDebugger;