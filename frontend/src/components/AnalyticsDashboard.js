import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  Chart as ChartJS, 
  CategoryScale, 
  LinearScale, 
  PointElement, 
  LineElement, 
  BarElement,
  ArcElement,
  Title, 
  Tooltip, 
  Legend 
} from 'chart.js';
import { Line, Bar, Doughnut } from 'react-chartjs-2';
import './AnalyticsDashboard.css';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
);

const AnalyticsDashboard = () => {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchMetrics();
  }, []);

  const fetchMetrics = async () => {
    try {
      setLoading(true);
      const token = sessionStorage.getItem('token');
      const response = await axios.get('/analytics/dashboard-summary', {
        headers: { 
          Authorization: `Bearer ${token}`,
          'Cache-Control': 'no-cache',
          'Pragma': 'no-cache'
        }
      });
      setMetrics(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load analytics.');
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="loading-container"><div className="loading-spinner"></div><p>Loading Analytics...</p></div>;
  if (error) return <div className="error-message">{error}</div>;
  if (!metrics) return null;

  // Prepare chart data
  const trendsData = {
    labels: metrics.trends?.trends?.map(t => t.expense_date) || [],
    datasets: [{
      label: 'Daily Expenses',
      data: metrics.trends?.trends?.map(t => t.total_amount) || [],
      borderColor: '#00e5ff',
      backgroundColor: 'rgba(0, 229, 255, 0.2)',
      tension: 0.4
    }]
  };

  const categoriesData = {
    labels: metrics.categories?.categories?.map(c => c.category) || [],
    datasets: [{
      label: 'Expenses by Category',
      data: metrics.categories?.categories?.map(c => c.total_amount) || [],
      backgroundColor: [
        '#00e5ff', '#7c4dff', '#ff1744', '#00e676', '#ffea00'
      ],
      borderWidth: 0
    }]
  };

  const approvalData = metrics.approval_metrics ? {
    labels: Object.keys(metrics.approval_metrics.metrics || {}).map(k => k.toUpperCase()),
    datasets: [{
      label: 'Claims Status',
      data: Object.values(metrics.approval_metrics.metrics || {}).map(m => m.count),
      backgroundColor: ['#00e676', '#ffc107', '#ff1744'],
      borderWidth: 0
    }]
  } : null;

  const chartOptions = {
    responsive: true,
    plugins: {
      legend: { labels: { color: '#fff' } },
    },
    scales: {
      y: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.1)' } },
      x: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.1)' } }
    }
  };

  return (
    <div className="analytics-dashboard">
      <h2 className="dashboard-title">System Analytics & Reporting</h2>
      
      <div className="summary-cards">
        <div className="stat-card glass-card">
          <h4>Total Claims</h4>
          <p className="stat-value">{metrics.trends?.summary?.total_bills || 0}</p>
        </div>
        <div className="stat-card glass-card">
          <h4>Total Amount</h4>
          <p className="stat-value">₹{(metrics.trends?.summary?.total_amount || 0).toLocaleString()}</p>
        </div>
        {metrics.approval_metrics && (
          <>
            <div className="stat-card glass-card">
              <h4>Approval Rate</h4>
              <p className="stat-value">{metrics.approval_metrics.summary?.approval_rate?.toFixed(1) || 0}%</p>
            </div>
            <div className="stat-card glass-card">
              <h4>Rejection Rate (Fraud/Policy)</h4>
              <p className="stat-value text-danger">{metrics.approval_metrics.summary?.rejection_rate?.toFixed(1) || 0}%</p>
            </div>
          </>
        )}
      </div>

      <div className="charts-grid">
        <div className="chart-container glass-card">
          <h3>Expense Trends (30 Days)</h3>
          <div className="chart-wrapper">
            <Line data={trendsData} options={chartOptions} />
          </div>
        </div>

        <div className="chart-container glass-card">
          <h3>Category Breakdown</h3>
          <div className="chart-wrapper doughnut-wrapper">
            <Doughnut data={categoriesData} options={{...chartOptions, scales: {}}} />
          </div>
        </div>
        
        {approvalData && (
          <div className="chart-container glass-card">
            <h3>Approval vs Rejection</h3>
            <div className="chart-wrapper doughnut-wrapper">
              <Bar data={approvalData} options={chartOptions} />
            </div>
          </div>
        )}
      </div>
      
      {metrics.anomalies?.anomalies?.length > 0 && (
        <div className="anomalies-section glass-card">
          <h3>Detected Anomalies (Fraud Alerts)</h3>
          <table className="data-table">
            <thead>
              <tr>
                <th>Date</th>
                <th>Employee</th>
                <th>Amount</th>
                <th>Category</th>
                <th>Deviation</th>
              </tr>
            </thead>
            <tbody>
              {metrics.anomalies.anomalies.map(a => (
                <tr key={a.id}>
                  <td>{a.date}</td>
                  <td>{a.employee_name}</td>
                  <td className="text-danger">₹{a.amount}</td>
                  <td>{a.category}</td>
                  <td>+{a.deviation_percentage.toFixed(1)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default AnalyticsDashboard;
