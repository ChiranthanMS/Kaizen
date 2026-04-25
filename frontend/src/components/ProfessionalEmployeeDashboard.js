import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import EnhancedBillUpload from './EnhancedBillUpload';
import TripBudgetDashboard from './TripBudgetDashboard';
import CompletedTripsEmployee from './CompletedTripsEmployee';
import AnalyticsDashboard from './AnalyticsDashboard';
import './ProfessionalEmployeeDashboard.css';

const ProfessionalEmployeeDashboard = () => {
    const navigate = useNavigate();
    const [profile, setProfile] = useState(null);
    const [activeTab, setActiveTab] = useState('overview');
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [myBills, setMyBills] = useState([]);
    const [justificationText, setJustificationText] = useState({});
    const [dashboardStats, setDashboardStats] = useState({
        totalBills: 0,
        pendingBills: 0,
        approvedBills: 0,
        rejectedBills: 0,
        totalAmount: 0,
        activeTrips: 0,
        completedTrips: 0
    });

    // Auto-refresh polling interval (30s) for manager approval sync
    const refreshInterval = useRef(null);
    const [lastRefresh, setLastRefresh] = useState(null);

    useEffect(() => {
        const token = sessionStorage.getItem('token');
        if (!token) {
            navigate('/login');
            return;
        }
        
        fetchProfile();
        fetchDashboardData();

        // Auto-refresh every 30 seconds to pick up manager approvals
        refreshInterval.current = setInterval(() => {
            fetchDashboardData(true); // silent refresh
        }, 30000);

        // Also refresh when user returns to tab
        const handleVisibility = () => {
            if (document.visibilityState === 'visible') {
                fetchDashboardData(true);
            }
        };
        document.addEventListener('visibilitychange', handleVisibility);

        return () => {
            clearInterval(refreshInterval.current);
            document.removeEventListener('visibilitychange', handleVisibility);
        };
    }, [navigate]);

    const fetchProfile = async () => {
        try {
            const token = sessionStorage.getItem('token');
            const response = await fetch('http://localhost:8000/profile', {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                const data = await response.json();
                setProfile(data);
                
                if (data.role === 'manager') {
                    navigate('/manager-dashboard');
                }
            } else {
                throw new Error('Failed to fetch profile');
            }
        } catch (err) {
            console.error('Error fetching profile:', err);
            if (err.response?.status === 401) {
                sessionStorage.removeItem('token');
                navigate('/login');
            }
        }
    };

    const fetchDashboardData = async (silent = false) => {
        try {
            if (!silent) setLoading(true);
            const token = sessionStorage.getItem('token');
            
            // Fetch employee bills and trips data
            const [billsRes, completedTripsRes] = await Promise.all([
                fetch('http://localhost:8000/bills/my-bills', {
                    headers: { 
                        'Authorization': `Bearer ${token}`,
                        'Cache-Control': 'no-cache',
                        'Pragma': 'no-cache'
                    }
                }).catch(() => ({ ok: false })),
                fetch('http://localhost:8000/trip-budget/completed-trips', {
                    headers: { 
                        'Authorization': `Bearer ${token}`,
                        'Cache-Control': 'no-cache',
                        'Pragma': 'no-cache'
                    }
                }).catch(() => ({ ok: false }))
            ]);

            // Process bills data
            let billsData = [];
            let serverStats = null;
            if (billsRes.ok) {
                const billsResponse = await billsRes.json();
                billsData = billsResponse.bills || [];
                serverStats = billsResponse.statistics || null;
                setMyBills(billsData);
            }

            // Process completed trips data
            let completedTripsData = [];
            if (completedTripsRes.ok) {
                const tripsResponse = await completedTripsRes.json();
                completedTripsData = tripsResponse.completed_trips || [];
            }

            // Use server statistics if available, otherwise calculate from bills
            const stats = {
                totalBills: serverStats ? (serverStats.total_bills || 0) : billsData.length,
                pendingBills: serverStats ? (serverStats.pending_bills || 0) : billsData.filter(bill => bill.status === 'pending').length,
                approvedBills: serverStats ? (serverStats.approved_bills || 0) : billsData.filter(bill => bill.status === 'approved').length,
                rejectedBills: serverStats ? (serverStats.rejected_bills || 0) : billsData.filter(bill => bill.status === 'rejected').length,
                totalAmount: serverStats ? (parseFloat(serverStats.total_amount) || 0) : billsData.reduce((sum, bill) => sum + (parseFloat(bill.amount) || 0), 0),
                activeTrips: 0,
                completedTrips: completedTripsData.length
            };

            setDashboardStats(stats);
            setLastRefresh(new Date());
            setError('');
        } catch (err) {
            console.error('Error fetching dashboard data:', err);
            if (!silent) setError('Failed to load dashboard data');
        } finally {
            if (!silent) setLoading(false);
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

    const getStatusBadge = (status) => {
        const statusConfig = {
            'pending': { class: 'status-pending', text: 'Pending' },
            'approved': { class: 'status-approved', text: 'Approved' },
            'rejected': { class: 'status-rejected', text: 'Rejected' },
            'under_review': { class: 'status-review', text: 'Under Review' }
        };
        
        const config = statusConfig[status] || { class: 'status-unknown', text: status };
        return <span className={`status-badge ${config.class}`}>{config.text}</span>;
    };

    const handleDownloadReport = (billId) => {
        const token = sessionStorage.getItem('token');
        window.open(`http://localhost:8000/bills/bill/${billId}/report?token=${token}`, '_blank');
    };

    const handleSubmitJustification = async (billId) => {
        const text = justificationText[billId];
        if (!text || text.trim() === '') return;
        
        try {
            const token = sessionStorage.getItem('token');
            const response = await fetch(`http://localhost:8000/bills/bill/${billId}/justify?justification=${encodeURIComponent(text)}`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (response.ok) {
                alert('Justification submitted successfully! Sent to manager for review.');
                setJustificationText(prev => ({...prev, [billId]: ''}));
                fetchDashboardData();
            } else {
                alert('Failed to submit justification.');
            }
        } catch (err) {
            console.error(err);
            alert('Error submitting justification.');
        }
    };

    const logout = () => {
        sessionStorage.removeItem('token');
        window.location.href = '/login';
    };

    const goToProfile = () => {
        navigate('/profile');
    };

    if (loading) {
        return (
            <div className="professional-employee-dashboard">
                <div className="loading-container">
                    <div className="loading-spinner"></div>
                    <h3>Loading Your Dashboard...</h3>
                </div>
            </div>
        );
    }

    return (
        <div className="professional-employee-dashboard">
            {/* Header */}
            <div className="dashboard-header">
                <div className="header-content">
                    <div className="header-left">
                        <h1 className="dashboard-title">Employee Dashboard</h1>
                        {profile && (
                            <p className="welcome-text">
                                Welcome back, {profile.full_name || profile.username}
                            </p>
                        )}
                    </div>
                    <div className="header-actions">
                        <button className="btn btn-secondary" onClick={goToProfile}>
                            👤 Profile
                        </button>
                        <button className="btn btn-danger" onClick={logout}>
                            🚪 Logout
                        </button>
                    </div>
                </div>
            </div>

            {/* Statistics Overview */}
            <div className="stats-overview">
                <div className="stats-grid">
                    <div className="stat-card primary">
                        <div className="stat-icon">📄</div>
                        <div className="stat-content">
                            <div className="stat-number">{dashboardStats.totalBills}</div>
                            <div className="stat-label">Total Bills</div>
                        </div>
                    </div>
                    
                    <div className="stat-card warning">
                        <div className="stat-icon">⏳</div>
                        <div className="stat-content">
                            <div className="stat-number">{dashboardStats.pendingBills}</div>
                            <div className="stat-label">Pending Approval</div>
                        </div>
                    </div>
                    
                    <div className="stat-card success">
                        <div className="stat-icon">✅</div>
                        <div className="stat-content">
                            <div className="stat-number">{dashboardStats.approvedBills}</div>
                            <div className="stat-label">Approved Bills</div>
                        </div>
                    </div>
                    
                    <div className="stat-card info">
                        <div className="stat-icon">💰</div>
                        <div className="stat-content">
                            <div className="stat-number">{formatCurrency(dashboardStats.totalAmount)}</div>
                            <div className="stat-label">Total Expenses</div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Navigation Tabs */}
            <div className="dashboard-navigation">
                <div className="nav-tabs">
                    <button 
                        className={`nav-tab ${activeTab === 'overview' ? 'active' : ''}`}
                        onClick={() => setActiveTab('overview')}
                    >
                        📊 Overview
                    </button>
                    <button 
                        className={`nav-tab ${activeTab === 'upload' ? 'active' : ''}`}
                        onClick={() => setActiveTab('upload')}
                    >
                        📤 Upload Bill
                    </button>
                    <button 
                        className={`nav-tab ${activeTab === 'my-bills' ? 'active' : ''}`}
                        onClick={() => setActiveTab('my-bills')}
                    >
                        📋 My Bills ({dashboardStats.totalBills})
                    </button>
                    <button 
                        className={`nav-tab ${activeTab === 'trips' ? 'active' : ''}`}
                        onClick={() => setActiveTab('trips')}
                    >
                        ✈️ Trip Management
                    </button>
                    <button 
                        className={`nav-tab ${activeTab === 'completed' ? 'active' : ''}`}
                        onClick={() => setActiveTab('completed')}
                    >
                        📚 Completed Trips
                    </button>
                    <button 
                        className={`nav-tab ${activeTab === 'analytics' ? 'active' : ''}`}
                        onClick={() => setActiveTab('analytics')}
                    >
                        📈 Analytics
                    </button>
                </div>
            </div>

            {/* Tab Content */}
            <div className="dashboard-content">
                {activeTab === 'overview' && (
                    <div className="overview-content">
                        <div className="overview-grid">
                            {/* Quick Actions */}
                            <div className="overview-card">
                                <h3>🚀 Quick Actions</h3>
                                <div className="quick-actions">
                                    <button 
                                        className="action-btn primary"
                                        onClick={() => setActiveTab('upload')}
                                    >
                                        📤 Upload New Bill
                                    </button>
                                    <button 
                                        className="action-btn secondary"
                                        onClick={() => setActiveTab('my-bills')}
                                    >
                                        📋 View My Bills ({dashboardStats.totalBills})
                                    </button>
                                    <button 
                                        className="action-btn tertiary"
                                        onClick={() => setActiveTab('trips')}
                                    >
                                        ✈️ Manage Trips
                                    </button>
                                </div>
                            </div>

                            {/* Bills Summary */}
                            <div className="overview-card">
                                <h3>📊 Bills Summary</h3>
                                <div className="bills-summary">
                                    <div className="summary-item">
                                        <span className="summary-label">Total Submitted:</span>
                                        <span className="summary-value">{dashboardStats.totalBills}</span>
                                    </div>
                                    <div className="summary-item">
                                        <span className="summary-label">Pending Review:</span>
                                        <span className="summary-value pending">{dashboardStats.pendingBills}</span>
                                    </div>
                                    <div className="summary-item">
                                        <span className="summary-label">Approved:</span>
                                        <span className="summary-value approved">{dashboardStats.approvedBills}</span>
                                    </div>
                                    <div className="summary-item">
                                        <span className="summary-label">Rejected:</span>
                                        <span className="summary-value rejected">{dashboardStats.rejectedBills}</span>
                                    </div>
                                </div>
                            </div>

                            {/* Recent Bills */}
                            <div className="overview-card full-width">
                                <h3>📄 Recent Bills</h3>
                                {myBills.length > 0 ? (
                                    <div className="recent-bills">
                                        {myBills.slice(0, 5).map((bill) => (
                                            <div key={bill.id} className="recent-bill-item">
                                                <div className="bill-info">
                                                    <div className="bill-header">
                                                        <strong>Bill #{bill.id}</strong>
                                                        {getStatusBadge(bill.status)}
                                                    </div>
                                                    <div className="bill-details">
                                                        <span className="bill-amount">{formatCurrency(bill.amount)}</span>
                                                        <span className="bill-date">{formatDate(bill.date)}</span>
                                                        <span className="bill-vendor">{bill.vendor || 'N/A'}</span>
                                                    </div>
                                                </div>
                                            </div>
                                        ))}
                                        {myBills.length > 5 && (
                                            <div className="view-all">
                                                <button 
                                                    className="btn btn-link"
                                                    onClick={() => setActiveTab('my-bills')}
                                                >
                                                    View All {myBills.length} Bills →
                                                </button>
                                            </div>
                                        )}
                                    </div>
                                ) : (
                                    <div className="empty-state">
                                        <p>No bills submitted yet. Upload your first bill to get started!</p>
                                        <button 
                                            className="btn btn-primary"
                                            onClick={() => setActiveTab('upload')}
                                        >
                                            Upload First Bill
                                        </button>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                )}

                {activeTab === 'upload' && (
                    <div className="upload-content">
                        <div className="upload-header">
                            <h2>📤 Upload New Bill</h2>
                            <p>Upload your expense receipts for processing and approval</p>
                        </div>
                        <EnhancedBillUpload onUploadSuccess={(data) => {
                            fetchDashboardData();
                            // Switch to my-bills tab after 2 seconds so user sees the new bill
                            setTimeout(() => setActiveTab('my-bills'), 2000);
                        }} />
                    </div>
                )}

                {activeTab === 'my-bills' && (
                    <div className="bills-content">
                        <div className="bills-header">
                            <h2>📋 My Bills</h2>
                            <p>View and manage all your submitted expense bills</p>
                        </div>
                        
                        {myBills.length > 0 ? (
                            <div className="bills-grid">
                                {myBills.map((bill) => (
                                    <div key={bill.id} className="bill-card">
                                        <div className="bill-card-header">
                                            <div className="bill-id">Bill #{bill.id}</div>
                                            {getStatusBadge(bill.status)}
                                        </div>
                                        
                                        <div className="bill-card-content">
                                            <div className="bill-amount-large">
                                                {formatCurrency(bill.amount)}
                                            </div>
                                            
                                            <div className="bill-details-grid">
                                                <div className="detail-item">
                                                    <span className="detail-label">📅 Date:</span>
                                                    <span className="detail-value">{formatDate(bill.date)}</span>
                                                </div>
                                                <div className="detail-item">
                                                    <span className="detail-label">🏪 Vendor:</span>
                                                    <span className="detail-value">{bill.vendor || 'N/A'}</span>
                                                </div>
                                                <div className="detail-item">
                                                    <span className="detail-label">📂 Category:</span>
                                                    <span className="detail-value">{bill.category || 'N/A'}</span>
                                                </div>
                                                <div className="detail-item">
                                                    <span className="detail-label">📄 File:</span>
                                                    <span className="detail-value">{bill.filename || 'N/A'}</span>
                                                </div>
                                                <div className="detail-item">
                                                    <span className="detail-label">📤 Submitted:</span>
                                                    <span className="detail-value">{formatDate(bill.created_at)}</span>
                                                </div>
                                                {bill.confidence_score && (
                                                    <div className="detail-item">
                                                        <span className="detail-label">🎯 Confidence:</span>
                                                        <span className="detail-value">{(bill.confidence_score * 100).toFixed(1)}%</span>
                                                    </div>
                                                )}
                                            </div>
                                            
                                            {bill.remarks && (
                                                <div className="bill-remarks">
                                                    <strong>💬 AI/Manager Comments:</strong>
                                                    <p>{bill.remarks}</p>
                                                </div>
                                            )}
                                            {bill.rejection_reason && (
                                                <div className="bill-remarks" style={{color: '#ff1744'}}>
                                                    <strong>⚠️ Flag Reason:</strong>
                                                    <p>{bill.rejection_reason}</p>
                                                </div>
                                            )}
                                            
                                            <div className="bill-actions" style={{marginTop: '15px', display: 'flex', gap: '10px', flexWrap: 'wrap'}}>
                                                <button className="btn btn-sm btn-secondary" onClick={() => handleDownloadReport(bill.id)}>
                                                    📄 Download Report
                                                </button>
                                                
                                                {(bill.status === 'rejected' || bill.status === 'pending') && (
                                                    <div className="justification-section" style={{display: 'flex', gap: '10px', width: '100%', marginTop: '10px'}}>
                                                        <input 
                                                            type="text" 
                                                            className="input-field" 
                                                            placeholder="Provide justification..."
                                                            value={justificationText[bill.id] || ''}
                                                            onChange={(e) => setJustificationText({...justificationText, [bill.id]: e.target.value})}
                                                            style={{flex: 1}}
                                                        />
                                                        <button className="btn btn-sm btn-primary" onClick={() => handleSubmitJustification(bill.id)} style={{width: 'auto'}}>
                                                            Submit Justification
                                                        </button>
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <div className="empty-bills">
                                <div className="empty-icon">📄</div>
                                <h3>No Bills Submitted</h3>
                                <p>You haven't submitted any expense bills yet.</p>
                                <button 
                                    className="btn btn-primary"
                                    onClick={() => setActiveTab('upload')}
                                >
                                    Upload Your First Bill
                                </button>
                            </div>
                        )}
                    </div>
                )}

                {activeTab === 'trips' && (
                    <div className="trips-content">
                        <TripBudgetDashboard />
                    </div>
                )}

                {activeTab === 'completed' && (
                    <div className="completed-content">
                        <CompletedTripsEmployee />
                    </div>
                )}

                {activeTab === 'analytics' && (
                    <div className="analytics-content">
                        <AnalyticsDashboard />
                    </div>
                )}
            </div>

            {/* Error Display */}
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
        </div>
    );
};

export default ProfessionalEmployeeDashboard;