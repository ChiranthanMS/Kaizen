import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";

// Create axios instance with auth header
const api = axios.create({
  baseURL: "http://localhost:8000",
});

// Add interceptor to include token in requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

function ManagerDashboard() {
  const navigate = useNavigate();
  const [profile, setProfile] = useState(null);
  const [teamOverview, setTeamOverview] = useState([]);
  const [pendingBills, setPendingBills] = useState([]);
  const [allBills, setAllBills] = useState([]);
  const [statistics, setStatistics] = useState({});
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  const [message, setMessage] = useState("");
  const [selectedEmployee, setSelectedEmployee] = useState(null);
  const [employeeBills, setEmployeeBills] = useState([]);

  // Check authentication on component mount
  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) {
      navigate("/login");
      return;
    }
    
    fetchProfile();
    fetchData();
  }, [navigate]);

  const fetchProfile = async () => {
    try {
      const res = await api.get("/profile");
      setProfile(res.data);
      
      // Check if user is manager
      if (res.data.role !== 'manager') {
        navigate("/upload-bill"); // Redirect employees to upload page
      }
    } catch (err) {
      console.error("Error fetching profile:", err);
      if (err.response?.status === 401) {
        localStorage.removeItem("token");
        navigate("/login");
      }
    }
  };

  const fetchData = async () => {
    setLoading(true);
    try {
      await Promise.all([
        fetchTeamOverview(),
        fetchPendingBills(),
        fetchStatistics()
      ]);
    } catch (err) {
      console.error("Error fetching data:", err);
    } finally {
      setLoading(false);
    }
  };

  const fetchTeamOverview = async () => {
    try {
      const res = await api.get("/manager/team-overview");
      setTeamOverview(res.data || []);
    } catch (err) {
      console.error("Error fetching team overview:", err);
    }
  };

  const fetchPendingBills = async () => {
    try {
      const res = await api.get("/manager/pending-bills?page=1&page_size=20");
      setPendingBills(res.data.bills || []);
    } catch (err) {
      console.error("Error fetching pending bills:", err);
    }
  };

  const fetchAllBills = async () => {
    try {
      const res = await api.get("/bills/team-bills?page=1&page_size=50");
      setAllBills(res.data.bills || []);
    } catch (err) {
      console.error("Error fetching all bills:", err);
    }
  };

  const fetchStatistics = async () => {
    try {
      const res = await api.get("/bills/statistics");
      setStatistics(res.data || {});
    } catch (err) {
      console.error("Error fetching statistics:", err);
    }
  };

  const fetchEmployeeBills = async (employeeId) => {
    try {
      const res = await api.get(`/manager/employee/${employeeId}/bills?page=1&page_size=20`);
      setEmployeeBills(res.data.bills || []);
    } catch (err) {
      console.error("Error fetching employee bills:", err);
      showMessage("Failed to fetch employee bills.", true);
    }
  };

  const approveBill = async (billId) => {
    try {
      const res = await api.post(`/manager/bills/${billId}/approve`);
      showMessage(res.data.message);
      // Refresh data
      fetchPendingBills();
      fetchStatistics();
      if (activeTab === 'all-bills') {
        fetchAllBills();
      }
    } catch (err) {
      console.error("Error approving bill:", err);
      showMessage(err.response?.data?.detail || "Failed to approve bill.", true);
    }
  };

  const rejectBill = async (billId, remarks = "") => {
    try {
      const res = await api.post(`/manager/bills/${billId}/reject`, { remarks });
      showMessage(res.data.message);
      // Refresh data
      fetchPendingBills();
      fetchStatistics();
      if (activeTab === 'all-bills') {
        fetchAllBills();
      }
    } catch (err) {
      console.error("Error rejecting bill:", err);
      showMessage(err.response?.data?.detail || "Failed to reject bill.", true);
    }
  };

  const showMessage = (msg, isError = false) => {
    setMessage(msg);
    setTimeout(() => setMessage(""), isError ? 7000 : 5000);
  };

  const logout = () => {
    localStorage.removeItem("token");
    navigate("/login");
  };

  const goToProfile = () => {
    navigate("/profile");
  };

  const handleTabChange = (tab) => {
    setActiveTab(tab);
    if (tab === 'all-bills' && allBills.length === 0) {
      fetchAllBills();
    }
  };

  const handleEmployeeSelect = (employee) => {
    setSelectedEmployee(employee);
    // Note: For now, we'll use the MongoDB ID, but bill fetching might need PostgreSQL ID
    // This could be enhanced to use employee.postgres_id if available
    fetchEmployeeBills(employee.postgres_id || employee.id);
  };

  // Utility functions
  const formatCurrency = (amount, currency = 'INR') => {
    if (amount === null || amount === undefined) return 'N/A';
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: currency
    }).format(amount);
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return 'N/A';
    try {
      return new Date(dateStr).toLocaleDateString();
    } catch {
      return dateStr;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'approved': return '#28a745';
      case 'rejected': return '#dc3545';
      case 'under_review': return '#ffc107';
      default: return '#6c757d';
    }
  };

  const LoadingSpinner = () => (
    <div className="loading-spinner">
      <div className="spinner"></div>
    </div>
  );

  const getMessageClass = () => {
    if (!message) return "";
    return message.toLowerCase().includes("error") || message.toLowerCase().includes("failed")
      ? "message error" 
      : "message success";
  };

  if (loading) {
    return (
      <div className="container">
        <div className="loading-container">
          <LoadingSpinner />
          <h3>Loading Manager Dashboard...</h3>
        </div>
      </div>
    );
  }

  return (
    <div className="container">
      {/* Header */}
      <div className="bill-header">
        <h1 className="app-title">Manager Dashboard</h1>
        <div className="user-info-header">
          {profile && (
            <span className="welcome-text">
              Welcome, Manager {profile.full_name || profile.username}!
            </span>
          )}
          <div className="header-buttons">
            <button className="btn btn-secondary" onClick={goToProfile}>
              Profile
            </button>
            <button className="btn btn-danger" onClick={logout}>
              Logout
            </button>
          </div>
        </div>
      </div>

      {/* Statistics Cards */}
      <div className="statistics-section">
        <div className="stats-grid">
          <div className="stat-card">
            <h3>Total Bills</h3>
            <div className="stat-value">{statistics.total_bills || 0}</div>
          </div>
          <div className="stat-card">
            <h3>Total Amount</h3>
            <div className="stat-value">{formatCurrency(statistics.total_amount || 0)}</div>
          </div>
          <div className="stat-card pending">
            <h3>Pending Approval</h3>
            <div className="stat-value">{statistics.pending_bills || 0}</div>
          </div>
          <div className="stat-card approved">
            <h3>Approved</h3>
            <div className="stat-value">{statistics.approved_bills || 0}</div>
          </div>
          <div className="stat-card rejected">
            <h3>Rejected</h3>
            <div className="stat-value">{statistics.rejected_bills || 0}</div>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="tabs-section">
        <div className="tabs">
          <button 
            className={`tab ${activeTab === 'overview' ? 'active' : ''}`}
            onClick={() => handleTabChange('overview')}
          >
            Team Overview
          </button>
          <button 
            className={`tab ${activeTab === 'pending' ? 'active' : ''}`}
            onClick={() => handleTabChange('pending')}
          >
            Pending Bills ({pendingBills.length})
          </button>
          <button 
            className={`tab ${activeTab === 'all-bills' ? 'active' : ''}`}
            onClick={() => handleTabChange('all-bills')}
          >
            All Bills
          </button>
        </div>
      </div>

      {/* Tab Content */}
      <div className="tab-content">
        {/* Team Overview Tab */}
        {activeTab === 'overview' && (
          <div className="bill-section">
            <h2>Team Overview</h2>
            {teamOverview.length > 0 ? (
              <div className="team-grid">
                {teamOverview.map((employee) => (
                  <div key={employee.id} className="employee-card">
                    <div className="employee-header">
                      <h4>{employee.name || employee.username}</h4>
                      <span className="employee-email">{employee.email}</span>
                    </div>
                    <div className="employee-stats">
                      <div className="stat-row">
                        <span>Username:</span>
                        <span>{employee.username || 'N/A'}</span>
                      </div>
                      <div className="stat-row">
                        <span>Department:</span>
                        <span>{employee.department || 'N/A'}</span>
                      </div>
                      <div className="stat-row">
                        <span>Registration Date:</span>
                        <span>{formatDate(employee.registration_date)}</span>
                      </div>
                      <div className="stat-row">
                        <span>Total Bills:</span>
                        <span>{employee.total_bills || 0}</span>
                      </div>
                      <div className="stat-row">
                        <span>Total Amount:</span>
                        <span>{formatCurrency(employee.total_amount || 0)}</span>
                      </div>
                      <div className="stat-row">
                        <span>Pending:</span>
                        <span className="pending-count">{employee.pending_bills || 0}</span>
                      </div>
                    </div>
                    <button 
                      className="btn btn-primary btn-small"
                      onClick={() => handleEmployeeSelect(employee)}
                    >
                      View Bills
                    </button>
                  </div>
                ))}
              </div>
            ) : (
              <p>No employees found under your management.</p>
            )}
          </div>
        )}

        {/* Pending Bills Tab */}
        {activeTab === 'pending' && (
          <div className="bill-section">
            <h2>Pending Bills for Approval</h2>
            {pendingBills.length > 0 ? (
              <div className="bills-list">
                {pendingBills.map((bill) => (
                  <div key={bill.id} className="bill-item pending-bill">
                    <div className="bill-header-item">
                      <div>
                        <h4>Bill #{bill.id}</h4>
                        <p className="employee-info">
                          {bill.employee_name} ({bill.employee_email})
                        </p>
                      </div>
                      <div className="bill-actions">
                        <button 
                          className="btn btn-success btn-small"
                          onClick={() => approveBill(bill.id)}
                        >
                          ✓ Approve
                        </button>
                        <button 
                          className="btn btn-danger btn-small"
                          onClick={() => rejectBill(bill.id)}
                        >
                          ✗ Reject
                        </button>
                      </div>
                    </div>
                    <div className="bill-details-grid">
                      <div><strong>Amount:</strong> {formatCurrency(bill.amount)}</div>
                      <div><strong>Date:</strong> {formatDate(bill.date)}</div>
                      <div><strong>Vendor:</strong> {bill.vendor || 'N/A'}</div>
                      <div><strong>Category:</strong> {bill.category || 'N/A'}</div>
                      <div><strong>Submitted:</strong> {formatDate(bill.created_at)}</div>
                      <div><strong>File:</strong> {bill.filename || 'N/A'}</div>
                    </div>
                    {bill.remarks && (
                      <div className="bill-remarks">
                        <strong>Remarks:</strong> {bill.remarks}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p>No pending bills for approval.</p>
            )}
          </div>
        )}

        {/* All Bills Tab */}
        {activeTab === 'all-bills' && (
          <div className="bill-section">
            <h2>All Team Bills</h2>
            {allBills.length > 0 ? (
              <div className="bills-list">
                {allBills.map((bill) => (
                  <div key={bill.id} className="bill-item">
                    <div className="bill-header-item">
                      <div>
                        <h4>Bill #{bill.id}</h4>
                        <p className="employee-info">
                          {bill.employee_name} ({bill.employee_email})
                        </p>
                      </div>
                      <span 
                        className="status-badge" 
                        style={{ backgroundColor: getStatusColor(bill.status) }}
                      >
                        {bill.status.toUpperCase()}
                      </span>
                    </div>
                    <div className="bill-details-grid">
                      <div><strong>Amount:</strong> {formatCurrency(bill.amount)}</div>
                      <div><strong>Date:</strong> {formatDate(bill.date)}</div>
                      <div><strong>Vendor:</strong> {bill.vendor || 'N/A'}</div>
                      <div><strong>Category:</strong> {bill.category || 'N/A'}</div>
                      <div><strong>Submitted:</strong> {formatDate(bill.created_at)}</div>
                      <div><strong>Department:</strong> {bill.department || 'N/A'}</div>
                    </div>
                    {bill.remarks && (
                      <div className="bill-remarks">
                        <strong>Remarks:</strong> {bill.remarks}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p>No bills found.</p>
            )}
          </div>
        )}
      </div>

      {/* Employee Bills Modal */}
      {selectedEmployee && (
        <div className="modal-overlay" onClick={() => setSelectedEmployee(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Bills for {selectedEmployee.employee_name}</h3>
              <button 
                className="modal-close"
                onClick={() => setSelectedEmployee(null)}
              >
                ×
              </button>
            </div>
            <div className="modal-body">
              {employeeBills.length > 0 ? (
                <div className="bills-list">
                  {employeeBills.map((bill) => (
                    <div key={bill.id} className="bill-item">
                      <div className="bill-header-item">
                        <h4>Bill #{bill.id}</h4>
                        <span 
                          className="status-badge" 
                          style={{ backgroundColor: getStatusColor(bill.status) }}
                        >
                          {bill.status.toUpperCase()}
                        </span>
                      </div>
                      <div className="bill-details-grid">
                        <div><strong>Amount:</strong> {formatCurrency(bill.amount)}</div>
                        <div><strong>Date:</strong> {formatDate(bill.date)}</div>
                        <div><strong>Vendor:</strong> {bill.vendor || 'N/A'}</div>
                        <div><strong>Category:</strong> {bill.category || 'N/A'}</div>
                      </div>
                      {bill.status === 'pending' && (
                        <div className="bill-actions">
                          <button 
                            className="btn btn-success btn-small"
                            onClick={() => {
                              approveBill(bill.id);
                              fetchEmployeeBills(selectedEmployee.employee_id);
                            }}
                          >
                            ✓ Approve
                          </button>
                          <button 
                            className="btn btn-danger btn-small"
                            onClick={() => {
                              rejectBill(bill.id);
                              fetchEmployeeBills(selectedEmployee.employee_id);
                            }}
                          >
                            ✗ Reject
                          </button>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <p>No bills found for this employee.</p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Message Display */}
      {message && <div className={getMessageClass()}>{message}</div>}
    </div>
  );
}

export default ManagerDashboard;