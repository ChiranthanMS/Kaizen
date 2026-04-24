import React, { useState, useEffect } from 'react';
import './CompletedTripsEmployee.css';

const CompletedTripsEmployee = () => {
    const [completedTrips, setCompletedTrips] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [selectedTrip, setSelectedTrip] = useState(null);
    const [showDetails, setShowDetails] = useState(false);

    useEffect(() => {
        fetchCompletedTrips();
    }, []);

    const fetchCompletedTrips = async () => {
        try {
            setLoading(true);
            const token = localStorage.getItem('token');
            const response = await fetch('http://localhost:8000/trip-budget/completed-trips', {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                const data = await response.json();
                setCompletedTrips(data.completed_trips || []);
                setError('');
            } else {
                const errorData = await response.json();
                setError(errorData.detail || 'Failed to load completed trips');
            }
        } catch (err) {
            setError('Failed to load completed trips: ' + err.message);
        } finally {
            setLoading(false);
        }
    };

    const getStatusBadge = (submissionStatus) => {
        const statusConfig = {
            'not_submitted': { class: 'status-not-submitted', text: 'Not Submitted' },
            'submitted': { class: 'status-submitted', text: 'Pending Approval' },
            'approved': { class: 'status-approved', text: 'Approved' },
            'rejected': { class: 'status-rejected', text: 'Rejected' }
        };
        
        const config = statusConfig[submissionStatus] || { class: 'status-unknown', text: submissionStatus };
        return <span className={`status-badge ${config.class}`}>{config.text}</span>;
    };

    const formatCurrency = (amount) => {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD'
        }).format(amount || 0);
    };

    const formatDate = (dateString) => {
        if (!dateString) return 'N/A';
        return new Date(dateString).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    };

    const showTripDetails = (trip) => {
        setSelectedTrip(trip);
        setShowDetails(true);
    };

    const closeTripDetails = () => {
        setSelectedTrip(null);
        setShowDetails(false);
    };

    if (loading) {
        return (
            <div className="completed-trips-employee">
                <div className="loading-container">
                    <div className="loading-spinner"></div>
                    <p>Loading your completed trips...</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="completed-trips-employee">
                <div className="error-container">
                    <h3>❌ Error</h3>
                    <p>{error}</p>
                    <button onClick={fetchCompletedTrips} className="retry-button">
                        🔄 Retry
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="completed-trips-employee">
            <div className="header">
                <h2>📋 My Completed Trips</h2>
                <p>View your completed business trips and their approval status</p>
            </div>

            {completedTrips.length === 0 ? (
                <div className="no-trips">
                    <div className="no-trips-icon">✈️</div>
                    <h3>No Completed Trips</h3>
                    <p>You haven't completed any business trips yet.</p>
                    <p>Complete a trip to see it here with bills and approval status.</p>
                </div>
            ) : (
                <div className="trips-grid">
                    {completedTrips.map((trip) => (
                        <div key={trip.trip_id} className="trip-card">
                            <div className="trip-header">
                                <h3>{trip.trip_purpose}</h3>
                                {getStatusBadge(trip.submission_status)}
                            </div>
                            
                            <div className="trip-info">
                                <div className="info-row">
                                    <span className="label">📍 Destination:</span>
                                    <span className="value">{trip.destination_city}</span>
                                </div>
                                
                                <div className="info-row">
                                    <span className="label">📅 Duration:</span>
                                    <span className="value">
                                        {formatDate(trip.start_date)} - {formatDate(trip.end_date)}
                                        ({trip.duration_days} days)
                                    </span>
                                </div>
                                
                                <div className="info-row">
                                    <span className="label">💰 Budget:</span>
                                    <span className="value">{formatCurrency(trip.allocated_budget)}</span>
                                </div>
                                
                                <div className="info-row">
                                    <span className="label">🧾 Expenses:</span>
                                    <span className="value">
                                        {formatCurrency(trip.actual_total_amount)} 
                                        ({trip.actual_bills_count} bills)
                                    </span>
                                </div>
                                
                                <div className="info-row">
                                    <span className="label">📊 Utilization:</span>
                                    <span className="value">{trip.budget_utilization.toFixed(1)}%</span>
                                </div>
                                
                                <div className="info-row">
                                    <span className="label">✅ Completed:</span>
                                    <span className="value">{formatDate(trip.completed_at)}</span>
                                </div>
                                
                                {trip.submitted_at && (
                                    <div className="info-row">
                                        <span className="label">📤 Submitted:</span>
                                        <span className="value">{formatDate(trip.submitted_at)}</span>
                                    </div>
                                )}
                                
                                {trip.approved_at && (
                                    <div className="info-row">
                                        <span className="label">✅ Approved:</span>
                                        <span className="value">{formatDate(trip.approved_at)}</span>
                                    </div>
                                )}
                            </div>
                            
                            <div className="trip-actions">
                                <button 
                                    onClick={() => showTripDetails(trip)}
                                    className="details-button"
                                >
                                    👁️ View Details
                                </button>
                            </div>
                            
                            {trip.approval_comments && (
                                <div className="approval-comments">
                                    <strong>💬 Manager Comments:</strong>
                                    <p>{trip.approval_comments}</p>
                                </div>
                            )}
                            
                            {trip.rejection_reason && (
                                <div className="rejection-reason">
                                    <strong>❌ Rejection Reason:</strong>
                                    <p>{trip.rejection_reason}</p>
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            )}

            {/* Trip Details Modal */}
            {showDetails && selectedTrip && (
                <div className="modal-overlay" onClick={closeTripDetails}>
                    <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                        <div className="modal-header">
                            <h3>🔍 Trip Details</h3>
                            <button onClick={closeTripDetails} className="close-button">✕</button>
                        </div>
                        
                        <div className="modal-body">
                            <div className="detail-section">
                                <h4>📋 Trip Information</h4>
                                <div className="detail-grid">
                                    <div className="detail-item">
                                        <label>Purpose:</label>
                                        <span>{selectedTrip.trip_purpose}</span>
                                    </div>
                                    <div className="detail-item">
                                        <label>Destination:</label>
                                        <span>{selectedTrip.destination_city}</span>
                                    </div>
                                    <div className="detail-item">
                                        <label>Designation:</label>
                                        <span>{selectedTrip.designation}</span>
                                    </div>
                                    <div className="detail-item">
                                        <label>City Tier:</label>
                                        <span>{selectedTrip.city_tier}</span>
                                    </div>
                                    <div className="detail-item">
                                        <label>Duration:</label>
                                        <span>{selectedTrip.duration_days} days</span>
                                    </div>
                                    <div className="detail-item">
                                        <label>Status:</label>
                                        {getStatusBadge(selectedTrip.submission_status)}
                                    </div>
                                </div>
                            </div>
                            
                            <div className="detail-section">
                                <h4>💰 Financial Summary</h4>
                                <div className="financial-summary">
                                    <div className="financial-item">
                                        <label>Allocated Budget:</label>
                                        <span className="amount">{formatCurrency(selectedTrip.allocated_budget)}</span>
                                    </div>
                                    <div className="financial-item">
                                        <label>Total Expenses:</label>
                                        <span className="amount">{formatCurrency(selectedTrip.actual_total_amount)}</span>
                                    </div>
                                    <div className="financial-item">
                                        <label>Budget Utilization:</label>
                                        <span className="percentage">{selectedTrip.budget_utilization.toFixed(1)}%</span>
                                    </div>
                                    <div className="financial-item">
                                        <label>Number of Bills:</label>
                                        <span>{selectedTrip.actual_bills_count}</span>
                                    </div>
                                </div>
                            </div>
                            
                            <div className="detail-section">
                                <h4>📅 Timeline</h4>
                                <div className="timeline">
                                    <div className="timeline-item">
                                        <span className="timeline-label">Completed:</span>
                                        <span>{formatDate(selectedTrip.completed_at)}</span>
                                    </div>
                                    {selectedTrip.submitted_at && (
                                        <div className="timeline-item">
                                            <span className="timeline-label">Submitted:</span>
                                            <span>{formatDate(selectedTrip.submitted_at)}</span>
                                        </div>
                                    )}
                                    {selectedTrip.approved_at && (
                                        <div className="timeline-item">
                                            <span className="timeline-label">Approved:</span>
                                            <span>{formatDate(selectedTrip.approved_at)}</span>
                                        </div>
                                    )}
                                </div>
                            </div>
                            
                            {selectedTrip.approval_comments && (
                                <div className="detail-section">
                                    <h4>💬 Manager Comments</h4>
                                    <div className="comments-box">
                                        {selectedTrip.approval_comments}
                                    </div>
                                </div>
                            )}
                            
                            {selectedTrip.rejection_reason && (
                                <div className="detail-section">
                                    <h4>❌ Rejection Reason</h4>
                                    <div className="rejection-box">
                                        {selectedTrip.rejection_reason}
                                    </div>
                                </div>
                            )}
                        </div>
                        
                        <div className="modal-footer">
                            <button onClick={closeTripDetails} className="close-modal-button">
                                Close
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default CompletedTripsEmployee;