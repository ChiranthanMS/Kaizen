from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, date, timedelta
from database import db_manager
import logging

logger = logging.getLogger(__name__)

class AnalyticsService:
    """Service for generating analytics and reports on expense data"""
    
    def __init__(self):
        pass

    async def get_expense_trends(self, employee_id: Optional[int] = None, 
                               days: int = 30) -> Dict[str, Any]:
        """Get expense trends over time"""
        try:
            end_date = date.today()
            start_date = end_date - timedelta(days=days)
            
            if employee_id:
                query = """
                SELECT 
                    DATE(created_at) as expense_date,
                    COUNT(*) as bill_count,
                    SUM(amount) as total_amount,
                    AVG(amount) as avg_amount
                FROM app_bills 
                WHERE employee_id = $1 
                AND DATE(created_at) >= $2 
                AND DATE(created_at) <= $3
                GROUP BY DATE(created_at)
                ORDER BY expense_date
                """
                results = await db_manager.execute_query(query, employee_id, start_date, end_date)
            else:
                query = """
                SELECT 
                    DATE(created_at) as expense_date,
                    COUNT(*) as bill_count,
                    SUM(amount) as total_amount,
                    AVG(amount) as avg_amount
                FROM app_bills 
                WHERE DATE(created_at) >= $1 
                AND DATE(created_at) <= $2
                GROUP BY DATE(created_at)
                ORDER BY expense_date
                """
                results = await db_manager.execute_query(query, start_date, end_date)
            
            return {
                "period": f"{start_date} to {end_date}",
                "trends": results,
                "summary": {
                    "total_days": len(results),
                    "total_bills": sum(r['bill_count'] for r in results),
                    "total_amount": sum(r['total_amount'] or 0 for r in results),
                    "avg_daily_amount": sum(r['total_amount'] or 0 for r in results) / max(len(results), 1)
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting expense trends: {str(e)}")
            return {"error": str(e)}

    async def get_category_breakdown(self, employee_id: Optional[int] = None,
                                   days: int = 30) -> Dict[str, Any]:
        """Get breakdown of expenses by category"""
        try:
            end_date = date.today()
            start_date = end_date - timedelta(days=days)
            
            if employee_id:
                query = """
                SELECT 
                    category,
                    COUNT(*) as bill_count,
                    SUM(amount) as total_amount,
                    AVG(amount) as avg_amount,
                    MIN(amount) as min_amount,
                    MAX(amount) as max_amount
                FROM app_bills 
                WHERE employee_id = $1 
                AND DATE(created_at) >= $2 
                AND DATE(created_at) <= $3
                AND category IS NOT NULL
                GROUP BY category
                ORDER BY total_amount DESC
                """
                results = await db_manager.execute_query(query, employee_id, start_date, end_date)
            else:
                query = """
                SELECT 
                    category,
                    COUNT(*) as bill_count,
                    SUM(amount) as total_amount,
                    AVG(amount) as avg_amount,
                    MIN(amount) as min_amount,
                    MAX(amount) as max_amount
                FROM app_bills 
                WHERE DATE(created_at) >= $1 
                AND DATE(created_at) <= $2
                AND category IS NOT NULL
                GROUP BY category
                ORDER BY total_amount DESC
                """
                results = await db_manager.execute_query(query, start_date, end_date)
            
            total_amount = sum(r['total_amount'] or 0 for r in results)
            
            # Add percentage to each category
            for result in results:
                result['percentage'] = (result['total_amount'] / total_amount * 100) if total_amount > 0 else 0
            
            return {
                "period": f"{start_date} to {end_date}",
                "categories": results,
                "summary": {
                    "total_categories": len(results),
                    "total_amount": total_amount,
                    "top_category": results[0]['category'] if results else None
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting category breakdown: {str(e)}")
            return {"error": str(e)}

    async def get_employee_rankings(self, manager_id: int, days: int = 30) -> Dict[str, Any]:
        """Get employee expense rankings for a manager"""
        try:
            end_date = date.today()
            start_date = end_date - timedelta(days=days)
            
            query = """
            SELECT 
                u.id as employee_id,
                u.full_name as employee_name,
                u.email as employee_email,
                u.department,
                COUNT(b.id) as bill_count,
                SUM(b.amount) as total_amount,
                AVG(b.amount) as avg_amount,
                COUNT(CASE WHEN b.status = 'approved' THEN 1 END) as approved_count,
                COUNT(CASE WHEN b.status = 'pending' THEN 1 END) as pending_count,
                COUNT(CASE WHEN b.status = 'rejected' THEN 1 END) as rejected_count
            FROM app_users u
            LEFT JOIN app_bills b ON u.id = b.employee_id 
                AND DATE(b.created_at) >= $2 
                AND DATE(b.created_at) <= $3
            WHERE u.manager_id = $1 AND u.role = 'employee'
            GROUP BY u.id, u.full_name, u.email, u.department
            ORDER BY total_amount DESC
            """
            
            results = await db_manager.execute_query(query, manager_id, start_date, end_date)
            
            # Add rankings
            for i, result in enumerate(results, 1):
                result['rank'] = i
                result['approval_rate'] = (
                    result['approved_count'] / max(result['bill_count'], 1) * 100
                ) if result['bill_count'] > 0 else 0
            
            return {
                "period": f"{start_date} to {end_date}",
                "rankings": results,
                "summary": {
                    "total_employees": len(results),
                    "total_bills": sum(r['bill_count'] for r in results),
                    "total_amount": sum(r['total_amount'] or 0 for r in results),
                    "top_spender": results[0] if results else None
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting employee rankings: {str(e)}")
            return {"error": str(e)}

    async def get_approval_metrics(self, manager_id: Optional[int] = None,
                                 days: int = 30) -> Dict[str, Any]:
        """Get approval/rejection metrics"""
        try:
            end_date = date.today()
            start_date = end_date - timedelta(days=days)
            
            if manager_id:
                query = """
                SELECT 
                    b.status,
                    COUNT(*) as count,
                    SUM(b.amount) as total_amount,
                    AVG(b.amount) as avg_amount
                FROM app_bills b
                JOIN app_users u ON b.employee_id = u.id
                WHERE u.manager_id = $1
                AND DATE(b.created_at) >= $2 
                AND DATE(b.created_at) <= $3
                GROUP BY b.status
                """
                results = await db_manager.execute_query(query, manager_id, start_date, end_date)
            else:
                query = """
                SELECT 
                    status,
                    COUNT(*) as count,
                    SUM(amount) as total_amount,
                    AVG(amount) as avg_amount
                FROM app_bills 
                WHERE DATE(created_at) >= $1 
                AND DATE(created_at) <= $2
                GROUP BY status
                """
                results = await db_manager.execute_query(query, start_date, end_date)
            
            total_bills = sum(r['count'] for r in results)
            
            # Calculate percentages
            metrics = {}
            for result in results:
                metrics[result['status']] = {
                    "count": result['count'],
                    "total_amount": result['total_amount'] or 0,
                    "avg_amount": result['avg_amount'] or 0,
                    "percentage": (result['count'] / total_bills * 100) if total_bills > 0 else 0
                }
            
            return {
                "period": f"{start_date} to {end_date}",
                "metrics": metrics,
                "summary": {
                    "total_bills": total_bills,
                    "approval_rate": metrics.get('approved', {}).get('percentage', 0),
                    "rejection_rate": metrics.get('rejected', {}).get('percentage', 0),
                    "pending_rate": metrics.get('pending', {}).get('percentage', 0)
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting approval metrics: {str(e)}")
            return {"error": str(e)}

    async def get_monthly_summary(self, employee_id: Optional[int] = None,
                                months: int = 6) -> Dict[str, Any]:
        """Get monthly expense summary"""
        try:
            if employee_id:
                query = """
                SELECT 
                    DATE_TRUNC('month', created_at) as month,
                    COUNT(*) as bill_count,
                    SUM(amount) as total_amount,
                    AVG(amount) as avg_amount,
                    COUNT(CASE WHEN status = 'approved' THEN 1 END) as approved_count,
                    COUNT(CASE WHEN status = 'rejected' THEN 1 END) as rejected_count
                FROM bills 
                WHERE employee_id = $1
                AND created_at >= CURRENT_DATE - INTERVAL '%s months'
                GROUP BY DATE_TRUNC('month', created_at)
                ORDER BY month DESC
                """ % months
                results = await db_manager.execute_query(query, employee_id)
            else:
                query = """
                SELECT 
                    DATE_TRUNC('month', created_at) as month,
                    COUNT(*) as bill_count,
                    SUM(amount) as total_amount,
                    AVG(amount) as avg_amount,
                    COUNT(CASE WHEN status = 'approved' THEN 1 END) as approved_count,
                    COUNT(CASE WHEN status = 'rejected' THEN 1 END) as rejected_count
                FROM bills 
                WHERE created_at >= CURRENT_DATE - INTERVAL '%s months'
                GROUP BY DATE_TRUNC('month', created_at)
                ORDER BY month DESC
                """ % months
                results = await db_manager.execute_query(query)
            
            # Format month names
            for result in results:
                if result['month']:
                    result['month_name'] = result['month'].strftime('%B %Y')
                    result['approval_rate'] = (
                        result['approved_count'] / max(result['bill_count'], 1) * 100
                    ) if result['bill_count'] > 0 else 0
            
            return {
                "months": results,
                "summary": {
                    "total_months": len(results),
                    "total_bills": sum(r['bill_count'] for r in results),
                    "total_amount": sum(r['total_amount'] or 0 for r in results),
                    "avg_monthly_amount": sum(r['total_amount'] or 0 for r in results) / max(len(results), 1)
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting monthly summary: {str(e)}")
            return {"error": str(e)}

    async def get_expense_anomalies(self, employee_id: Optional[int] = None,
                                  threshold_multiplier: float = 2.0) -> Dict[str, Any]:
        """Detect expense anomalies (unusually high amounts)"""
        try:
            # First, get average and standard deviation
            if employee_id:
                stats_query = """
                SELECT 
                    AVG(amount) as avg_amount,
                    STDDEV(amount) as stddev_amount
                FROM app_bills 
                WHERE employee_id = $1 AND amount > 0
                """
                stats = await db_manager.fetch_one(stats_query, employee_id)
            else:
                stats_query = """
                SELECT 
                    AVG(amount) as avg_amount,
                    STDDEV(amount) as stddev_amount
                FROM app_bills 
                WHERE amount > 0
                """
                stats = await db_manager.fetch_one(stats_query)
            
            if not stats or not stats['avg_amount']:
                return {"anomalies": [], "summary": {"threshold": 0, "count": 0}}
            
            avg_amount = float(stats['avg_amount'])
            stddev_amount = float(stats['stddev_amount'] or 0)
            threshold = avg_amount + (threshold_multiplier * stddev_amount)
            
            # Find anomalies
            if employee_id:
                anomaly_query = """
                SELECT 
                    b.id,
                    b.amount,
                    b.date,
                    b.vendor,
                    b.category,
                    b.created_at,
                    u.full_name as employee_name
                FROM app_bills b
                JOIN app_users u ON b.employee_id = u.id
                WHERE b.employee_id = $1 AND b.amount > $2
                ORDER BY b.amount DESC
                """
                anomalies = await db_manager.execute_query(anomaly_query, employee_id, threshold)
            else:
                anomaly_query = """
                SELECT 
                    b.id,
                    b.amount,
                    b.date,
                    b.vendor,
                    b.category,
                    b.created_at,
                    u.full_name as employee_name
                FROM app_bills b
                JOIN app_users u ON b.employee_id = u.id
                WHERE b.amount > $1
                ORDER BY b.amount DESC
                """
                anomalies = await db_manager.execute_query(anomaly_query, threshold)
            
            # Add deviation info
            for anomaly in anomalies:
                anomaly['deviation_from_avg'] = anomaly['amount'] - avg_amount
                anomaly['deviation_percentage'] = (
                    (anomaly['amount'] - avg_amount) / avg_amount * 100
                ) if avg_amount > 0 else 0
            
            return {
                "anomalies": anomalies,
                "summary": {
                    "threshold": threshold,
                    "count": len(anomalies),
                    "avg_amount": avg_amount,
                    "stddev_amount": stddev_amount,
                    "threshold_multiplier": threshold_multiplier
                }
            }
            
        except Exception as e:
            logger.error(f"Error detecting anomalies: {str(e)}")
            return {"error": str(e)}

# Global analytics service instance
analytics_service = AnalyticsService()