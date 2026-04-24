import React, { useState, useEffect } from 'react';
import axios from 'axios';

const ManagerTripApprovals = () => {
  const [pendingRequests, setPendingRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedTrip, setSelectedTrip] = useState(null);
  const [approvalNotes, setApprovalNotes] = useState('');
  const [budgetAdjustments, setBudgetAdjustments] = useState({});

  useEffect(() => {
    fetchPendingRequests();
  }, []);

  const fetchPendingRequests = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get('http://localhost:8000/trip-budget/pending-requests', {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (response.data.success) {
        setPendingRequests(response.data.pending_requests);
      }
    } catch (err) {
      console.error('Error fetching pending requests:', err);
      setError('Failed to load pending trip requests');
    } finally {
      setLoading(false);
    }
  };

  const handleApproveTrip = async (tripId) => {
    try {
      const token = localStorage.getItem('token');
      const requestData = {
        trip_id: tripId,
        approval_notes: approvalNotes || null,
        budget_adjustments: Object.keys(budgetAdjustments).length > 0 ? budgetAdjustments : null
      };

      const response = await axios.post('http://localhost:8000/trip-budget/approve-trip', requestData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (response.data.success) {
        alert('Trip approved successfully!');
        setSelectedTrip(null);
        setApprovalNotes('');
        setBudgetAdjustments({});
        fetchPendingRequests();
      }
    } catch (err) {
      console.error('Error approving trip:', err);
      alert('Failed to approve trip: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleBudgetAdjustment = (expenseType, newAmount) => {
    setBudgetAdjustments(prev => ({
      ...prev,
      [expenseType]: parseFloat(newAmount) || 0
    }));
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount);
  };

  const getStatusColor = (status) => {
    const colors = {
      pending: '#ffc107',
      approved: '#28a745',
      active: '#007bff',
      completed: '#6c757d',
      cancelled: '#dc3545'
    };
    return colors[status] || '#6c757d';
  };

  if (loading) {
    return (
      <div className="manager-approvals">
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>Loading pending trip requests...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="manager-approvals">
        <div className="error-container">
          <h2>❌ Error</h2>
          <p>{error}</p>
          <button onClick={fetchPendingRequests} className="retry-btn">
            🔄 Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="manager-approvals">
      <div className="dashboard-header">
        <h1>👨‍💼 Trip Approval Dashboard</h1>
        <p>Review and approve employee trip requests</p>
      </div>

      {pendingRequests.length === 0 ? (
        <div className="no-requests">
          <h2>📋 No Pending Requests</h2>
          <p>All trip requests have been processed. Check back later for new requests.</p>
        </div>
      ) : (
        <div className="requests-section">
          <h2>⏳ Pending Trip Requests ({pendingRequests.length})</h2>
          
          <div className="requests-grid">
            {pendingRequests.map((trip) => (
              <div key={trip.trip_id} className="trip-request-card">
                <div className="request-header">
                  <div className="employee-info">
                    <h3>{trip.employee_name}</h3>
                    <span className="designation">{trip.designation.replace('_', ' ').toUpperCase()}</span>
                  </div>
                  <span 
                    className="status-badge" 
                    style={{ backgroundColor: getStatusColor(trip.status) }}
                  >
                    {trip.status.toUpperCase()}
                  </span>
                </div>
                
                <div className="trip-details">
                  <div className="detail-row">
                    <strong>Purpose:</strong> {trip.purpose}
                  </div>
                  <div className="detail-row">
                    <strong>Destination:</strong> {trip.destination} ({trip.destination_tier.replace('_', ' ')})
                  </div>
                  <div className="detail-row">
                    <strong>Duration:</strong> {trip.duration_days} days
                  </div>
                  <div className="detail-row">
                    <strong>Dates:</strong> {new Date(trip.start_date).toLocaleDateString()} - {new Date(trip.end_date).toLocaleDateString()}
                  </div>
                  <div className="detail-row">
                    <strong>Total Budget:</strong> {formatCurrency(trip.total_allocated)}
                  </div>
                  <div className="detail-row">
                    <strong>Requested:</strong> {new Date(trip.created_at).toLocaleDateString()}
                  </div>
                </div>

                <div className="budget-breakdown">
                  <h4>💰 Budget Breakdown</h4>
                  <div className="budget-items">
                    {Object.entries(trip.allocated_budget).map(([type, amount]) => (
                      <div key={type} className="budget-item">
                        <span className="budget-type">{type.replace('_', ' ').toUpperCase()}</span>
                        <span className="budget-amount">{formatCurrency(amount)}</span>
                      </div>
                    ))}
                  </div>
                </div>
                
                <div className="request-actions">
                  <button 
                    onClick={() => setSelectedTrip(trip)} 
                    className="review-btn"
                  >
                    📋 Review & Approve
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Approval Modal */}
      {selectedTrip && (
        <div className="modal-overlay">
          <div className="approval-modal">
            <div className="modal-header">
              <h3>✅ Approve Trip Request</h3>
              <button onClick={() => setSelectedTrip(null)} className="close-btn">×</button>
            </div>
            
            <div className="trip-summary">
              <h4>{selectedTrip.employee_name} - {selectedTrip.destination}</h4>
              <p><strong>Purpose:</strong> {selectedTrip.purpose}</p>
              <p><strong>Duration:</strong> {selectedTrip.duration_days} days</p>
              <p><strong>Dates:</strong> {new Date(selectedTrip.start_date).toLocaleDateString()} - {new Date(selectedTrip.end_date).toLocaleDateString()}</p>
            </div>

            <div className="budget-adjustment-section">
              <h4>💰 Budget Adjustments (Optional)</h4>
              <p>Modify budget allocations if needed:</p>
              
              <div className="budget-adjustments">
                {Object.entries(selectedTrip.allocated_budget).map(([type, originalAmount]) => (
                  <div key={type} className="adjustment-row">
                    <label>{type.replace('_', ' ').toUpperCase()}</label>
                    <div className="adjustment-input">
                      <span className="original-amount">Original: {formatCurrency(originalAmount)}</span>
                      <input
                        type="number"
                        placeholder={originalAmount}
                        value={budgetAdjustments[type] || ''}
                        onChange={(e) => handleBudgetAdjustment(type, e.target.value)}
                        className="budget-input"
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="approval-notes-section">
              <h4>📝 Approval Notes (Optional)</h4>
              <textarea
                value={approvalNotes}
                onChange={(e) => setApprovalNotes(e.target.value)}
                placeholder="Add any notes or comments about this approval..."
                className="notes-textarea"
                rows="3"
              />
            </div>
            
            <div className="modal-actions">
              <button 
                onClick={() => setSelectedTrip(null)} 
                className="cancel-btn"
              >
                Cancel
              </button>
              <button 
                onClick={() => handleApproveTrip(selectedTrip.trip_id)} 
                className="approve-btn"
              >
                ✅ Approve Trip
              </button>
            </div>
          </div>
        </div>
      )}

      <style jsx>{`
        .manager-approvals {
          max-width: 1400px;
          margin: 0 auto;
          padding: 20px;
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }

        .dashboard-header {
          text-align: center;
          margin-bottom: 30px;
        }

        .dashboard-header h1 {
          color: #2c3e50;
          margin-bottom: 10px;
        }

        .dashboard-header p {
          color: #6c757d;
          font-size: 1.1em;
        }

        .no-requests {
          text-align: center;
          padding: 60px 20px;
          background: #f8f9fa;
          border-radius: 15px;
        }

        .requests-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
          gap: 25px;
        }

        .trip-request-card {
          background: white;
          border-radius: 15px;
          padding: 25px;
          box-shadow: 0 8px 25px rgba(0,0,0,0.1);
          border: 1px solid #e1e8ed;
          transition: transform 0.2s ease, box-shadow 0.2s ease;
        }

        .trip-request-card:hover {
          transform: translateY(-2px);
          box-shadow: 0 12px 35px rgba(0,0,0,0.15);
        }

        .request-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 20px;
          padding-bottom: 15px;
          border-bottom: 2px solid #f8f9fa;
        }

        .employee-info h3 {
          margin: 0 0 5px 0;
          color: #2c3e50;
          font-size: 1.3em;
        }

        .designation {
          background: #e9ecef;
          color: #495057;
          padding: 4px 12px;
          border-radius: 15px;
          font-size: 0.8em;
          font-weight: 600;
        }

        .status-badge {
          color: white;
          padding: 6px 15px;
          border-radius: 20px;
          font-size: 0.8em;
          font-weight: 600;
        }

        .trip-details {
          margin-bottom: 20px;
        }

        .detail-row {
          margin: 10px 0;
          color: #6c757d;
        }

        .detail-row strong {
          color: #2c3e50;
          margin-right: 8px;
        }

        .budget-breakdown {
          background: #f8f9fa;
          padding: 15px;
          border-radius: 10px;
          margin-bottom: 20px;
        }

        .budget-breakdown h4 {
          margin: 0 0 15px 0;
          color: #2c3e50;
          font-size: 1.1em;
        }

        .budget-items {
          display: grid;
          gap: 8px;
        }

        .budget-item {
          display: flex;
          justify-content: space-between;
          padding: 8px 0;
          border-bottom: 1px solid #e9ecef;
        }

        .budget-type {
          font-weight: 600;
          color: #495057;
          font-size: 0.9em;
        }

        .budget-amount {
          font-weight: 600;
          color: #28a745;
        }

        .request-actions {
          text-align: center;
        }

        .review-btn {
          background: linear-gradient(135deg, #007bff, #0056b3);
          color: white;
          border: none;
          padding: 12px 30px;
          border-radius: 8px;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s ease;
          font-size: 1em;
        }

        .review-btn:hover {
          transform: translateY(-1px);
          box-shadow: 0 5px 15px rgba(0,123,255,0.3);
        }

        .modal-overlay {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0,0,0,0.6);
          display: flex;
          justify-content: center;
          align-items: center;
          z-index: 1000;
        }

        .approval-modal {
          background: white;
          border-radius: 20px;
          padding: 30px;
          max-width: 600px;
          width: 90%;
          max-height: 90vh;
          overflow-y: auto;
        }

        .modal-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 25px;
          padding-bottom: 15px;
          border-bottom: 2px solid #f8f9fa;
        }

        .modal-header h3 {
          margin: 0;
          color: #2c3e50;
        }

        .close-btn {
          background: none;
          border: none;
          font-size: 28px;
          cursor: pointer;
          color: #6c757d;
          padding: 0;
          width: 30px;
          height: 30px;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .trip-summary {
          background: #f8f9fa;
          padding: 20px;
          border-radius: 10px;
          margin-bottom: 25px;
        }

        .trip-summary h4 {
          margin: 0 0 15px 0;
          color: #2c3e50;
        }

        .trip-summary p {
          margin: 8px 0;
          color: #6c757d;
        }

        .budget-adjustment-section {
          margin-bottom: 25px;
        }

        .budget-adjustment-section h4 {
          color: #2c3e50;
          margin-bottom: 10px;
        }

        .budget-adjustments {
          display: grid;
          gap: 15px;
        }

        .adjustment-row {
          display: grid;
          grid-template-columns: 150px 1fr;
          align-items: center;
          gap: 15px;
        }

        .adjustment-row label {
          font-weight: 600;
          color: #495057;
          font-size: 0.9em;
        }

        .adjustment-input {
          display: flex;
          align-items: center;
          gap: 15px;
        }

        .original-amount {
          font-size: 0.9em;
          color: #6c757d;
          min-width: 120px;
        }

        .budget-input {
          padding: 8px 12px;
          border: 2px solid #e1e8ed;
          border-radius: 6px;
          font-size: 1em;
          width: 120px;
        }

        .budget-input:focus {
          outline: none;
          border-color: #007bff;
        }

        .approval-notes-section h4 {
          color: #2c3e50;
          margin-bottom: 10px;
        }

        .notes-textarea {
          width: 100%;
          padding: 12px;
          border: 2px solid #e1e8ed;
          border-radius: 8px;
          font-size: 1em;
          font-family: inherit;
          resize: vertical;
        }

        .notes-textarea:focus {
          outline: none;
          border-color: #007bff;
        }

        .modal-actions {
          display: flex;
          gap: 15px;
          justify-content: flex-end;
          margin-top: 25px;
          padding-top: 20px;
          border-top: 2px solid #f8f9fa;
        }

        .cancel-btn, .approve-btn {
          padding: 12px 25px;
          border: none;
          border-radius: 8px;
          font-weight: 600;
          cursor: pointer;
          font-size: 1em;
          transition: all 0.2s ease;
        }

        .cancel-btn {
          background: #6c757d;
          color: white;
        }

        .approve-btn {
          background: linear-gradient(135deg, #28a745, #1e7e34);
          color: white;
        }

        .cancel-btn:hover, .approve-btn:hover {
          transform: translateY(-1px);
          box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }

        .loading-container, .error-container {
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

        .retry-btn {
          background: #007bff;
          color: white;
          border: none;
          padding: 12px 25px;
          border-radius: 8px;
          font-weight: 600;
          cursor: pointer;
          margin-top: 15px;
        }

        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }

        @media (max-width: 768px) {
          .requests-grid {
            grid-template-columns: 1fr;
          }
          
          .adjustment-row {
            grid-template-columns: 1fr;
            gap: 8px;
          }
          
          .adjustment-input {
            flex-direction: column;
            align-items: flex-start;
            gap: 8px;
          }
          
          .modal-actions {
            flex-direction: column;
          }
        }
      `}</style>
    </div>
  );
};

export default ManagerTripApprovals;