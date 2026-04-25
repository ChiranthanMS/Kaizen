import React, { useState, useEffect } from 'react';
import './TripApprovalManager.css';

const TripApprovalManager = () => {
    const [pendingSubmissions, setPendingSubmissions] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [processingId, setProcessingId] = useState(null);
    const [showApprovalModal, setShowApprovalModal] = useState(false);
    const [showRejectionModal, setShowRejectionModal] = useState(false);
    const [selectedSubmission, setSelectedSubmission] = useState(null);
    const [approvalComments, setApprovalComments] = useState('');
    const [rejectionReason, setRejectionReason] = useState('');

    useEffect(() => {
        fetchPendingSubmissions();
    }, []);

    const fetchPendingSubmissions = async () => {
        try {
            setLoading(true);
            const token = sessionStorage.getItem('token');
            const response = await fetch('http://localhost:8000/trip-budget/pending-trip-submissions', {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                    'Cache-Control': 'no-cache',
                    'Pragma': 'no-cache'
                }
            });

            if (response.ok) {
                const data = await response.json();
                setPendingSubmissions(data.pending_submissions || []);
                setError('');
            } else {
                throw new Error('Failed to fetch pending submissions');
            }
        } catch (err) {
            console.error('Error fetching pending submissions:', err);
            setError('Failed to load pending submissions');
        } finally {
            setLoading(false);
        }
    };

    const handleApprove = async () => {
        if (!selectedSubmission) return;

        try {
            setProcessingId(selectedSubmission.submission_id);
            const token = sessionStorage.getItem('token');
            
            const response = await fetch('http://localhost:8000/trip-budget/approve-trip-submission', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    submission_id: selectedSubmission.submission_id,
                    comments: approvalComments || 'Approved by manager'
                })
            });

            if (response.ok) {
                await fetchPendingSubmissions(); // Refresh the list
                setShowApprovalModal(false);
                setApprovalComments('');
                setSelectedSubmission(null);
            } else {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to approve submission');
            }
        } catch (err) {
            console.error('Error approving submission:', err);
            setError(`Failed to approve submission: ${err.message}`);
        } finally {
            setProcessingId(null);
        }
    };

    const handleReject = async () => {
        if (!selectedSubmission || !rejectionReason.trim()) return;

        try {
            setProcessingId(selectedSubmission.submission_id);
            const token = sessionStorage.getItem('token');
            
            const response = await fetch('http://localhost:8000/trip-budget/reject-trip-submission', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    submission_id: selectedSubmission.submission_id,
                    reason: rejectionReason
                })
            });

            if (response.ok) {
                await fetchPendingSubmissions(); // Refresh the list
                setShowRejectionModal(false);
                setRejectionReason('');
                setSelectedSubmission(null);
            } else {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to reject submission');
            }
        } catch (err) {
            console.error('Error rejecting submission:', err);
            setError(`Failed to reject submission: ${err.message}`);
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

    const openApprovalModal = (submission) => {
        setSelectedSubmission(submission);
        setShowApprovalModal(true);
    };

    const openRejectionModal = (submission) => {
        setSelectedSubmission(submission);
        setShowRejectionModal(true);
    };

    if (loading) {
        return (
            <div className="trip-approval-manager">
                <div className="loading-container">
                    <div className="loading-spinner"></div>
                    <h3>Loading Trip Submissions...</h3>
                </div>
            </div>
        );
    }

    return (
        <div className="trip-approval-manager">
            <div className="approval-header">
                <h2>🎯 Trip Approval Center</h2>
                <p>Review and approve employee trip submissions</p>
                <div className="approval-stats">
                    <span className="stat-badge">
                        {pendingSubmissions.length} Pending Submissions
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

            {pendingSubmissions.length === 0 ? (
                <div className="empty-submissions">
                    <div className="empty-icon">📋</div>
                    <h3>No Pending Submissions</h3>
                    <p>All trip submissions have been processed.</p>
                    <button 
                        className="btn btn-primary"
                        onClick={fetchPendingSubmissions}
                    >
                        🔄 Refresh
                    </button>
                </div>
            ) : (
                <div className="submissions-grid">
                    {pendingSubmissions.map((submission) => (
                        <div key={submission.submission_id} className="submission-card">
                            <div className="submission-header">
                                <div className="submission-info">
                                    <h3>{submission.employee_name}</h3>
                                    <p className="trip-id">Trip ID: {submission.trip_id}</p>
                                </div>
                                <div className="submission-status">
                                    <span className="status-badge pending">
                                        Pending Review
                                    </span>
                                </div>
                            </div>

                            <div className="submission-details">
                                <div className="detail-row">
                                    <span className="detail-label">🎯 Purpose:</span>
                                    <span className="detail-value">{submission.trip_purpose}</span>
                                </div>
                                <div className="detail-row">
                                    <span className="detail-label">📍 Destination:</span>
                                    <span className="detail-value">{submission.destination_city}</span>
                                </div>
                                <div className="detail-row">
                                    <span className="detail-label">📅 Duration:</span>
                                    <span className="detail-value">
                                        {formatDate(submission.start_date)} - {formatDate(submission.end_date)}
                                        ({submission.duration_days} days)
                                    </span>
                                </div>
                                <div className="detail-row">
                                    <span className="detail-label">💰 Budget:</span>
                                    <span className="detail-value">
                                        {formatCurrency(submission.allocated_budget)}
                                    </span>
                                </div>
                                <div className="detail-row">
                                    <span className="detail-label">📄 Bills:</span>
                                    <span className="detail-value">
                                        {submission.actual_bills_count || submission.total_bills || 0} bills
                                    </span>
                                </div>
                                <div className="detail-row">
                                    <span className="detail-label">💵 Total Amount:</span>
                                    <span className="detail-value expense-amount">
                                        {formatCurrency(submission.actual_total_amount || submission.total_amount)}
                                    </span>
                                </div>
                                <div className="detail-row">
                                    <span className="detail-label">📊 Utilization:</span>
                                    <span className="detail-value">
                                        {submission.budget_utilization ? 
                                            `${submission.budget_utilization.toFixed(1)}%` : 
                                            'N/A'
                                        }
                                    </span>
                                </div>
                                <div className="detail-row">
                                    <span className="detail-label">📤 Submitted:</span>
                                    <span className="detail-value">
                                        {formatDate(submission.submitted_at)}
                                    </span>
                                </div>
                            </div>

                            <div className="submission-actions">
                                <button 
                                    className="btn btn-success"
                                    onClick={() => openApprovalModal(submission)}
                                    disabled={processingId === submission.submission_id}
                                >
                                    {processingId === submission.submission_id ? '⏳' : '✅'} Approve
                                </button>
                                <button 
                                    className="btn btn-danger"
                                    onClick={() => openRejectionModal(submission)}
                                    disabled={processingId === submission.submission_id}
                                >
                                    {processingId === submission.submission_id ? '⏳' : '❌'} Reject
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {/* Approval Modal */}
            {showApprovalModal && (
                <div className="modal-overlay">
                    <div className="modal-content">
                        <div className="modal-header">
                            <h3>✅ Approve Trip Submission</h3>
                            <button 
                                className="modal-close"
                                onClick={() => setShowApprovalModal(false)}
                            >
                                ✕
                            </button>
                        </div>
                        <div className="modal-body">
                            <p>
                                Are you sure you want to approve the trip submission for{' '}
                                <strong>{selectedSubmission?.employee_name}</strong>?
                            </p>
                            <div className="form-group">
                                <label>Approval Comments (Optional):</label>
                                <textarea
                                    value={approvalComments}
                                    onChange={(e) => setApprovalComments(e.target.value)}
                                    placeholder="Add any comments for the employee..."
                                    rows="3"
                                />
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
                                {processingId ? '⏳ Processing...' : '✅ Approve'}
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
                            <h3>❌ Reject Trip Submission</h3>
                            <button 
                                className="modal-close"
                                onClick={() => setShowRejectionModal(false)}
                            >
                                ✕
                            </button>
                        </div>
                        <div className="modal-body">
                            <p>
                                Please provide a reason for rejecting the trip submission for{' '}
                                <strong>{selectedSubmission?.employee_name}</strong>:
                            </p>
                            <div className="form-group">
                                <label>Rejection Reason (Required):</label>
                                <textarea
                                    value={rejectionReason}
                                    onChange={(e) => setRejectionReason(e.target.value)}
                                    placeholder="Please explain why this submission is being rejected..."
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
                                {processingId ? '⏳ Processing...' : '❌ Reject'}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default TripApprovalManager;