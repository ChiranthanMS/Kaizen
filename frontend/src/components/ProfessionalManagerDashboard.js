import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import TripSubmissionsDashboard from './TripSubmissionsDashboard';
import CompletedTripsManager from './CompletedTripsManager';
import TripApprovalManager from './TripApprovalManager';
import TripRequestApproval from './TripRequestApproval';
import AnalyticsDashboard from './AnalyticsDashboard';
import PendingBillsManager from './PendingBillsManager';
import './ProfessionalManagerDashboard.css';

const ProfessionalManagerDashboard = () => {
    const navigate = useNavigate();
    const [profile, setProfile] = useState(null);
    const [activeTab, setActiveTab] = useState('overview');
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [dashboardStats, setDashboardStats] = useState({
        totalEmployees: 0,
        pendingSubmissions: 0,
        pendingRequests: 0,
        completedTrips: 0,
        totalExpenses: 0,
        pendingBills: 0,
        approvedBills: 0
    });
    const [teamEmployees, setTeamEmployees] = useState([]);
    const [pendingBills, setPendingBills] = useState([]);

    useEffect(() => {
        const token = sessionStorage.getItem('token');
        if (!token) {
            navigate('/login');
            return;
        }
        
        fetchProfile();
        fetchDashboardData();
    }, [navigate]);

    const fetchProfile = async () => {
        try {
            const token = sessionStorage.getItem('token');
            const response = await fetch('http://localhost:8000/profile', {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                    'Cache-Control': 'no-cache',
                    'Pragma': 'no-cache'
                }
            });

            if (response.ok) {
                const data = await response.json();
                setProfile(data);
                
                if (data.role !== 'manager') {
                    navigate('/upload-bill');
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

    const fetchDashboardData = async () => {
        try {
            setLoading(true);
            const token = sessionStorage.getItem('token');
            
            // Fetch all data in parallel - Use all-employees to get ALL employees, not just team
            const [allEmployeesRes, submissionsRes, requestsRes, completedRes] = await Promise.all([
                fetch('http://localhost:8000/manager/all-employees', {
                    headers: { 
                        'Authorization': `Bearer ${token}`,
                        'Cache-Control': 'no-cache',
                        'Pragma': 'no-cache'
                    }
                }),
                fetch('http://localhost:8000/trip-budget/pending-trip-submissions', {
                    headers: { 
                        'Authorization': `Bearer ${token}`,
                        'Cache-Control': 'no-cache',
                        'Pragma': 'no-cache'
                    }
                }),
                fetch('http://localhost:8000/trip-budget/pending-requests', {
                    headers: { 
                        'Authorization': `Bearer ${token}`,
                        'Cache-Control': 'no-cache',
                        'Pragma': 'no-cache'
                    }
                }),
                fetch('http://localhost:8000/trip-budget/manager/completed-trips', {
                    headers: { 
                        'Authorization': `Bearer ${token}`,
                        'Cache-Control': 'no-cache',
                        'Pragma': 'no-cache'
                    }
                })
            ]);

            // Process all employees data
            let allEmployeesData = [];
            if (allEmployeesRes.ok) {
                allEmployeesData = await allEmployeesRes.json();
                setTeamEmployees(allEmployeesData);
            } else {
                console.error('Failed to fetch all employees:', allEmployeesRes.status);
            }

            // Process submissions data
            let submissionsData = { pending_submissions: [], total_count: 0 };
            if (submissionsRes.ok) {
                submissionsData = await submissionsRes.json();
            }

            // Process requests data
            let requestsData = { pending_requests: [], total_pending: 0 };
            if (requestsRes.ok) {
                requestsData = await requestsRes.json();
            }

            // Process completed trips data
            let completedData = { completed_trips: [], total_count: 0 };
            if (completedRes.ok) {
                completedData = await completedRes.json();
            }

            // Calculate dashboard statistics
            const stats = {
                totalEmployees: allEmployeesData.length,
                pendingSubmissions: submissionsData.total_count || 0,
                pendingRequests: requestsData.total_pending || 0,
                completedTrips: completedData.total_count || 0,
                totalExpenses: completedData.completed_trips?.reduce((sum, trip) => 
                    sum + (trip.actual_total_amount || 0), 0) || 0,
                pendingBills: allEmployeesData.reduce((sum, emp) => sum + (emp.pending_bills || 0), 0),
                approvedBills: allEmployeesData.reduce((sum, emp) => sum + (emp.approved_bills || 0), 0)
            };

            setDashboardStats(stats);
            setError('');
        } catch (err) {
            console.error('Error fetching dashboard data:', err);
            setError('Failed to load dashboard data');
        } finally {
            setLoading(false);
        }
    };

    const formatCurrency = (amount) => {
        return new Intl.NumberFormat('en-IN', {
            style: 'currency',
            currency: 'INR'
        }).format(amount || 0);
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
            <div className="professional-manager-dashboard">
                <div className="loading-container">
                    <div className="loading-spinner"></div>
                    <h3>Loading Manager Dashboard...</h3>
                </div>
            </div>
        );
    }

    return (
        <div className="professional-manager-dashboard">
            {/* Header */}
            <div className="dashboard-header">
                <div className="header-content">
                    <div className="header-left">
                        <h1 className="dashboard-title">Manager Dashboard</h1>
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
                        <div className="stat-icon">👥</div>
                        <div className="stat-content">
                            <div className="stat-number">{dashboardStats.totalEmployees}</div>
                            <div className="stat-label">Team Members</div>
                        </div>
                    </div>
                    
                    <div className="stat-card warning">
                        <div className="stat-icon">⏳</div>
                        <div className="stat-content">
                            <div className="stat-number">{dashboardStats.pendingSubmissions}</div>
                            <div className="stat-label">Pending Submissions</div>
                        </div>
                    </div>
                    
                    <div className="stat-card danger">
                        <div className="stat-icon">🎯</div>
                        <div className="stat-content">
                            <div className="stat-number">{dashboardStats.pendingRequests}</div>
                            <div className="stat-label">Trip Requests</div>
                        </div>
                    </div>
                    
                    <div className="stat-card success">
                        <div className="stat-icon">✅</div>
                        <div className="stat-content">
                            <div className="stat-number">{dashboardStats.completedTrips}</div>
                            <div className="stat-label">Completed Trips</div>
                        </div>
                    </div>
                    
                    <div className="stat-card info">
                        <div className="stat-icon">💰</div>
                        <div className="stat-content">
                            <div className="stat-number">{formatCurrency(dashboardStats.totalExpenses)}</div>
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
                        className={`nav-tab ${activeTab === 'requests' ? 'active' : ''}`}
                        onClick={() => setActiveTab('requests')}
                    >
                        🎯 Trip Requests ({dashboardStats.pendingRequests})
                    </button>
                    <button 
                        className={`nav-tab ${activeTab === 'submissions' ? 'active' : ''}`}
                        onClick={() => setActiveTab('submissions')}
                    >
                        📋 Trip Submissions ({dashboardStats.pendingSubmissions})
                    </button>
                    <button 
                        className={`nav-tab ${activeTab === 'approvals' ? 'active' : ''}`}
                        onClick={() => setActiveTab('approvals')}
                    >
                        🎯 Trip Approvals ({dashboardStats.pendingSubmissions})
                    </button>
                    <button 
                        className={`nav-tab ${activeTab === 'completed' ? 'active' : ''}`}
                        onClick={() => setActiveTab('completed')}
                    >
                        ✅ Completed Trips
                    </button>
                    <button 
                        className={`nav-tab ${activeTab === 'team' ? 'active' : ''}`}
                        onClick={() => setActiveTab('team')}
                    >
                        👥 All Employees ({dashboardStats.totalEmployees})
                    </button>
                    <button 
                        className={`nav-tab ${activeTab === 'bills' ? 'active' : ''}`}
                        onClick={() => setActiveTab('bills')}
                    >
                        🧾 Approve Bills ({dashboardStats.pendingBills})
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
                                        onClick={() => setActiveTab('requests')}
                                        disabled={dashboardStats.pendingRequests === 0}
                                    >
                                        🎯 Approve Trip Requests ({dashboardStats.pendingRequests})
                                    </button>
                                    <button 
                                        className="action-btn secondary"
                                        onClick={() => setActiveTab('approvals')}
                                        disabled={dashboardStats.pendingSubmissions === 0}
                                    >
                                        📋 Approve Submissions ({dashboardStats.pendingSubmissions})
                                    </button>
                                    <button 
                                        className="action-btn tertiary"
                                        onClick={() => setActiveTab('team')}
                                    >
                                        👥 Manage Team ({dashboardStats.totalEmployees})
                                    </button>
                                </div>
                            </div>

                            {/* Recent Activity */}
                            <div className="overview-card">
                                <h3>📈 Activity Summary</h3>
                                <div className="activity-summary">
                                    <div className="activity-item">
                                        <span className="activity-label">Pending Bills:</span>
                                        <span className="activity-value">{dashboardStats.pendingBills}</span>
                                    </div>
                                    <div className="activity-item">
                                        <span className="activity-label">Approved Bills:</span>
                                        <span className="activity-value">{dashboardStats.approvedBills}</span>
                                    </div>
                                    <div className="activity-item">
                                        <span className="activity-label">Team Size:</span>
                                        <span className="activity-value">{dashboardStats.totalEmployees}</span>
                                    </div>
                                    <div className="activity-item">
                                        <span className="activity-label">Total Processed:</span>
                                        <span className="activity-value">{formatCurrency(dashboardStats.totalExpenses)}</span>
                                    </div>
                                </div>
                            </div>

                            {/* Team Performance */}
                            <div className="overview-card full-width">
                                <h3>👥 Team Performance</h3>
                                {teamEmployees.length > 0 ? (
                                    <div className="team-performance">
                                        {teamEmployees.slice(0, 5).map((employee) => (
                                            <div key={employee.id} className="performance-item">
                                                <div className="employee-info">
                                                    <strong>{employee.name || employee.username}</strong>
                                                    <span className="employee-email">{employee.email}</span>
                                                </div>
                                                <div className="employee-stats">
                                                    <span className="stat">
                                                        Bills: {employee.total_bills || 0}
                                                    </span>
                                                    <span className="stat">
                                                        Amount: {formatCurrency(employee.total_amount || 0)}
                                                    </span>
                                                    <span className="stat pending">
                                                        Pending: {employee.pending_bills || 0}
                                                    </span>
                                                </div>
                                            </div>
                                        ))}
                                        {teamEmployees.length > 5 && (
                                            <div className="view-all">
                                                <button 
                                                    className="btn btn-link"
                                                    onClick={() => setActiveTab('team')}
                                                >
                                                    View All {teamEmployees.length} Team Members →
                                                </button>
                                            </div>
                                        )}
                                    </div>
                                ) : (
                                    <div className="empty-state">
                                        <p>No team members found. Team data will appear here once employees are assigned to you.</p>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                )}

                {activeTab === 'requests' && (
                    <div className="requests-content">
                        <TripRequestApproval />
                    </div>
                )}

                {activeTab === 'submissions' && (
                    <div className="submissions-content">
                        <TripSubmissionsDashboard />
                    </div>
                )}

                {activeTab === 'approvals' && (
                    <div className="approvals-content">
                        <TripApprovalManager />
                    </div>
                )}

                {activeTab === 'completed' && (
                    <div className="completed-content">
                        <CompletedTripsManager />
                    </div>
                )}

                {activeTab === 'team' && (
                    <div className="team-content">
                        <div className="team-header">
                            <h2>👥 All Employees Overview</h2>
                            <p>Manage and monitor all employees' expense activities across the organization</p>
                        </div>
                        
                        {teamEmployees.length > 0 ? (
                            <div className="team-grid">
                                {teamEmployees.map((employee) => (
                                    <div key={employee.id} className="team-member-card">
                                        <div className="member-header">
                                            <div className="member-avatar">
                                                {(employee.name || employee.username || 'U').charAt(0).toUpperCase()}
                                            </div>
                                            <div className="member-info">
                                                <h4>{employee.name || employee.username}</h4>
                                                <p className="member-email">{employee.email}</p>
                                                {employee.department && (
                                                    <p className="member-department">{employee.department}</p>
                                                )}
                                            </div>
                                        </div>
                                        
                                        <div className="member-stats">
                                            <div className="stat-row">
                                                <span className="stat-label">Total Bills:</span>
                                                <span className="stat-value">{employee.total_bills || 0}</span>
                                            </div>
                                            <div className="stat-row">
                                                <span className="stat-label">Total Amount:</span>
                                                <span className="stat-value">{formatCurrency(employee.total_amount || 0)}</span>
                                            </div>
                                            <div className="stat-row">
                                                <span className="stat-label">Pending:</span>
                                                <span className="stat-value pending">{employee.pending_bills || 0}</span>
                                            </div>
                                            <div className="stat-row">
                                                <span className="stat-label">Approved:</span>
                                                <span className="stat-value approved">{employee.approved_bills || 0}</span>
                                            </div>
                                        </div>
                                        
                                        <div className="member-actions">
                                            <button className="btn btn-sm btn-primary" onClick={() => alert(`Detailed view for ${employee.name || employee.username} is coming soon!`)}>
                                                View Details
                                            </button>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <div className="empty-team">
                                <div className="empty-icon">👥</div>
                                <h3>No Employees Found</h3>
                                <p>No employees are currently registered in the system.</p>
                                <p>Employee data will appear here once users register and submit expense bills.</p>
                            </div>
                        )}
                    </div>
                )}

                {activeTab === 'analytics' && (
                    <div className="analytics-content">
                        <AnalyticsDashboard />
                    </div>
                )}

                {activeTab === 'bills' && (
                    <div className="bills-content">
                        <PendingBillsManager />
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

export default ProfessionalManagerDashboard;