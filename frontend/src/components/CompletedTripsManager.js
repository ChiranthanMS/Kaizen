import React, { useState, useEffect } from 'react';
import './CompletedTripsManager.css';

const CompletedTripsManager = () => {
    const [completedTrips, setCompletedTrips] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [selectedTrip, setSelectedTrip] = useState(null);
    const [showDetails, setShowDetails] = useState(false);
    const [filterStatus, setFilterStatus] = useState('all');
    const [searchTerm, setSearchTerm] = useState('');

    useEffect(() => {
        fetchCompletedTrips();
    }, []);

    const fetchCompletedTrips = async () => {
        try {
            setLoading(true);
            const token = sessionStorage.getItem('token');
            const response = await fetch('http://localhost:8000/trip-budget/manager/completed-trips', {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                    'Cache-Control': 'no-cache',
                    'Pragma': 'no-cache'
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
        return new Intl.NumberFormat('en-IN', {
            style: 'currency',
            currency: 'INR'
        }).format(amount || 0);
    };

    const formatDate = (dateString) => {
        if (!dateString) return 'N/A';
        return new Date(dateString).toLocaleDateString('en-IN', {
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

    // Filter trips based on status and search term
    const filteredTrips = completedTrips.filter(trip => {
        const matchesStatus = filterStatus === 'all' || trip.submission_status === filterStatus;
        const matchesSearch = trip.employee_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                             trip.trip_purpose.toLowerCase().includes(searchTerm.toLowerCase()) ||
                             trip.destination_city.toLowerCase().includes(searchTerm.toLowerCase());
        return matchesStatus && matchesSearch;
    });

    // Calculate summary statistics
    const totalTrips = completedTrips.length;
    const approvedTrips = completedTrips.filter(t => t.submission_status === 'approved').length;
    const pendingTrips = completedTrips.filter(t => t.submission_status === 'submitted').length;
    const totalAmount = completedTrips.reduce((sum, trip) => sum + (trip.actual_total_amount || 0), 0);

    if (loading) {
        return (
            <div className="completed-trips-manager">
                <div className="loading-container">
                    <div className="loading-spinner"></div>
                    <p>Loading completed trips...</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="completed-trips-manager">
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
        <div className="completed-trips-manager">
            <div className="header">
                <h2>📊 Team Completed Trips</h2>
                <p>Monitor and review completed business trips from your team</p>
            </div>

            {/* Summary Statistics */}
            <div className="summary-stats">
                <div className="stat-card">
                    <div className="stat-number">{totalTrips}</div>
                    <div className="stat-label">Total Trips</div>
                </div>
                <div className="stat-card approved">
                    <div className="stat-number">{approvedTrips}</div>
                    <div className="stat-label">Approved</div>
                </div>
                <div className="stat-card pending">
                    <div className="stat-number">{pendingTrips}</div>
                    <div className="stat-label">Pending</div>
                </div>
                <div className="stat-card amount">
                    <div className="stat-number">{formatCurrency(totalAmount)}</div>
                    <div className="stat-label">Total Expenses</div>
                </div>
            </div>

            {/* Filters and Search */}
            <div className="filters-section">
                <div className="search-box">
                    <input
                        type="text"
                        placeholder="🔍 Search by employee, purpose, or destination..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="search-input"
                    />
                </div>
                
                <div className="status-filters">
                    <button 
                        className={`filter-button ${filterStatus === 'all' ? 'active' : ''}`}
                        onClick={() => setFilterStatus('all')}
                    >
                        All ({completedTrips.length})
                    </button>
                    <button 
                        className={`filter-button ${filterStatus === 'approved' ? 'active' : ''}`}
                        onClick={() => setFilterStatus('approved')}
                    >
                        Approved ({approvedTrips})
                    </button>
                    <button 
                        className={`filter-button ${filterStatus === 'submitted' ? 'active' : ''}`}
                        onClick={() => setFilterStatus('submitted')}
                    >
                        Pending ({pendingTrips})
                    </button>
                    <button 
                        className={`filter-button ${filterStatus === 'not_submitted' ? 'active' : ''}`}
                        onClick={() => setFilterStatus('not_submitted')}
                    >
                        Not Submitted ({completedTrips.filter(t => t.submission_status === 'not_submitted').length})
                    </button>
                </div>
            </div>

            {filteredTrips.length === 0 ? (
                <div className="no-trips">
                    <div className="no-trips-icon">📋</div>
                    <h3>No Trips Found</h3>
                    <p>
                        {searchTerm || filterStatus !== 'all' 
                            ? 'No trips match your current filters.' 
                            : 'No completed trips available yet.'
                        }
                    </p>
                    {(searchTerm || filterStatus !== 'all') && (
                        <button 
                            onClick={() => { setSearchTerm(''); setFilterStatus('all'); }}
                            className="clear-filters-button"
                        >
                            Clear Filters
                        </button>
                    )}
                </div>
            ) : (
                <div className="trips-table-container">
                    <table className="trips-table">
                        <thead>
                            <tr>
                                <th>Employee</th>
                                <th>Purpose</th>
                                <th>Destination</th>
                                <th>Duration</th>
                                <th>Budget</th>
                                <th>Expenses</th>
                                <th>Utilization</th>
                                <th>Status</th>
                                <th>Completed</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {filteredTrips.map((trip) => (
                                <tr key={trip.trip_id} className="trip-row">
                                    <td className="employee-cell">
                                        <div className="employee-info">
                                            <strong>{trip.employee_name}</strong>
                                            <small>{trip.designation}</small>
                                        </div>
                                    </td>
                                    <td className="purpose-cell">
                                        <div className="purpose-text" title={trip.trip_purpose}>
                                            {trip.trip_purpose.length > 30 
                                                ? trip.trip_purpose.substring(0, 30) + '...' 
                                                : trip.trip_purpose
                                            }
                                        </div>
                                    </td>
                                    <td>{trip.destination_city}</td>
                                    <td>{trip.duration_days} days</td>
                                    <td className="amount-cell">{formatCurrency(trip.allocated_budget)}</td>
                                    <td className="amount-cell">
                                        <div>
                                            {formatCurrency(trip.actual_total_amount)}
                                            <small>({trip.actual_bills_count} bills)</small>
                                        </div>
                                    </td>
                                    <td className="utilization-cell">
                                        <div className="utilization-bar">
                                            <div 
                                                className="utilization-fill"
                                                style={{ 
                                                    width: `${Math.min(trip.budget_utilization, 100)}%`,
                                                    backgroundColor: trip.budget_utilization > 100 ? '#e74c3c' : 
                                                                   trip.budget_utilization > 80 ? '#f39c12' : '#27ae60'
                                                }}
                                            ></div>
                                            <span className="utilization-text">
                                                {trip.budget_utilization.toFixed(1)}%
                                            </span>
                                        </div>
                                    </td>
                                    <td>{getStatusBadge(trip.submission_status)}</td>
                                    <td>{formatDate(trip.completed_at)}</td>
                                    <td>
                                        <button 
                                            onClick={() => showTripDetails(trip)}
                                            className="view-details-button"
                                            title="View trip details"
                                        >
                                            👁️
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}

            {/* Trip Details Modal */}
            {showDetails && selectedTrip && (
                <div className="modal-overlay" onClick={closeTripDetails}>
                    <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                        <div className="modal-header">
                            <h3>🔍 Trip Details - {selectedTrip.employee_name}</h3>
                            <button onClick={closeTripDetails} className="close-button">✕</button>
                        </div>
                        
                        <div className="modal-body">
                            <div className="detail-section">
                                <h4>👤 Employee Information</h4>
                                <div className="detail-grid">
                                    <div className="detail-item">
                                        <label>Employee:</label>
                                        <span>{selectedTrip.employee_name}</span>
                                    </div>
                                    <div className="detail-item">
                                        <label>Designation:</label>
                                        <span>{selectedTrip.designation}</span>
                                    </div>
                                    <div className="detail-item">
                                        <label>City Tier:</label>
                                        <span>{selectedTrip.city_tier}</span>
                                    </div>
                                </div>
                            </div>
                            
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
                                        <label>Start Date:</label>
                                        <span>{formatDate(selectedTrip.start_date)}</span>
                                    </div>
                                    <div className="detail-item">
                                        <label>End Date:</label>
                                        <span>{formatDate(selectedTrip.end_date)}</span>
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
                                        <span className={`percentage ${selectedTrip.budget_utilization > 100 ? 'over-budget' : ''}`}>
                                            {selectedTrip.budget_utilization.toFixed(1)}%
                                        </span>
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

export default CompletedTripsManager;