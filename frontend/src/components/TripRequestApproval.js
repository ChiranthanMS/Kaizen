import React, { useState, useEffect } from 'react';
import './TripRequestApproval.css';

const TripRequestApproval = () => {
    const [pendingRequests, setPendingRequests] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [processingId, setProcessingId] = useState(null);
    const [showApprovalModal, setShowApprovalModal] = useState(false);
    const [showRejectionModal, setShowRejectionModal] = useState(false);
    const [selectedRequest, setSelectedRequest] = useState(null);
    const [budgetAdjustments, setBudgetAdjustments] = useState({});
    const [rejectionReason, setRejectionReason] = useState('');

    useEffect(() => {
        fetchPendingRequests();
    }, []);

    const fetchPendingRequests = async () => {
        try {
            setLoading(true);
            const token = sessionStorage.getItem('token');
            const response = await fetch('http://localhost:8000/trip-budget/pending-requests', {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                    'Cache-Control': 'no-cache',
                    'Pragma': 'no-cache'
                }
            });

            if (response.ok) {
                const data = await response.json();
                setPendingRequests(data.pending_requests || []);
                setError('');
            } else {
                throw new Error('Failed to fetch pending trip requests');
            }
        } catch (err) {
            console.error('Error fetching pending requests:', err);
            setError('Failed to load pending trip requests');
        } finally {
            setLoading(false);
        }
    };

    const handleApprove = async () => {
        if (!selectedRequest) return;

        try {
            setProcessingId(selectedRequest.trip_id);
            const token = sessionStorage.getItem('token');
            
            const response = await fetch('http://localhost:8000/trip-budget/approve-trip', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    trip_id: selectedRequest.trip_id,
                    budget_adjustments: Object.keys(budgetAdjustments).length > 0 ? budgetAdjustments : null
                })
            });

            if (response.ok) {
                await fetchPendingRequests(); // Refresh the list
                setShowApprovalModal(false);
                setBudgetAdjustments({});
                setSelectedRequest(null);
            } else {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to approve trip request');
            }
        } catch (err) {
            console.error('Error approving request:', err);
            setError(`Failed to approve trip request: ${err.message}`);
        } finally {
            setProcessingId(null);
        }
    };

    const handleReject = async () => {
        if (!selectedRequest || !rejectionReason.trim()) return;

        try {
            setProcessingId(selectedRequest.trip_id);
            const token = sessionStorage.getItem('token');
            
            const response = await fetch('http://localhost:8000/trip-budget/reject-trip', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    trip_id: selectedRequest.trip_id,
                    reason: rejectionReason
                })
            });

            if (response.ok) {
                await fetchPendingRequests(); // Refresh the list
                setShowRejectionModal(false);
                setRejectionReason('');
                setSelectedRequest(null);
            } else {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to reject trip request');
            }
        } catch (err) {
            console.error('Error rejecting request:', err);
            setError(`Failed to reject trip request: ${err.message}`);
        } finally {
            setProcessingId(null);
        }
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

    const openApprovalModal = (request) => {
        setSelectedRequest(request);
        // Initialize budget adjustments with current values
        setBudgetAdjustments(request.allocated_budget || {});
        setShowApprovalModal(true);
    };

    const openRejectionModal = (request) => {
        setSelectedRequest(request);
        setShowRejectionModal(true);
    };

    const updateBudgetAdjustment = (category, value) => {
        setBudgetAdjustments(prev => ({
            ...prev,
            [category]: parseFloat(value) || 0
        }));
    };

    if (loading) {
        return (
            <div className="trip-request-approval">
                <div className="loading-container">
                    <div className="loading-spinner"></div>
                    <h3>Loading Trip Requests...</h3>
                </div>
            </div>
        );
    }

    return (
        <div className="trip-request-approval">
            <div className="approval-header">
                <h2>🎯 Trip Request Approval</h2>
                <p>Review and approve employee trip planning requests</p>
                <div className="approval-stats">
                    <span className="stat-badge">
                        {pendingRequests.length} Pending Requests
                    </span>
                </div>
            </div>

            {error && (
                <div className="error-banner">
                    <span className="error-icon">⚠️</span>
                    <span className="error-message">{error}</span>
                    <button 
                        className="error-close"
                        onClick={() => setError('')}
                    >
                        ✕
                    </button>
                </div>
            )}

            {pendingRequests.length === 0 ? (
                <div className="empty-requests">
                    <div className="empty-icon">📋</div>
                    <h3>No Pending Trip Requests</h3>
                    <p>All trip requests have been processed.</p>
                    <button 
                        className="btn btn-primary"
                        onClick={fetchPendingRequests}
                    >
                        🔄 Refresh
                    </button>
                </div>
            ) : (
                <div className="requests-grid">
                    {pendingRequests.map((request) => (
                        <div key={request.trip_id} className="request-card">
                            <div className="request-header">
                                <div className="request-info">
                                    <h3>{request.employee_name}</h3>
                                    <p className="trip-id">Trip ID: {request.trip_id}</p>
                                    <p className="designation">{request.designation}</p>
                                </div>
                                <div className="request-status">
                                    <span className="status-badge pending">
                                        Pending Approval
                                    </span>
                                </div>
                            </div>

                            <div className="request-details">
                                <div className="detail-row">
                                    <span className="detail-label">🎯 Purpose:</span>
                                    <span className="detail-value">{request.purpose}</span>
                                </div>
                                <div className="detail-row">
                                    <span className="detail-label">📍 Destination:</span>
                                    <span className="detail-value">
                                        {request.destination} ({request.destination_tier})
                                    </span>
                                </div>
                                <div className="detail-row">
                                    <span className="detail-label">📅 Duration:</span>
                                    <span className="detail-value">
                                        {formatDate(request.start_date)} - {formatDate(request.end_date)}
                                        ({request.duration_days} days)
                                    </span>
                                </div>
                                <div className="detail-row">
                                    <span className="detail-label">💰 Total Budget:</span>
                                    <span className="detail-value budget-amount">
                                        {formatCurrency(request.total_allocated)}
                                    </span>
                                </div>
                                <div className="detail-row">
                                    <span className="detail-label">📤 Requested:</span>
                                    <span className="detail-value">
                                        {formatDate(request.created_at)}
                                    </span>
                                </div>
                                {request.rejection_reason && (
                                    <div className="detail-row rejection-info">
                                        <span className="detail-label">❌ Prev Reason:</span>
                                        <span className="detail-value">{request.rejection_reason}</span>
                                    </div>
                                )}
                                {request.justification && (
                                    <div className="detail-row justification-info">
                                        <span className="detail-label">📤 Justification:</span>
                                        <span className="detail-value">{request.justification}</span>
                                    </div>
                                )}
                            </div>

                            <div className="budget-breakdown">
                                <h4>Budget Breakdown:</h4>
                                <div className="budget-items">
                                    {Object.entries(request.allocated_budget || {}).map(([category, amount]) => (
                                        <div key={category} className="budget-item">
                                            <span className="budget-category">{category}:</span>
                                            <span className="budget-amount">{formatCurrency(amount)}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            <div className="request-actions">
                                <button 
                                    className="btn btn-success"
                                    onClick={() => openApprovalModal(request)}
                                    disabled={processingId === request.trip_id}
                                >
                                    {processingId === request.trip_id ? '⏳' : '✅'} Approve
                                </button>
                                <button 
                                    className="btn btn-danger"
                                    onClick={() => openRejectionModal(request)}
                                    disabled={processingId === request.trip_id}
                                >
                                    {processingId === request.trip_id ? '⏳' : '❌'} Reject
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {/* Approval Modal */}
            {showApprovalModal && (
                <div className="modal-overlay">
                    <div className="modal-content large-modal">
                        <div className="modal-header">
                            <h3>✅ Approve Trip Request</h3>
                            <button 
                                className="modal-close"
                                onClick={() => setShowApprovalModal(false)}
                            >
                                ✕
                            </button>
                        </div>
                        <div className="modal-body">
                            <p>
                                Approve trip request for <strong>{selectedRequest?.employee_name}</strong> 
                                to <strong>{selectedRequest?.destination}</strong>?
                            </p>
                            
                            <div className="budget-adjustment-section">
                                <h4>Budget Adjustments (Optional):</h4>
                                <p className="adjustment-note">
                                    You can adjust the budget allocations if needed. Leave unchanged to approve with original amounts.
                                </p>
                                
                                <div className="budget-adjustments">
                                    {Object.entries(selectedRequest?.allocated_budget || {}).map(([category, originalAmount]) => (
                                        <div key={category} className="adjustment-row">
                                            <label>{category}:</label>
                                            <div className="adjustment-input">
                                                <span className="currency-symbol">$</span>
                                                <input
                                                    type="number"
                                                    step="0.01"
                                                    min="0"
                                                    value={budgetAdjustments[category] || originalAmount}
                                                    onChange={(e) => updateBudgetAdjustment(category, e.target.value)}
                                                />
                                                <span className="original-amount">
                                                    (Original: {formatCurrency(originalAmount)})
                                                </span>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                                
                                <div className="total-budget">
                                    <strong>
                                        Total Adjusted Budget: {formatCurrency(
                                            Object.values(budgetAdjustments).reduce((sum, amount) => sum + (parseFloat(amount) || 0), 0)
                                        )}
                                    </strong>
                                </div>
                            </div>
                        </div>
                        <div className="modal-actions">
                            <button 
                                className="btn btn-secondary"
                                onClick={() => setShowApprovalModal(false)}
                            >
                                Cancel
                            </button>
                            <button 
                                className="btn btn-success"
                                onClick={handleApprove}
                                disabled={processingId}
                            >
                                {processingId ? '⏳ Processing...' : '✅ Approve Trip'}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Rejection Modal */}
            {showRejectionModal && (
                <div className="modal-overlay">
                    <div className="modal-content">
                        <div className="modal-header">
                            <h3>❌ Reject Trip Request</h3>
                            <button 
                                className="modal-close"
                                onClick={() => setShowRejectionModal(false)}
                            >
                                ✕
                            </button>
                        </div>
                        <div className="modal-body">
                            <p>
                                Please provide a reason for rejecting the trip request for{' '}
                                <strong>{selectedRequest?.employee_name}</strong>:
                            </p>
                            <div className="form-group">
                                <label>Rejection Reason (Required):</label>
                                <textarea
                                    value={rejectionReason}
                                    onChange={(e) => setRejectionReason(e.target.value)}
                                    placeholder="Please explain why this trip request is being rejected..."
                                    rows="4"
                                    required
                                />
                            </div>
                        </div>
                        <div className="modal-actions">
                            <button 
                                className="btn btn-secondary"
                                onClick={() => setShowRejectionModal(false)}
                            >
                                Cancel
                            </button>
                            <button 
                                className="btn btn-danger"
                                onClick={handleReject}
                                disabled={processingId || !rejectionReason.trim()}
                            >
                                {processingId ? '⏳ Processing...' : '❌ Reject Trip'}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default TripRequestApproval;