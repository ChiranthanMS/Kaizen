from fastapi import APIRouter, HTTPException, Depends, Query
from models.user_models import TokenData
from dependencies.auth_dependencies import get_current_user, get_current_manager, get_current_employee
from services.analytics_service import analytics_service
import logging
from typing import Optional

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["Analytics & Reporting"])

@router.get("/expense-trends")
async def get_expense_trends(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Get expense trends over time.
    Employees see their own trends, managers see team trends.
    """
    try:
        if current_user.role == "employee":
            employee_id = int(current_user.user_id)
        else:
            employee_id = None  # Managers see all trends
        
        trends = await analytics_service.get_expense_trends(employee_id, days)
        return trends
        
    except Exception as e:
        logger.error(f"Error getting expense trends: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get expense trends: {str(e)}"
        )

@router.get("/category-breakdown")
async def get_category_breakdown(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Get breakdown of expenses by category.
    Employees see their own breakdown, managers see team breakdown.
    """
    try:
        if current_user.role == "employee":
            employee_id = int(current_user.user_id)
        else:
            employee_id = None  # Managers see all categories
        
        breakdown = await analytics_service.get_category_breakdown(employee_id, days)
        return breakdown
        
    except Exception as e:
        logger.error(f"Error getting category breakdown: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get category breakdown: {str(e)}"
        )

@router.get("/employee-rankings")
async def get_employee_rankings(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    current_user: TokenData = Depends(get_current_manager)
):
    """
    Get employee expense rankings.
    Only managers can access this endpoint.
    """
    try:
        rankings = await analytics_service.get_employee_rankings(int(current_user.user_id), days)
        return rankings
        
    except Exception as e:
        logger.error(f"Error getting employee rankings: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get employee rankings: {str(e)}"
        )

@router.get("/approval-metrics")
async def get_approval_metrics(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    current_user: TokenData = Depends(get_current_manager)
):
    """
    Get approval/rejection metrics.
    Only managers can access this endpoint.
    """
    try:
        metrics = await analytics_service.get_approval_metrics(int(current_user.user_id), days)
        return metrics
        
    except Exception as e:
        logger.error(f"Error getting approval metrics: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get approval metrics: {str(e)}"
        )

@router.get("/monthly-summary")
async def get_monthly_summary(
    months: int = Query(6, ge=1, le=24, description="Number of months to analyze"),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Get monthly expense summary.
    Employees see their own summary, managers see team summary.
    """
    try:
        if current_user.role == "employee":
            employee_id = int(current_user.user_id)
        else:
            employee_id = None  # Managers see all data
        
        summary = await analytics_service.get_monthly_summary(employee_id, months)
        return summary
        
    except Exception as e:
        logger.error(f"Error getting monthly summary: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get monthly summary: {str(e)}"
        )

@router.get("/anomalies")
async def get_expense_anomalies(
    threshold: float = Query(2.0, ge=1.0, le=5.0, description="Standard deviation multiplier for anomaly detection"),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Detect expense anomalies (unusually high amounts).
    Employees see their own anomalies, managers see team anomalies.
    """
    try:
        if current_user.role == "employee":
            employee_id = int(current_user.user_id)
        else:
            employee_id = None  # Managers see all anomalies
        
        anomalies = await analytics_service.get_expense_anomalies(employee_id, threshold)
        return anomalies
        
    except Exception as e:
        logger.error(f"Error detecting anomalies: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to detect anomalies: {str(e)}"
        )

@router.get("/dashboard-summary")
async def get_dashboard_summary(
    current_user: TokenData = Depends(get_current_user)
):
    """
    Get comprehensive dashboard summary combining multiple analytics.
    """
    try:
        if current_user.role == "employee":
            employee_id = int(current_user.user_id)
            
            # Get employee-specific analytics
            trends = await analytics_service.get_expense_trends(employee_id, 30)
            categories = await analytics_service.get_category_breakdown(employee_id, 30)
            monthly = await analytics_service.get_monthly_summary(employee_id, 6)
            anomalies = await analytics_service.get_expense_anomalies(employee_id, 2.0)
            
            return {
                "user_role": "employee",
                "trends": trends,
                "categories": categories,
                "monthly_summary": monthly,
                "anomalies": anomalies
            }
        else:
            # Manager dashboard
            manager_id = int(current_user.user_id)
            
            trends = await analytics_service.get_expense_trends(None, 30)
            categories = await analytics_service.get_category_breakdown(None, 30)
            rankings = await analytics_service.get_employee_rankings(manager_id, 30)
            metrics = await analytics_service.get_approval_metrics(manager_id, 30)
            monthly = await analytics_service.get_monthly_summary(None, 6)
            
            return {
                "user_role": "manager",
                "trends": trends,
                "categories": categories,
                "employee_rankings": rankings,
                "approval_metrics": metrics,
                "monthly_summary": monthly
            }
        
    except Exception as e:
        logger.error(f"Error getting dashboard summary: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get dashboard summary: {str(e)}"
        )

@router.get("/health")
async def analytics_health_check(current_user: TokenData = Depends(get_current_user)):
    """Health check endpoint for analytics service"""
    try:
        return {
            "status": "healthy",
            "service": "Analytics & Reporting",
            "user": current_user.email,
            "role": current_user.role,
            "available_endpoints": [
                "/analytics/expense-trends",
                "/analytics/category-breakdown", 
                "/analytics/monthly-summary",
                "/analytics/anomalies",
                "/analytics/dashboard-summary"
            ],
            "manager_only_endpoints": [
                "/analytics/employee-rankings",
                "/analytics/approval-metrics"
            ] if current_user.role == "manager" else [],
            "features": [
                "Expense trend analysis",
                "Category breakdown",
                "Monthly summaries", 
                "Anomaly detection",
                "Employee rankings (managers only)",
                "Approval metrics (managers only)"
            ]
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "Analytics & Reporting",
            "error": str(e)
        }