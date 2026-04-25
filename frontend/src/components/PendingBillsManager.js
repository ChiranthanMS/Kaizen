import React, { useState, useEffect } from 'react';
import './PendingBillsManager.css';

const PendingBillsManager = () => {
    const [pendingBills, setPendingBills] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [processingId, setProcessingId] = useState(null);
    const [showApprovalModal, setShowApprovalModal] = useState(false);
    const [showRejectionModal, setShowRejectionModal] = useState(false);
    const [selectedBill, setSelectedBill] = useState(null);
    const [approvalComments, setApprovalComments] = useState('');
    const [rejectionReason, setRejectionReason] = useState('');

    useEffect(() => {
        fetchPendingBills();
    }, []);

    const fetchPendingBills = async () => {
        try {
            setLoading(true);
            const token = sessionStorage.getItem('token');
            const response = await fetch('http://localhost:8000/manager/pending-bills?page=1&page_size=50', {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                    'Cache-Control': 'no-cache',
                    'Pragma': 'no-cache'
                }
            });

            if (response.ok) {
                const data = await response.json();
                setPendingBills(data.bills || []);
                setError('');
            } else {
                throw new Error('Failed to fetch pending bills');
            }
        } catch (err) {
            console.error('Error fetching pending bills:', err);
            setError('Failed to load pending bills');
        } finally {
            setLoading(false);
        }
    };

    const handleApprove = async () => {
        if (!selectedBill) return;

        try {
            setProcessingId(selectedBill.id);
            const token = sessionStorage.getItem('token');
            
            const response = await fetch(`http://localhost:8000/manager/bills/${selectedBill.id}/approve?remarks=${encodeURIComponent(approvalComments || 'Approved by manager')}`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                await fetchPendingBills(); // Refresh the list
                setShowApprovalModal(false);
                setApprovalComments('');
                setSelectedBill(null);
            } else {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to approve bill');
            }
        } catch (err) {
            console.error('Error approving bill:', err);
            setError(`Failed to approve bill: ${err.message}`);
        } finally {
            setProcessingId(null);
        }
    };

    const handleReject = async () => {
        if (!selectedBill || !rejectionReason.trim()) return;

        try {
            setProcessingId(selectedBill.id);
            const token = sessionStorage.getItem('token');
            
            const response = await fetch(`http://localhost:8000/manager/bills/${selectedBill.id}/reject?remarks=${encodeURIComponent(rejectionReason)}`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                await fetchPendingBills(); // Refresh the list
                setShowRejectionModal(false);
                setRejectionReason('');
                setSelectedBill(null);
            } else {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to reject bill');
            }
        } catch (err) {
            console.error('Error rejecting bill:', err);
            setError(`Failed to reject bill: ${err.message}`);
        } finally {
            setProcessingId(null);
        }
    };

    const formatCurrency = (amount, currency = 'INR') => {
        return new Intl.NumberFormat('en-IN', {
            style: 'currency',
            currency: currency || 'INR'
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

    const openApprovalModal = (bill) => {
        setSelectedBill(bill);
        setShowApprovalModal(true);
    };

    const openRejectionModal = (bill) => {
        setSelectedBill(bill);
        setShowRejectionModal(true);
    };

    if (loading) {
        return (
            <div className="pending-bills-manager">
                <div className="loading-container">
                    <div className="loading-spinner"></div>
                    <h3>Loading Pending Bills...</h3>
                </div>
            </div>
        );
    }

    return (
        <div className="pending-bills-manager">
            <div className="approval-header">
                <h2>📋 Individual Bill Approval Center</h2>
                <p>Review and approve employee expense bills</p>
                <div className="approval-stats">
                    <span className="stat-badge">
                        {pendingBills.length} Pending Bills
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

            {pendingBills.length === 0 ? (
                <div className="empty-submissions">
                    <div className="empty-icon">🧾</div>
                    <h3>No Pending Bills</h3>
                    <p>All individual bills have been processed.</p>
                    <button 
                        className="btn btn-primary"
                        onClick={fetchPendingBills}
                    >
                        🔄 Refresh
                    </button>
                </div>
            ) : (
                <div className="submissions-grid">
                    {pendingBills.map((bill) => (
                        <div key={bill.id} className="submission-card">
                            <div className="submission-header">
                                <div className="submission-info">
                                    <h3>{bill.employee_name || bill.username || 'Unknown Employee'}</h3>
                                    <p className="trip-id">Bill ID: #{bill.id}</p>
                                </div>
                                <div className="submission-status">
                                    <span className="status-badge pending">
                                        Pending Review
                                    </span>
                                </div>
                            </div>

                            <div className="submission-details">
                                <div className="detail-row">
                                    <span className="detail-label">🏪 Vendor:</span>
                                    <span className="detail-value">{bill.vendor || 'N/A'}</span>
                                </div>
                                <div className="detail-row">
                                    <span className="detail-label">📅 Date:</span>
                                    <span className="detail-value">{formatDate(bill.date)}</span>
                                </div>
                                <div className="detail-row">
                                    <span className="detail-label">💵 Amount:</span>
                                    <span className="detail-value expense-amount">
                                        {formatCurrency(bill.amount, bill.currency)}
                                    </span>
                                </div>
                                <div className="detail-row">
                                    <span className="detail-label">📂 Category:</span>
                                    <span className="detail-value">{bill.category || 'N/A'}</span>
                                </div>
                                <div className="detail-row">
                                    <span className="detail-label">🎯 AI Confidence:</span>
                                    <span className="detail-value" style={{color: bill.confidence_score >= 0.8 ? '#4CAF50' : (bill.confidence_score >= 0.6 ? '#FF9800' : '#F44336'), fontWeight: 'bold'}}>
                                        {bill.confidence_score ? `${(bill.confidence_score * 100).toFixed(1)}%` : 'N/A'}
                                    </span>
                                </div>
                                {bill.remarks && (
                                    <div className="detail-row">
                                        <span className="detail-label">💬 AI Remarks:</span>
                                        <span className="detail-value" style={{fontSize: '0.9em', fontStyle: 'italic'}}>{bill.remarks}</span>
                                    </div>
                                )}
                                {bill.rejection_reason && (
                                    <div className="detail-row">
                                        <span className="detail-label" style={{color: '#ff1744'}}>⚠️ Flag Reason:</span>
                                        <span className="detail-value" style={{color: '#ff1744'}}>{bill.rejection_reason}</span>
                                    </div>
                                )}
                                {bill.justification && (
                                    <div className="detail-row" style={{marginTop: '10px', background: 'rgba(255, 255, 255, 0.1)', padding: '10px', borderRadius: '8px'}}>
                                        <span className="detail-label" style={{color: '#2196F3'}}>Employee Justification:</span>
                                        <span className="detail-value">{bill.justification}</span>
                                    </div>
                                )}
                            </div>

                            <div className="submission-actions">
                                <button 
                                    className="btn btn-success"
                                    onClick={() => openApprovalModal(bill)}
                                    disabled={processingId === bill.id}
                                >
                                    {processingId === bill.id ? '⏳' : '✅'} Approve
                                </button>
                                <button 
                                    className="btn btn-danger"
                                    onClick={() => openRejectionModal(bill)}
                                    disabled={processingId === bill.id}
                                >
                                    {processingId === bill.id ? '⏳' : '❌'} Reject
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
                            <h3>✅ Approve Bill #{selectedBill?.id}</h3>
                            <button 
                                className="modal-close"
                                onClick={() => setShowApprovalModal(false)}
                            >
                                ✕
                            </button>
                        </div>
                        <div className="modal-body">
                            <p>
                                Are you sure you want to approve this bill for{' '}
                                <strong>{selectedBill?.employee_name || selectedBill?.username}</strong>?
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
                            <h3>❌ Reject Bill #{selectedBill?.id}</h3>
                            <button 
                                className="modal-close"
                                onClick={() => setShowRejectionModal(false)}
                            >
                                ✕
                            </button>
                        </div>
                        <div className="modal-body">
                            <p>
                                Please provide a reason for rejecting this bill for{' '}
                                <strong>{selectedBill?.employee_name || selectedBill?.username}</strong>:
                            </p>
                            <div className="form-group">
                                <label>Rejection Reason (Required):</label>
                                <textarea
                                    value={rejectionReason}
                                    onChange={(e) => setRejectionReason(e.target.value)}
                                    placeholder="Please explain why this bill is being rejected..."
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

export default PendingBillsManager;
