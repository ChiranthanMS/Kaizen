import React, { useState, useEffect } from 'react';
import axios from 'axios';

const TripBudgetDashboard = () => {
  const [trips, setTrips] = useState([]);
  const [activeTrip, setActiveTrip] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showCreateTrip, setShowCreateTrip] = useState(false);
  const [showBudgetCalculator, setShowBudgetCalculator] = useState(false);
  const [justificationTexts, setJustificationTexts] = useState({});

  // Trip creation form
  const [tripForm, setTripForm] = useState({
    trip_purpose: '',
    destination_city: '',
    start_date: '',
    end_date: ''
  });

  // Budget calculator form
  const [calculatorForm, setCalculatorForm] = useState({
    destination_city: '',
    start_date: '',
    end_date: ''
  });
  const [calculatedBudget, setCalculatedBudget] = useState(null);

  useEffect(() => {
    fetchTrips();
    fetchActiveTrip();
  }, []);

  const fetchTrips = async () => {
    try {
      const token = sessionStorage.getItem('token');
      const response = await axios.get('http://localhost:8000/trip-budget/my-trips', {
        headers: { 
          Authorization: `Bearer ${token}`,
          'Cache-Control': 'no-cache',
          'Pragma': 'no-cache'
        }
      });
      
      if (response.data.success) {
        setTrips(response.data.trips);
      }
    } catch (err) {
      console.error('Error fetching trips:', err);
      setError('Failed to load trips');
    }
  };

  const fetchActiveTrip = async () => {
    try {
      const token = sessionStorage.getItem('token');
      const response = await axios.get('http://localhost:8000/trip-budget/active-trip', {
        headers: { 
          Authorization: `Bearer ${token}`,
          'Cache-Control': 'no-cache',
          'Pragma': 'no-cache'
        }
      });
      
      if (response.data.success && response.data.active_trip) {
        setActiveTrip(response.data.active_trip);
      } else {
        setActiveTrip(null);
      }
    } catch (err) {
      console.error('Error fetching active trip:', err);
      setActiveTrip(null);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateTrip = async (e) => {
    e.preventDefault();
    try {
      const token = sessionStorage.getItem('token');
      const response = await axios.post('http://localhost:8000/trip-budget/create-trip', tripForm, {
        headers: { 
          Authorization: `Bearer ${token}`,
          'Cache-Control': 'no-cache',
          'Pragma': 'no-cache'
        }
      });
      
      if (response.data.success) {
        alert('Trip request created successfully! Waiting for manager approval.');
        setShowCreateTrip(false);
        setTripForm({ trip_purpose: '', destination_city: '', start_date: '', end_date: '' });
        fetchTrips();
      }
    } catch (err) {
      console.error('Error creating trip:', err);
      alert('Failed to create trip request: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleCalculateBudget = async (e) => {
    e.preventDefault();
    try {
      const token = sessionStorage.getItem('token');
      const response = await axios.get('http://localhost:8000/trip-budget/budget-calculator', {
        params: calculatorForm,
        headers: { 
          Authorization: `Bearer ${token}`,
          'Cache-Control': 'no-cache',
          'Pragma': 'no-cache'
        }
      });
      
      if (response.data.success) {
        setCalculatedBudget(response.data.calculation);
      }
    } catch (err) {
      console.error('Error calculating budget:', err);
      alert('Failed to calculate budget: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleActivateTrip = async (tripId) => {
    try {
      const token = sessionStorage.getItem('token');
      const response = await axios.post(`http://localhost:8000/trip-budget/activate-trip?trip_id=${tripId}`, {}, {
        headers: { 
          Authorization: `Bearer ${token}`,
          'Cache-Control': 'no-cache',
          'Pragma': 'no-cache'
        }
      });
      
      if (response.data.success) {
        alert('Trip activated! You can now submit expenses.');
        fetchActiveTrip();
        fetchTrips();
      }
    } catch (err) {
      console.error('Error activating trip:', err);
      alert('Failed to activate trip: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleCompleteTrip = async (tripId) => {
    const confirmComplete = window.confirm(
      'Are you sure you want to complete this trip? Once completed, you can submit it for manager approval.'
    );
    
    if (!confirmComplete) return;

    try {
      const token = sessionStorage.getItem('token');
      const response = await axios.post(`http://localhost:8000/trip-budget/complete-trip?trip_id=${tripId}`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (response.data.success) {
        alert('✅ Trip marked as completed! You can now submit it for manager approval.');
        fetchActiveTrip();
        fetchTrips();
      }
    } catch (err) {
      console.error('Error completing trip:', err);
      alert('Failed to complete trip: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleSubmitTripForApproval = async (tripId) => {
    const submissionNotes = prompt(
      'Add any notes for your manager (optional):\n\nThis will submit all bills from this trip for collective approval.'
    );
    
    // User cancelled the prompt
    if (submissionNotes === null) return;

    try {
      const token = sessionStorage.getItem('token');
      const response = await axios.post('http://localhost:8000/trip-budget/submit-trip', {
        trip_id: tripId,
        submission_notes: submissionNotes || ''
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (response.data.success) {
        alert(`🎉 ${response.data.message}\n\nYour manager will review all ${response.data.total_bills} bills together.`);
        fetchTrips();
      }
    } catch (err) {
      console.error('Error submitting trip for approval:', err);
      alert('Failed to submit trip for approval: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleSubmitJustification = async (tripId) => {
    const justification = justificationTexts[tripId];
    if (!justification || !justification.trim()) {
      alert('Please provide a justification');
      return;
    }

    try {
      const token = sessionStorage.getItem('token');
      const response = await axios.post('http://localhost:8000/trip-budget/submit-trip-justification', {
        trip_id: tripId,
        justification: justification
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (response.data.success) {
        alert('✅ Justification submitted successfully! The trip status has been updated to pending for manager review.');
        setJustificationTexts(prev => ({ ...prev, [tripId]: '' }));
        fetchTrips();
      }
    } catch (err) {
      console.error('Error submitting justification:', err);
      alert('Failed to submit justification: ' + (err.response?.data?.detail || err.message));
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

  const getStatusColor = (status) => {
    const colors = {
      pending: '#ffc107',
      approved: '#28a745',
      active: '#007bff',
      completed: '#6c757d',
      cancelled: '#dc3545',
      rejected: '#e74c3c'
    };
    return colors[status] || '#6c757d';
  };

  const getProgressPercentage = (used, allocated) => {
    if (!allocated || allocated === 0) return 0;
    return Math.min((used / allocated) * 100, 100);
  };

  const getProgressColor = (percentage) => {
    if (percentage >= 90) return '#dc3545';
    if (percentage >= 70) return '#ffc107';
    return '#28a745';
  };

  if (loading) {
    return (
      <div className="trip-budget-dashboard">
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>Loading trip information...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="trip-budget-dashboard">
      <div className="dashboard-header">
        <h1>🧳 Trip Budget Management</h1>
        <p>Manage your official company trips and expense budgets</p>
      </div>

      {/* Active Trip Section */}
      {activeTrip ? (
        <div className="active-trip-section">
          <h2>🔥 Active Trip</h2>
          <div className="active-trip-card">
            <div className="trip-header">
              <h3>Trip to {activeTrip.destination}</h3>
              <span className="trip-dates">
                {new Date(activeTrip.trip_start).toLocaleDateString()} - {new Date(activeTrip.trip_end).toLocaleDateString()}
              </span>
            </div>
            
            <div className="dashboard-budget-breakdown">
              {Object.entries(activeTrip.allocated_budgets).map(([expenseType, allocated]) => {
                const used = activeTrip.used_budgets[expenseType] || 0;
                const remaining = activeTrip.remaining_budgets[expenseType] || allocated;
                const percentage = getProgressPercentage(used, allocated);
                
                return (
                  <div key={expenseType} className="expense-item">
                    <div className="expense-header">
                      <span className="expense-type">{expenseType.replace('_', ' ').toUpperCase()}</span>
                      <span className="expense-amounts">
                        {formatCurrency(used)} / {formatCurrency(allocated)}
                      </span>
                    </div>
                    <div className="progress-bar">
                      <div 
                        className="progress-fill" 
                        style={{ 
                          width: `${percentage}%`,
                          backgroundColor: getProgressColor(percentage)
                        }}
                      ></div>
                    </div>
                    <div className="remaining-amount">
                      Remaining: <strong>{formatCurrency(remaining)}</strong>
                    </div>
                  </div>
                );
              })}
            </div>
            
            <div className="trip-actions">
              <button 
                onClick={() => window.location.href = '/upload'} 
                className="submit-expense-btn"
              >
                📤 Submit Expense
              </button>
              <button 
                onClick={() => handleCompleteTrip(activeTrip.trip_id)} 
                className="complete-trip-btn"
              >
                ✅ Complete Trip
              </button>
            </div>
          </div>
        </div>
      ) : (
        <div className="no-active-trip">
          <h2>📋 No Active Trip</h2>
          <p>You can only submit expenses during approved company trips. Create a trip request to get started.</p>
        </div>
      )}

      {/* Action Buttons */}
      <div className="action-buttons">
        <button 
          onClick={() => setShowCreateTrip(true)} 
          className="create-trip-btn"
        >
          ➕ Create Trip Request
        </button>
        <button 
          onClick={() => setShowBudgetCalculator(true)} 
          className="calculate-budget-btn"
        >
          🧮 Calculate Budget
        </button>
      </div>

      {/* All Trips Section */}
      <div className="all-trips-section">
        <h2>📋 All Trips</h2>
        {trips.length === 0 ? (
          <div className="no-trips">
            <p>No trips found. Create your first trip request!</p>
          </div>
        ) : (
          <div className="trips-grid">
            {trips.map((trip) => (
              <div key={trip.trip_id} className="trip-card">
                <div className="trip-card-header">
                  <h3>{trip.purpose}</h3>
                  <span 
                    className="status-badge" 
                    style={{ backgroundColor: getStatusColor(trip.status) }}
                  >
                    {trip.status.toUpperCase()}
                  </span>
                </div>
                
                <div className="trip-details">
                  <p><strong>Destination:</strong> {trip.destination} ({trip.destination_tier.replace('_', ' ')})</p>
                  <p><strong>Duration:</strong> {trip.duration_days} days</p>
                  <p><strong>Dates:</strong> {new Date(trip.start_date).toLocaleDateString()} - {new Date(trip.end_date).toLocaleDateString()}</p>
                  <p><strong>Total Budget:</strong> {formatCurrency(trip.total_allocated)}</p>
                  <p><strong>Expenses Submitted:</strong> {formatCurrency(trip.expenses_submitted)}</p>
                  <p><strong>Remaining:</strong> {formatCurrency(trip.remaining_budget)}</p>
                </div>
                
                <div className="trip-actions">
                  {trip.status === 'approved' && (
                    <button 
                      onClick={() => handleActivateTrip(trip.trip_id)} 
                      className="activate-btn"
                    >
                      🚀 Activate Trip
                    </button>
                  )}
                  {trip.status === 'active' && (
                    <button 
                      onClick={() => handleCompleteTrip(trip.trip_id)} 
                      className="complete-btn"
                    >
                      ✅ Complete
                    </button>
                  )}
                  {trip.status === 'completed' && (
                    <button 
                      onClick={() => handleSubmitTripForApproval(trip.trip_id)} 
                      className="submit-approval-btn"
                    >
                      📤 Submit for Approval
                    </button>
                  )}
                  {trip.status === 'pending' && (
                    <span className="status-info">⏳ Waiting for manager approval</span>
                  )}
                  {trip.status === 'rejected' && (
                    <div className="rejection-handling" style={{ width: '100%', marginTop: '15px' }}>
                      {trip.rejection_reason && (
                        <div className="rejection-reason" style={{ backgroundColor: '#fdeaea', color: '#e74c3c', padding: '10px', borderRadius: '8px', marginBottom: '10px', borderLeft: '4px solid #e74c3c' }}>
                          <strong>❌ Reason:</strong> {trip.rejection_reason}
                        </div>
                      )}
                      {trip.justification && (
                        <div className="justification-display" style={{ backgroundColor: '#e3f2fd', color: '#1976d2', padding: '10px', borderRadius: '8px', marginBottom: '10px', borderLeft: '4px solid #1976d2' }}>
                          <strong>📤 Your Justification:</strong> {trip.justification}
                        </div>
                      )}
                      <div className="justification-input" style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                        <textarea
                          placeholder="Provide justification or response to rejection..."
                          value={justificationTexts[trip.trip_id] || ''}
                          onChange={(e) => setJustificationTexts(prev => ({ ...prev, [trip.trip_id]: e.target.value }))}
                          style={{ padding: '10px', borderRadius: '8px', border: '1px solid #ddd', resize: 'vertical' }}
                          rows="2"
                        />
                        <button 
                          onClick={() => handleSubmitJustification(trip.trip_id)}
                          className="submit-justification-btn"
                          style={{ background: '#007bff', color: 'white', border: 'none', padding: '8px 15px', borderRadius: '6px', cursor: 'pointer', fontWeight: '600' }}
                        >
                          Submit Justification
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Create Trip Modal */}
      {showCreateTrip && (
        <div className="modal-overlay">
          <div className="modal">
            <div className="modal-header">
              <h3>Create Trip Request</h3>
              <button onClick={() => setShowCreateTrip(false)} className="close-btn">×</button>
            </div>
            <form onSubmit={handleCreateTrip} className="trip-form">
              <div className="form-group">
                <label>Trip Purpose</label>
                <input
                  type="text"
                  value={tripForm.trip_purpose}
                  onChange={(e) => setTripForm({...tripForm, trip_purpose: e.target.value})}
                  placeholder="e.g., Client meeting, Conference, Training"
                  required
                />
              </div>
              <div className="form-group">
                <label>Destination City</label>
                <input
                  type="text"
                  value={tripForm.destination_city}
                  onChange={(e) => setTripForm({...tripForm, destination_city: e.target.value})}
                  placeholder="e.g., Mumbai, Delhi, Bangalore"
                  required
                />
              </div>
              <div className="form-group">
                <label>Start Date</label>
                <input
                  type="date"
                  value={tripForm.start_date}
                  onChange={(e) => setTripForm({...tripForm, start_date: e.target.value})}
                  min={new Date().toISOString().split('T')[0]}
                  required
                />
              </div>
              <div className="form-group">
                <label>End Date</label>
                <input
                  type="date"
                  value={tripForm.end_date}
                  onChange={(e) => setTripForm({...tripForm, end_date: e.target.value})}
                  min={tripForm.start_date || new Date().toISOString().split('T')[0]}
                  required
                />
              </div>
              <div className="form-actions">
                <button type="button" onClick={() => setShowCreateTrip(false)} className="cancel-btn">
                  Cancel
                </button>
                <button type="submit" className="submit-btn">
                  Create Request
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Budget Calculator Modal */}
      {showBudgetCalculator && (
        <div className="modal-overlay">
          <div className="modal">
            <div className="modal-header">
              <h3>Budget Calculator</h3>
              <button onClick={() => setShowBudgetCalculator(false)} className="close-btn">×</button>
            </div>
            <form onSubmit={handleCalculateBudget} className="calculator-form">
              <div className="form-group">
                <label>Destination City</label>
                <input
                  type="text"
                  value={calculatorForm.destination_city}
                  onChange={(e) => setCalculatorForm({...calculatorForm, destination_city: e.target.value})}
                  placeholder="e.g., Mumbai, Delhi, Bangalore"
                  required
                />
              </div>
              <div className="form-group">
                <label>Start Date</label>
                <input
                  type="date"
                  value={calculatorForm.start_date}
                  onChange={(e) => setCalculatorForm({...calculatorForm, start_date: e.target.value})}
                  required
                />
              </div>
              <div className="form-group">
                <label>End Date</label>
                <input
                  type="date"
                  value={calculatorForm.end_date}
                  onChange={(e) => setCalculatorForm({...calculatorForm, end_date: e.target.value})}
                  min={calculatorForm.start_date}
                  required
                />
              </div>
              <div className="form-actions">
                <button type="submit" className="calculate-btn">
                  Calculate Budget
                </button>
              </div>
            </form>
            
            {calculatedBudget && (
              <div className="calculated-budget">
                <h4>💰 Estimated Budget</h4>
                <div className="budget-summary">
                  <p><strong>Destination:</strong> {calculatedBudget.destination_city} ({calculatedBudget.city_tier.replace('_', ' ')})</p>
                  <p><strong>Duration:</strong> {calculatedBudget.duration_days} days</p>
                  <p><strong>Designation:</strong> {calculatedBudget.designation.replace('_', ' ').toUpperCase()}</p>
                </div>
                <div className="dashboard-budget-breakdown">
                  {Object.entries(calculatedBudget.budget_breakdown).map(([type, amount]) => (
                    <div key={type} className="budget-item">
                      <span>{type.replace('_', ' ').toUpperCase()}</span>
                      <span>{formatCurrency(amount)}</span>
                    </div>
                  ))}
                </div>
                <div className="total-budget">
                  <strong>Total Budget: {formatCurrency(calculatedBudget.total_budget)}</strong>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      <style jsx>{`
        .trip-budget-dashboard {
          max-width: 1200px;
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

        .active-trip-section {
          margin-bottom: 30px;
        }

        .active-trip-card {
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
          padding: 25px;
          border-radius: 15px;
          box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }

        .trip-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 20px;
        }

        .trip-header h3 {
          margin: 0;
          font-size: 1.5em;
        }

        .trip-dates {
          background: rgba(255,255,255,0.2);
          padding: 5px 15px;
          border-radius: 20px;
          font-size: 0.9em;
        }

        .dashboard-budget-breakdown {
          margin-bottom: 20px;
        }

        .expense-item {
          margin-bottom: 15px;
        }

        .expense-header {
          display: flex;
          justify-content: space-between;
          margin-bottom: 5px;
        }

        .expense-type {
          font-weight: 600;
        }

        .expense-amounts {
          font-size: 0.9em;
        }

        .progress-bar {
          width: 100%;
          height: 8px;
          background-color: rgba(255,255,255,0.3);
          border-radius: 4px;
          overflow: hidden;
          margin-bottom: 5px;
        }

        .progress-fill {
          height: 100%;
          transition: width 0.3s ease;
        }

        .remaining-amount {
          font-size: 0.9em;
          text-align: right;
        }

        .trip-actions {
          display: flex;
          gap: 15px;
          justify-content: center;
        }

        .submit-expense-btn, .complete-trip-btn {
          padding: 12px 25px;
          border: none;
          border-radius: 8px;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s ease;
        }

        .submit-expense-btn {
          background: #28a745;
          color: white;
        }

        .complete-trip-btn {
          background: #ffc107;
          color: #212529;
        }

        .no-active-trip {
          text-align: center;
          padding: 40px;
          background: #f8f9fa;
          border-radius: 15px;
          margin-bottom: 30px;
          color: #2c3e50;
        }
        .no-active-trip h2 {
          color: #2c3e50;
        }
        .no-active-trip p {
          color: #6c757d;
        }

        .action-buttons {
          display: flex;
          gap: 15px;
          justify-content: center;
          margin-bottom: 30px;
        }

        .create-trip-btn, .calculate-budget-btn {
          padding: 15px 30px;
          border: none;
          border-radius: 8px;
          font-size: 1.1em;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s ease;
        }

        .create-trip-btn {
          background: #007bff;
          color: white;
        }

        .calculate-budget-btn {
          background: #17a2b8;
          color: white;
        }

        .trips-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
          gap: 20px;
        }

        .no-trips {
          text-align: center;
          padding: 40px;
          background: white;
          border-radius: 15px;
          color: #2c3e50;
        }

        .trip-card {
          background: white;
          border-radius: 15px;
          padding: 20px;
          box-shadow: 0 5px 15px rgba(0,0,0,0.1);
          border: 1px solid #e1e8ed;
        }

        .trip-card-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 15px;
        }

        .trip-card-header h3 {
          margin: 0;
          color: #2c3e50;
        }

        .status-badge {
          color: white;
          padding: 4px 12px;
          border-radius: 15px;
          font-size: 0.8em;
          font-weight: 600;
        }

        .trip-details p {
          margin: 8px 0;
          color: #6c757d;
        }

        .activate-btn, .complete-btn {
          padding: 8px 16px;
          border: none;
          border-radius: 6px;
          font-weight: 600;
          cursor: pointer;
          margin-top: 10px;
        }

        .activate-btn {
          background: #28a745;
          color: white;
        }

        .complete-btn {
          background: #ffc107;
          color: #212529;
        }

        .modal-overlay {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0,0,0,0.5);
          display: flex;
          justify-content: center;
          align-items: center;
          z-index: 1000;
        }

        .modal {
          background: white;
          border-radius: 15px;
          padding: 30px;
          max-width: 500px;
          width: 90%;
          max-height: 90vh;
          overflow-y: auto;
        }

        .modal-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 20px;
        }

        .close-btn {
          background: none;
          border: none;
          font-size: 24px;
          cursor: pointer;
          color: #6c757d;
        }

        .form-group {
          margin-bottom: 20px;
        }

        .form-group label {
          display: block;
          margin-bottom: 5px;
          font-weight: 600;
          color: #2c3e50;
        }

        .form-group input {
          width: 100%;
          padding: 12px;
          border: 2px solid #e1e8ed;
          border-radius: 8px;
          font-size: 1em;
          color: #2c3e50;
          background: white;
        }

        .form-actions {
          display: flex;
          gap: 15px;
          justify-content: flex-end;
        }

        .cancel-btn, .submit-btn, .calculate-btn {
          padding: 12px 25px;
          border: none;
          border-radius: 8px;
          font-weight: 600;
          cursor: pointer;
        }

        .cancel-btn {
          background: #6c757d;
          color: white;
        }

        .submit-btn, .calculate-btn {
          background: #007bff;
          color: white;
        }

        .calculated-budget {
          margin-top: 20px;
          padding: 20px;
          background: #f8f9fa;
          border-radius: 10px;
          color: #2c3e50;
        }
        
        .calculated-budget h4 {
          color: #2c3e50;
        }
        
        .calculated-budget .budget-summary p, 
        .calculated-budget .budget-item span,
        .calculated-budget .total-budget {
          color: #2c3e50;
        }

        .budget-item {
          display: flex;
          justify-content: space-between;
          padding: 8px 0;
          border-bottom: 1px solid #e1e8ed;
        }

        .total-budget {
          margin-top: 15px;
          padding-top: 15px;
          border-top: 2px solid #007bff;
          text-align: center;
          font-size: 1.2em;
          color: #007bff;
        }

        .loading-container {
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

        @media (max-width: 768px) {
          .trips-grid {
            grid-template-columns: 1fr;
          }
          
          .action-buttons {
            flex-direction: column;
            align-items: center;
          }
          
          .trip-actions {
            flex-direction: column;
            gap: 10px;
          }
        }
      `}</style>
    </div>
  );
};

export default TripBudgetDashboard;