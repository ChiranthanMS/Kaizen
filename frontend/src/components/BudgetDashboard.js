import React, { useState, useEffect } from 'react';
import axios from 'axios';

const BudgetDashboard = () => {
  const [budgetData, setBudgetData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [expenseSummary, setExpenseSummary] = useState(null);

  useEffect(() => {
    fetchBudgetData();
    fetchExpenseSummary();
  }, []);

  const fetchBudgetData = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get('http://localhost:8000/budget/fund-caps', {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (response.data.success) {
        setBudgetData(response.data);
      }
    } catch (err) {
      console.error('Error fetching budget data:', err);
      setError('Failed to load budget information');
    }
  };

  const fetchExpenseSummary = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get('http://localhost:8000/budget/expense-summary', {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (response.data.success) {
        setExpenseSummary(response.data.summary);
      }
    } catch (err) {
      console.error('Error fetching expense summary:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount);
  };

  const getProgressPercentage = (used, limit) => {
    if (!limit || limit === 0) return 0;
    return Math.min((used / limit) * 100, 100);
  };

  const getProgressColor = (percentage) => {
    if (percentage >= 90) return '#dc3545'; // Red
    if (percentage >= 70) return '#ffc107'; // Yellow
    return '#28a745'; // Green
  };

  const ExpenseCard = ({ title, expenseType, budgetCaps, currentUsage, remainingBudget }) => {
    const dailyUsed = currentUsage?.daily || 0;
    const monthlyUsed = currentUsage?.monthly || 0;
    const dailyLimit = budgetCaps?.daily_limit || 0;
    const monthlyLimit = budgetCaps?.monthly_limit || 0;
    const dailyRemaining = remainingBudget?.daily || dailyLimit;
    const monthlyRemaining = remainingBudget?.monthly || monthlyLimit;

    const dailyPercentage = getProgressPercentage(dailyUsed, dailyLimit);
    const monthlyPercentage = getProgressPercentage(monthlyUsed, monthlyLimit);

    return (
      <div className="budget-card">
        <div className="budget-card-header">
          <h3>{title}</h3>
          <span className="expense-type-badge">{expenseType}</span>
        </div>
        
        <div className="budget-limits">
          <div className="limit-section">
            <h4>Daily Limit</h4>
            <div className="progress-container">
              <div className="progress-bar">
                <div 
                  className="progress-fill" 
                  style={{ 
                    width: `${dailyPercentage}%`,
                    backgroundColor: getProgressColor(dailyPercentage)
                  }}
                ></div>
              </div>
              <div className="progress-text">
                <span className="used">{formatCurrency(dailyUsed)}</span>
                <span className="separator"> / </span>
                <span className="limit">{formatCurrency(dailyLimit)}</span>
              </div>
              <div className="remaining">
                Remaining: <strong>{formatCurrency(dailyRemaining)}</strong>
              </div>
            </div>
          </div>

          <div className="limit-section">
            <h4>Monthly Limit</h4>
            <div className="progress-container">
              <div className="progress-bar">
                <div 
                  className="progress-fill" 
                  style={{ 
                    width: `${monthlyPercentage}%`,
                    backgroundColor: getProgressColor(monthlyPercentage)
                  }}
                ></div>
              </div>
              <div className="progress-text">
                <span className="used">{formatCurrency(monthlyUsed)}</span>
                <span className="separator"> / </span>
                <span className="limit">{formatCurrency(monthlyLimit)}</span>
              </div>
              <div className="remaining">
                Remaining: <strong>{formatCurrency(monthlyRemaining)}</strong>
              </div>
            </div>
          </div>

          {budgetCaps?.per_trip_limit && (
            <div className="per-trip-limit">
              <small>Per Trip Limit: {formatCurrency(budgetCaps.per_trip_limit)}</small>
            </div>
          )}
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="budget-dashboard">
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>Loading budget information...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="budget-dashboard">
        <div className="error-container">
          <h2>Budget Information</h2>
          <div className="error-message">
            <p>{error}</p>
            <button onClick={fetchBudgetData} className="retry-button">
              Retry
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!budgetData || !expenseSummary) {
    return (
      <div className="budget-dashboard">
        <div className="no-data-container">
          <h2>Budget Information</h2>
          <p>No budget data available. Please contact your administrator.</p>
        </div>
      </div>
    );
  }

  const expenseTypes = [
    { key: 'travel', title: 'Travel Expenses', icon: '✈️' },
    { key: 'hotel', title: 'Hotel & Lodging', icon: '🏨' },
    { key: 'food', title: 'Food & Meals', icon: '🍽️' },
    { key: 'local_transport', title: 'Local Transport', icon: '🚗' },
    { key: 'miscellaneous', title: 'Miscellaneous', icon: '📋' }
  ];

  return (
    <div className="budget-dashboard">
      <div className="budget-header">
        <h1>💰 Budget Dashboard</h1>
        <div className="employee-info">
          <div className="info-item">
            <strong>Designation:</strong> {budgetData.designation}
          </div>
          <div className="info-item">
            <strong>City Tier:</strong> {budgetData.work_city_tier.replace('_', ' ').toUpperCase()}
          </div>
          <div className="info-item">
            <strong>Session Expires:</strong> {new Date(budgetData.session_expires_at).toLocaleString()}
          </div>
        </div>
      </div>

      <div className="budget-grid">
        {expenseTypes.map(({ key, title, icon }) => (
          <ExpenseCard
            key={key}
            title={`${icon} ${title}`}
            expenseType={key}
            budgetCaps={budgetData.fund_caps[key]}
            currentUsage={expenseSummary.current_usage[key]}
            remainingBudget={expenseSummary.remaining_budget[key]}
          />
        ))}
      </div>

      <div className="budget-actions">
        <button 
          onClick={fetchBudgetData} 
          className="refresh-button"
        >
          🔄 Refresh Budget Data
        </button>
        
        <button 
          onClick={() => window.location.href = '/upload'} 
          className="upload-button"
        >
          📤 Upload New Expense
        </button>
      </div>

      <div className="budget-tips">
        <h3>💡 Budget Tips</h3>
        <ul>
          <li>Monitor your daily spending to stay within monthly limits</li>
          <li>Higher tier cities have increased allowances for travel and accommodation</li>
          <li>Keep receipts for all expenses for easy claim processing</li>
          <li>Contact your manager if you need to exceed budget limits</li>
        </ul>
      </div>

      <style jsx>{`
        .budget-dashboard {
          max-width: 1200px;
          margin: 0 auto;
          padding: 20px;
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }

        .budget-header {
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
          padding: 30px;
          border-radius: 15px;
          margin-bottom: 30px;
          box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }

        .budget-header h1 {
          margin: 0 0 20px 0;
          font-size: 2.5em;
          font-weight: 700;
        }

        .employee-info {
          display: flex;
          gap: 30px;
          flex-wrap: wrap;
        }

        .info-item {
          background: rgba(255,255,255,0.1);
          padding: 10px 15px;
          border-radius: 8px;
          backdrop-filter: blur(10px);
        }

        .budget-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
          gap: 25px;
          margin-bottom: 30px;
        }

        .budget-card {
          background: white;
          border-radius: 15px;
          padding: 25px;
          box-shadow: 0 8px 25px rgba(0,0,0,0.1);
          border: 1px solid #e1e8ed;
          transition: transform 0.2s ease, box-shadow 0.2s ease;
        }

        .budget-card:hover {
          transform: translateY(-5px);
          box-shadow: 0 15px 35px rgba(0,0,0,0.15);
        }

        .budget-card-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 20px;
          padding-bottom: 15px;
          border-bottom: 2px solid #f8f9fa;
        }

        .budget-card-header h3 {
          margin: 0;
          color: #2c3e50;
          font-size: 1.3em;
          font-weight: 600;
        }

        .expense-type-badge {
          background: #e3f2fd;
          color: #1976d2;
          padding: 5px 12px;
          border-radius: 20px;
          font-size: 0.8em;
          font-weight: 500;
          text-transform: uppercase;
        }

        .limit-section {
          margin-bottom: 20px;
        }

        .limit-section h4 {
          margin: 0 0 10px 0;
          color: #495057;
          font-size: 1em;
          font-weight: 600;
        }

        .progress-container {
          margin-bottom: 15px;
        }

        .progress-bar {
          width: 100%;
          height: 12px;
          background-color: #e9ecef;
          border-radius: 6px;
          overflow: hidden;
          margin-bottom: 8px;
        }

        .progress-fill {
          height: 100%;
          transition: width 0.3s ease;
          border-radius: 6px;
        }

        .progress-text {
          display: flex;
          justify-content: space-between;
          align-items: center;
          font-size: 0.9em;
          color: #6c757d;
          margin-bottom: 5px;
        }

        .used {
          font-weight: 600;
          color: #495057;
        }

        .limit {
          font-weight: 500;
        }

        .remaining {
          font-size: 0.9em;
          color: #28a745;
          font-weight: 500;
        }

        .per-trip-limit {
          background: #f8f9fa;
          padding: 8px 12px;
          border-radius: 6px;
          text-align: center;
          color: #6c757d;
        }

        .budget-actions {
          display: flex;
          gap: 15px;
          justify-content: center;
          margin-bottom: 30px;
        }

        .refresh-button, .upload-button {
          padding: 12px 25px;
          border: none;
          border-radius: 8px;
          font-size: 1em;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s ease;
        }

        .refresh-button {
          background: #17a2b8;
          color: white;
        }

        .refresh-button:hover {
          background: #138496;
          transform: translateY(-2px);
        }

        .upload-button {
          background: #28a745;
          color: white;
        }

        .upload-button:hover {
          background: #218838;
          transform: translateY(-2px);
        }

        .budget-tips {
          background: #f8f9fa;
          padding: 25px;
          border-radius: 15px;
          border-left: 5px solid #ffc107;
        }

        .budget-tips h3 {
          margin: 0 0 15px 0;
          color: #495057;
        }

        .budget-tips ul {
          margin: 0;
          padding-left: 20px;
        }

        .budget-tips li {
          margin-bottom: 8px;
          color: #6c757d;
          line-height: 1.5;
        }

        .loading-container, .error-container, .no-data-container {
          text-align: center;
          padding: 60px 20px;
        }

        .loading-spinner {
          width: 50px;
          height: 50px;
          border: 5px solid #f3f3f3;
          border-top: 5px solid #007bff;
          border-radius: 50%;
          animation: spin 1s linear infinite;
          margin: 0 auto 20px;
        }

        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }

        .error-message {
          background: #f8d7da;
          color: #721c24;
          padding: 20px;
          border-radius: 8px;
          margin: 20px 0;
        }

        .retry-button {
          background: #dc3545;
          color: white;
          border: none;
          padding: 10px 20px;
          border-radius: 5px;
          cursor: pointer;
          margin-top: 10px;
        }

        .retry-button:hover {
          background: #c82333;
        }

        @media (max-width: 768px) {
          .budget-grid {
            grid-template-columns: 1fr;
          }
          
          .employee-info {
            flex-direction: column;
            gap: 10px;
          }
          
          .budget-actions {
            flex-direction: column;
            align-items: center;
          }
        }
      `}</style>
    </div>
  );
};

export default BudgetDashboard;