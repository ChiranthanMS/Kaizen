import React, { useState, useEffect } from 'react';
import './TripSubmissionsDashboard.css';

const TripSubmissionsDashboard = () => {
    const [submissions, setSubmissions] = useState([]);
    const [selectedSubmission, setSelectedSubmission] = useState(null);
    const [submissionDetails, setSubmissionDetails] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [actionLoading, setActionLoading] = useState(false);

    useEffect(() => {
        fetchPendingSubmissions();
    }, []);

    const fetchPendingSubmissions = async () => {
        try {
            setLoading(true);
            const token = localStorage.getItem('token');
            const response = await fetch('http://localhost:8000/trip-budget/pending-trip-submissions', {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error('Failed to fetch pending submissions');
            }

            const data = await response.json();
            setSubmissions(data.pending_submissions || []);
        } catch (err) {
            setError('Failed to load pending trip submissions: ' + err.message);
        } finally {
            setLoading(false);
        }
    };

    const fetchSubmissionDetails = async (submissionId) => {
        try {
            setActionLoading(true);
            const token = localStorage.getItem('token');
            const response = await fetch(`http://localhost:8000/trip-budget/trip-submission-details/${submissionId}`, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error('Failed to fetch submission details');
            }

            const data = await response.json();
            setSubmissionDetails(data);
        } catch (err) {
            setError('Failed to load submission details: ' + err.message);
        } finally {
            setActionLoading(false);
        }
    };

    const handleViewDetails = (submission) => {
        setSelectedSubmission(submission);
        fetchSubmissionDetails(submission.submission_id);
    };

    const handleApproveSubmission = async (submissionId, comments = '') => {
        try {
            setActionLoading(true);
            const token = localStorage.getItem('token');
            const response = await fetch('http://localhost:8000/trip-budget/approve-trip-submission', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    submission_id: submissionId,
                    comments: comments
                })
            });

            if (!response.ok) {
                throw new Error('Failed to approve submission');
            }

            const data = await response.json();
            alert(`✅ ${data.message}`);
            
            // Refresh the submissions list
            await fetchPendingSubmissions();
            setSelectedSubmission(null);
            setSubmissionDetails(null);
        } catch (err) {
            setError('Failed to approve submission: ' + err.message);
        } finally {
            setActionLoading(false);
        }
    };

    const handleRejectSubmission = async (submissionId, reason) => {
        if (!reason || reason.trim() === '') {
            alert('Please provide a reason for rejection');
            return;
        }

        try {
            setActionLoading(true);
            const token = localStorage.getItem('token');
            const response = await fetch('http://localhost:8000/trip-budget/reject-trip-submission', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    submission_id: submissionId,
                    reason: reason
                })
            });

            if (!response.ok) {
                throw new Error('Failed to reject submission');
            }

            const data = await response.json();
            alert(`❌ ${data.message}`);
            
            // Refresh the submissions list
            await fetchPendingSubmissions();
            setSelectedSubmission(null);
            setSubmissionDetails(null);
        } catch (err) {
            setError('Failed to reject submission: ' + err.message);
        } finally {
            setActionLoading(false);
        }
    };

    const formatCurrency = (amount) => {
        return new Intl.NumberFormat('en-IN', {
            style: 'currency',
            currency: 'INR'
        }).format(amount);
    };

    const formatDate = (dateString) => {
        if (!dateString) return 'N/A';
        return new Date(dateString).toLocaleDateString('en-IN');
    };

    const getBudgetUtilizationColor = (utilization) => {
        if (utilization <= 80) return '#28a745'; // Green
        if (utilization <= 100) return '#ffc107'; // Yellow
        return '#dc3545'; // Red
    };

    if (loading) {
        return (
            <div className="trip-submissions-dashboard">
                <div className="loading-container">
                    <div className="loading-spinner"></div>
                    <p>Loading trip submissions...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="trip-submissions-dashboard">
            <div className="dashboard-header">
                <h2>🧳 Trip Submissions for Approval</h2>
                <p>Review and approve completed trips with all associated expenses</p>
                {error && <div className="error-message">{error}</div>}
            </div>

            <div className="dashboard-content">
                {/* Submissions List */}
                <div className="submissions-list">
                    <div className="submissions-header">
                        <h3>Pending Submissions ({submissions.length})</h3>
                        <button 
                            onClick={fetchPendingSubmissions}
                            className="refresh-btn"
                            disabled={loading}
                        >
                            🔄 Refresh
                        </button>
                    </div>

                    {submissions.length === 0 ? (
                        <div className="no-submissions">
                            <p>🎉 No pending trip submissions!</p>
                            <p>All trips have been reviewed.</p>
                        </div>
                    ) : (
                        <div className="submissions-grid">
                            {submissions.map((submission) => (
                                <div key={submission.submission_id} className="submission-card">
                                    <div className="submission-header">
                                        <h4>{submission.employee_name}</h4>
                                        <span className="submission-id">#{submission.submission_id}</span>
                                    </div>
                                    
                                    <div className="submission-details">
                                        <p><strong>Trip:</strong> {submission.trip_purpose}</p>
                                        <p><strong>Destination:</strong> {submission.destination_city}</p>
                                        <p><strong>Duration:</strong> {submission.duration_days} days</p>
                                        <p><strong>Period:</strong> {formatDate(submission.start_date)} - {formatDate(submission.end_date)}</p>
                                    </div>

                                    <div className="submission-financials">
                                        <div className="financial-item">
                                            <span>Bills:</span>
                                            <strong>{submission.total_bills}</strong>
                                        </div>
                                        <div className="financial-item">
                                            <span>Total Amount:</span>
                                            <strong>{formatCurrency(submission.total_amount)}</strong>
                                        </div>
                                        <div className="financial-item">
                                            <span>Budget:</span>
                                            <strong>{formatCurrency(submission.allocated_budget)}</strong>
                                        </div>
                                        <div className="financial-item">
                                            <span>Utilization:</span>
                                            <strong 
                                                style={{ color: getBudgetUtilizationColor(submission.budget_utilization) }}
                                            >
                                                {submission.budget_utilization.toFixed(1)}%
                                            </strong>
                                        </div>
                                    </div>

                                    <div className="submission-actions">
                                        <button 
                                            onClick={() => handleViewDetails(submission)}
                                            className="view-details-btn"
                                        >
                                            👁️ View Details
                                        </button>
                                        <small>Submitted: {formatDate(submission.submitted_at)}</small>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {/* Submission Details Modal */}
                {selectedSubmission && (
                    <div className="modal-overlay">
                        <div className="submission-details-modal">
                            <div className="modal-header">
                                <h3>Trip Submission Details</h3>
                                <button 
                                    onClick={() => {
                                        setSelectedSubmission(null);
                                        setSubmissionDetails(null);
                                    }}
                                    className="close-btn"
                                >
                                    ✕
                                </button>
                            </div>

                            {actionLoading ? (
                                <div className="loading-container">
                                    <div className="loading-spinner"></div>
                                    <p>Loading details...</p>
                                </div>
                            ) : submissionDetails ? (
                                <div className="modal-content">
                                    {/* Trip Summary */}
                                    <div className="trip-summary">
                                        <h4>Trip Summary</h4>
                                        <div className="summary-grid">
                                            <div><strong>Employee:</strong> {submissionDetails.submission_details.employee_name}</div>
                                            <div><strong>Purpose:</strong> {submissionDetails.submission_details.trip_purpose}</div>
                                            <div><strong>Destination:</strong> {submissionDetails.submission_details.destination_city}</div>
                                            <div><strong>Duration:</strong> {submissionDetails.submission_details.duration_days} days</div>
                                            <div><strong>Period:</strong> {formatDate(submissionDetails.submission_details.start_date)} - {formatDate(submissionDetails.submission_details.end_date)}</div>
                                            <div><strong>Budget Allocated:</strong> {formatCurrency(submissionDetails.submission_details.allocated_budget)}</div>
                                            <div><strong>Total Spent:</strong> {formatCurrency(submissionDetails.submission_details.total_amount)}</div>
                                            <div><strong>Utilization:</strong> 
                                                <span style={{ color: getBudgetUtilizationColor(submissionDetails.submission_details.budget_utilization) }}>
                                                    {submissionDetails.submission_details.budget_utilization.toFixed(1)}%
                                                </span>
                                            </div>
                                        </div>
                                    </div>

                                    {/* Bills List */}
                                    <div className="bills-section">
                                        <h4>Bills ({submissionDetails.bills.length})</h4>
                                        <div className="bills-table">
                                            <table>
                                                <thead>
                                                    <tr>
                                                        <th>Date</th>
                                                        <th>Vendor</th>
                                                        <th>Category</th>
                                                        <th>Amount</th>
                                                        <th>Confidence</th>
                                                    </tr>
                                                </thead>
                                                <tbody>
                                                    {submissionDetails.bills.map((bill) => (
                                                        <tr key={bill.bill_id}>
                                                            <td>{formatDate(bill.date)}</td>
                                                            <td>{bill.vendor || 'N/A'}</td>
                                                            <td>
                                                                <span className={`category-badge ${bill.category}`}>
                                                                    {bill.category}
                                                                </span>
                                                            </td>
                                                            <td>{formatCurrency(bill.amount)}</td>
                                                            <td>
                                                                <span className={`confidence-score ${bill.confidence_score >= 0.8 ? 'high' : bill.confidence_score >= 0.6 ? 'medium' : 'low'}`}>
                                                                    {bill.confidence_score ? (bill.confidence_score * 100).toFixed(0) + '%' : 'N/A'}
                                                                </span>
                                                            </td>
                                                        </tr>
                                                    ))}
                                                </tbody>
                                            </table>
                                        </div>
                                    </div>

                                    {/* Action Buttons */}
                                    <div className="modal-actions">
                                        <div className="approval-section">
                                            <textarea
                                                id="approval-comments"
                                                placeholder="Add comments (optional)..."
                                                rows="3"
                                            />
                                            <div className="action-buttons">
                                                <button 
                                                    onClick={() => {
                                                        const comments = document.getElementById('approval-comments').value;
                                                        handleApproveSubmission(selectedSubmission.submission_id, comments);
                                                    }}
                                                    className="approve-btn"
                                                    disabled={actionLoading}
                                                >
                                                    ✅ Approve All Bills
                                                </button>
                                                <button 
                                                    onClick={() => {
                                                        const reason = prompt('Please provide a reason for rejection:');
                                                        if (reason) {
                                                            handleRejectSubmission(selectedSubmission.submission_id, reason);
                                                        }
                                                    }}
                                                    className="reject-btn"
                                                    disabled={actionLoading}
                                                >
                                                    ❌ Reject All Bills
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            ) : (
                                <div className="error-message">Failed to load submission details</div>
                            )}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default TripSubmissionsDashboard;