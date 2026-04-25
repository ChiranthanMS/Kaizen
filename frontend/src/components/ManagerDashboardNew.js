import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import ManagerTripApprovals from './ManagerTripApprovals';
import TripSubmissionsDashboard from './TripSubmissionsDashboard';

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

function ManagerDashboardNew() {
  const navigate = useNavigate();
  const [profile, setProfile] = useState(null);
  const [employees, setEmployees] = useState([]);
  const [allEmployees, setAllEmployees] = useState([]);
  const [pendingBills, setPendingBills] = useState([]);
  const [statistics, setStatistics] = useState({});
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  const [message, setMessage] = useState("");
  const [searchTerm, setSearchTerm] = useState("");
  const [departmentFilter, setDepartmentFilter] = useState("");
  const [selectedEmployee, setSelectedEmployee] = useState(null);
  const [employeeBills, setEmployeeBills] = useState([]);
  const [showEmployeeModal, setShowEmployeeModal] = useState(false);

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
        fetchTeamEmployees(),
        fetchAllEmployees(),
        fetchPendingBills(),
        fetchStatistics()
      ]);
    } catch (err) {
      console.error("Error fetching data:", err);
    } finally {
      setLoading(false);
    }
  };

  const fetchTeamEmployees = async () => {
    try {
      const res = await api.get("/manager/team-overview");
      setEmployees(res.data || []);
    } catch (err) {
      console.error("Error fetching team employees:", err);
      showMessage("Failed to fetch team employees", true);
    }
  };

  const fetchAllEmployees = async () => {
    try {
      const res = await api.get("/manager/all-employees");
      setAllEmployees(res.data || []);
    } catch (err) {
      console.error("Error fetching all employees:", err);
      // Fallback to team employees if all-employees endpoint fails
      try {
        const fallbackRes = await api.get("/manager/team-overview");
        setAllEmployees(fallbackRes.data || []);
      } catch (fallbackErr) {
        console.error("Error fetching fallback employees:", fallbackErr);
      }
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

  const fetchStatistics = async () => {
    try {
      const res = await api.get("/manager/statistics");
      setStatistics(res.data || {});
    } catch (err) {
      console.error("Error fetching statistics:", err);
    }
  };

  const fetchEmployeeBills = async (employeeId) => {
    try {
      const res = await api.get(`/manager/employee/${employeeId}/bills?page=1&page_size=50`);
      setEmployeeBills(res.data.bills || []);
    } catch (err) {
      console.error("Error fetching employee bills:", err);
      showMessage("Failed to fetch employee bills", true);
    }
  };

  const approveBill = async (billId) => {
    try {
      await api.put(`/bills/${billId}/status`, { status: "approved" });
      showMessage("Bill approved successfully!");
      fetchPendingBills();
      fetchStatistics();
    } catch (err) {
      console.error("Error approving bill:", err);
      showMessage(err.response?.data?.detail || "Failed to approve bill.", true);
    }
  };

  const rejectBill = async (billId) => {
    try {
      await api.put(`/bills/${billId}/status`, { status: "rejected" });
      showMessage("Bill rejected successfully!");
      fetchPendingBills();
      fetchStatistics();
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
  };

  const handleEmployeeSelect = (employee) => {
    setSelectedEmployee(employee);
    setShowEmployeeModal(true);
    fetchEmployeeBills(employee.postgres_id || employee.id);
  };

  const closeEmployeeModal = () => {
    setShowEmployeeModal(false);
    setSelectedEmployee(null);
    setEmployeeBills([]);
  };

  // Filter employees based on search and department
  const filteredEmployees = allEmployees.filter(employee => {
    const matchesSearch = !searchTerm || 
      employee.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      employee.username?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      employee.email?.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesDepartment = !departmentFilter || 
      employee.department?.toLowerCase().includes(departmentFilter.toLowerCase());
    
    return matchesSearch && matchesDepartment;
  });

  // Get unique departments for filter
  const departments = [...new Set(allEmployees.map(emp => emp.department).filter(Boolean))];

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
      <div className="loading-dots">
        <div className="loading-dot"></div>
        <div className="loading-dot"></div>
        <div className="loading-dot"></div>
      </div>
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
      <div className="manager-container">
        <div className="loading-container">
          <LoadingSpinner />
          <h3>Loading Manager Dashboard...</h3>
        </div>
      </div>
    );
  }

  return (
    <div className="manager-container">
      {/* Header */}
      <div className="manager-header">
        <div className="header-content">
          <div className="header-left">
            <h1 className="manager-title">Manager Dashboard</h1>
            <p className="manager-subtitle">Employee Management & Bill Oversight</p>
          </div>
          <div className="header-right">
            {profile && (
              <div className="manager-profile">
                <div className="profile-info">
                  <span className="manager-name">{profile.full_name || profile.username}</span>
                  <span className="manager-role">Manager</span>
                  <span className="manager-department">{profile.department}</span>
                </div>
                <div className="header-actions">
                  <button className="btn btn-outline" onClick={goToProfile}>
                    <i className="icon-user"></i> Profile
                  </button>
                  <button className="btn btn-danger" onClick={logout}>
                    <i className="icon-logout"></i> Logout
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Message Display */}
      {message && (
        <div className={`message-banner ${getMessageClass()}`}>
          {message}
        </div>
      )}

      {/* Statistics Dashboard */}
      <div className="stats-dashboard">
        <div className="stats-grid">
          <div className="stat-card primary">
            <div className="stat-icon">👥</div>
            <div className="stat-content">
              <h3>Total Employees</h3>
              <div className="stat-value">{allEmployees.length}</div>
              <div className="stat-label">Under Management</div>
            </div>
          </div>
          <div className="stat-card success">
            <div className="stat-icon">📄</div>
            <div className="stat-content">
              <h3>Total Bills</h3>
              <div className="stat-value">{statistics.total_bills || 0}</div>
              <div className="stat-label">All Submissions</div>
            </div>
          </div>
          <div className="stat-card warning">
            <div className="stat-icon">⏳</div>
            <div className="stat-content">
              <h3>Pending Approval</h3>
              <div className="stat-value">{pendingBills.length}</div>
              <div className="stat-label">Awaiting Review</div>
            </div>
          </div>
          <div className="stat-card info">
            <div className="stat-icon">💰</div>
            <div className="stat-content">
              <h3>Total Amount</h3>
              <div className="stat-value">{formatCurrency(statistics.total_amount || 0)}</div>
              <div className="stat-label">All Bills</div>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="manager-tabs">
        <button 
          className={`tab ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => handleTabChange('overview')}
        >
          <i className="icon-users"></i> Employee Overview
        </button>
        <button 
          className={`tab ${activeTab === 'employees' ? 'active' : ''}`}
          onClick={() => handleTabChange('employees')}
        >
          <i className="icon-list"></i> All Employees
        </button>
        <button 
          className={`tab ${activeTab === 'pending' ? 'active' : ''}`}
          onClick={() => handleTabChange('pending')}
        >
          <i className="icon-clock"></i> Pending Bills ({pendingBills.length})
        </button>
        <button 
          className={`tab ${activeTab === 'trip-approvals' ? 'active' : ''}`}
          onClick={() => handleTabChange('trip-approvals')}
        >
          <i className="icon-plane"></i> Trip Approvals
        </button>
        <button 
          className={`tab ${activeTab === 'trip-submissions' ? 'active' : ''}`}
          onClick={() => handleTabChange('trip-submissions')}
        >
          <i className="icon-briefcase"></i> Trip Submissions
        </button>
      </div>

      {/* Tab Content */}
      <div className="tab-content">
        {/* Employee Overview Tab */}
        {activeTab === 'overview' && (
          <div className="overview-section">
            <div className="section-header">
              <h2>Team Overview</h2>
              <p>Your direct reports and their activity summary</p>
            </div>
            
            {employees.length > 0 ? (
              <div className="employee-grid">
                {employees.map((employee) => (
                  <div key={employee.id} className="employee-card modern">
                    <div className="employee-avatar">
                      <div className="avatar-circle">
                        {(employee.name || employee.username || 'U').charAt(0).toUpperCase()}
                      </div>
                    </div>
                    <div className="employee-info">
                      <h4 className="employee-name">{employee.name || employee.username}</h4>
                      <p className="employee-email">{employee.email}</p>
                      <p className="employee-department">{employee.department}</p>
                    </div>
                    <div className="employee-stats">
                      <div className="stat-item">
                        <span className="stat-number">{employee.total_bills || 0}</span>
                        <span className="stat-label">Bills</span>
                      </div>
                      <div className="stat-item">
                        <span className="stat-number">{employee.pending_bills || 0}</span>
                        <span className="stat-label">Pending</span>
                      </div>
                      <div className="stat-item">
                        <span className="stat-number">{formatCurrency(employee.total_amount || 0)}</span>
                        <span className="stat-label">Total</span>
                      </div>
                    </div>
                    <div className="employee-actions">
                      <button 
                        className="btn btn-primary btn-sm"
                        onClick={() => handleEmployeeSelect(employee)}
                      >
                        View Details
                      </button>
                    </div>
                    <div className="employee-meta">
                      <small>Joined: {formatDate(employee.registration_date)}</small>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="empty-state">
                <div className="empty-icon">👥</div>
                <h3>No Team Members</h3>
                <p>No employees are currently assigned to your management.</p>
              </div>
            )}
          </div>
        )}

        {/* All Employees Tab */}
        {activeTab === 'employees' && (
          <div className="employees-section">
            <div className="section-header">
              <h2>All Registered Employees</h2>
              <p>Complete list of all employees in the system</p>
            </div>

            {/* Search and Filter Controls */}
            <div className="controls-bar">
              <div className="search-box">
                <input
                  type="text"
                  placeholder="Search employees by name, username, or email..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="search-input"
                />
                <i className="icon-search"></i>
              </div>
              <div className="filter-box">
                <select
                  value={departmentFilter}
                  onChange={(e) => setDepartmentFilter(e.target.value)}
                  className="filter-select"
                >
                  <option value="">All Departments</option>
                  {departments.map(dept => (
                    <option key={dept} value={dept}>{dept}</option>
                  ))}
                </select>
              </div>
            </div>

            {/* Employee List */}
            {filteredEmployees.length > 0 ? (
              <div className="employee-table">
                <div className="table-header">
                  <div className="col-avatar"></div>
                  <div className="col-name">Name</div>
                  <div className="col-email">Email</div>
                  <div className="col-department">Department</div>
                  <div className="col-joined">Joined</div>
                  <div className="col-bills">Bills</div>
                  <div className="col-actions">Actions</div>
                </div>
                <div className="table-body">
                  {filteredEmployees.map((employee) => (
                    <div key={employee.id} className="table-row">
                      <div className="col-avatar">
                        <div className="avatar-small">
                          {(employee.name || employee.username || 'U').charAt(0).toUpperCase()}
                        </div>
                      </div>
                      <div className="col-name">
                        <div className="name-info">
                          <span className="full-name">{employee.name || 'N/A'}</span>
                          <span className="username">@{employee.username}</span>
                        </div>
                      </div>
                      <div className="col-email">{employee.email}</div>
                      <div className="col-department">
                        <span className="department-badge">{employee.department || 'N/A'}</span>
                      </div>
                      <div className="col-joined">{formatDate(employee.registration_date)}</div>
                      <div className="col-bills">
                        <div className="bill-summary">
                          <span className="total-bills">{employee.total_bills || 0}</span>
                          {employee.pending_bills > 0 && (
                            <span className="pending-indicator">({employee.pending_bills} pending)</span>
                          )}
                        </div>
                      </div>
                      <div className="col-actions">
                        <button 
                          className="btn btn-sm btn-outline"
                          onClick={() => handleEmployeeSelect(employee)}
                        >
                          View
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="empty-state">
                <div className="empty-icon">🔍</div>
                <h3>No Employees Found</h3>
                <p>No employees match your search criteria.</p>
              </div>
            )}
          </div>
        )}

        {/* Pending Bills Tab */}
        {activeTab === 'pending' && (
          <div className="pending-section">
            <div className="section-header">
              <h2>Pending Bills for Approval</h2>
              <p>Bills awaiting your review and approval</p>
            </div>

            {pendingBills.length > 0 ? (
              <div className="bills-list">
                {pendingBills.map((bill) => (
                  <div key={bill.id} className="bill-card pending">
                    <div className="bill-header">
                      <div className="bill-info">
                        <h4>Bill #{bill.id}</h4>
                        <p className="employee-info">
                          {bill.employee_name} ({bill.employee_email})
                        </p>
                        <p className="bill-amount">{formatCurrency(bill.amount)}</p>
                      </div>
                      <div className="bill-actions">
                        <button 
                          className="btn btn-success btn-sm"
                          onClick={() => approveBill(bill.id)}
                        >
                          ✓ Approve
                        </button>
                        <button 
                          className="btn btn-danger btn-sm"
                          onClick={() => rejectBill(bill.id)}
                        >
                          ✗ Reject
                        </button>
                      </div>
                    </div>
                    <div className="bill-details">
                      <div className="detail-grid">
                        <div><strong>Date:</strong> {formatDate(bill.date)}</div>
                        <div><strong>Vendor:</strong> {bill.vendor || 'N/A'}</div>
                        <div><strong>Category:</strong> {bill.category || 'N/A'}</div>
                        <div><strong>Submitted:</strong> {formatDate(bill.created_at)}</div>
                      </div>
                      {bill.remarks && (
                        <div className="bill-remarks">
                          <strong>Remarks:</strong> {bill.remarks}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="empty-state">
                <div className="empty-icon">✅</div>
                <h3>No Pending Bills</h3>
                <p>All bills have been reviewed. Great job!</p>
              </div>
            )}
          </div>
        )}

        {/* Trip Approvals Tab */}
        {activeTab === 'trip-approvals' && (
          <ManagerTripApprovals />
        )}

        {/* Trip Submissions Tab */}
        {activeTab === 'trip-submissions' && (
          <TripSubmissionsDashboard />
        )}
      </div>

      {/* Employee Detail Modal */}
      {showEmployeeModal && selectedEmployee && (
        <div className="modal-overlay" onClick={closeEmployeeModal}>
          <div className="modal-content employee-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Employee Details</h3>
              <button className="modal-close" onClick={closeEmployeeModal}>×</button>
            </div>
            <div className="modal-body">
              <div className="employee-detail-header">
                <div className="employee-avatar-large">
                  {(selectedEmployee.name || selectedEmployee.username || 'U').charAt(0).toUpperCase()}
                </div>
                <div className="employee-detail-info">
                  <h4>{selectedEmployee.name || selectedEmployee.username}</h4>
                  <p>{selectedEmployee.email}</p>
                  <p>{selectedEmployee.department}</p>
                  <p>Joined: {formatDate(selectedEmployee.registration_date)}</p>
                </div>
              </div>
              
              <div className="employee-stats-detail">
                <div className="stat-card-small">
                  <span className="stat-value">{selectedEmployee.total_bills || 0}</span>
                  <span className="stat-label">Total Bills</span>
                </div>
                <div className="stat-card-small">
                  <span className="stat-value">{selectedEmployee.pending_bills || 0}</span>
                  <span className="stat-label">Pending</span>
                </div>
                <div className="stat-card-small">
                  <span className="stat-value">{selectedEmployee.approved_bills || 0}</span>
                  <span className="stat-label">Approved</span>
                </div>
                <div className="stat-card-small">
                  <span className="stat-value">{formatCurrency(selectedEmployee.total_amount || 0)}</span>
                  <span className="stat-label">Total Amount</span>
                </div>
              </div>

              <div className="employee-bills-section">
                <h5>Recent Bills</h5>
                {employeeBills.length > 0 ? (
                  <div className="bills-mini-list">
                    {employeeBills.slice(0, 5).map((bill) => (
                      <div key={bill.id} className="bill-mini-item">
                        <div className="bill-mini-info">
                          <span className="bill-id">#{bill.id}</span>
                          <span className="bill-amount">{formatCurrency(bill.amount)}</span>
                        </div>
                        <div className="bill-mini-meta">
                          <span className="bill-date">{formatDate(bill.date)}</span>
                          <span className={`bill-status status-${bill.status}`}>{bill.status}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p>No bills submitted yet.</p>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default ManagerDashboardNew;