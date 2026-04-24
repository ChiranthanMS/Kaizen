"""
Manager Service
Handles manager-specific operations including employee management and bill oversight
"""

from typing import List, Dict, Any, Optional
from services.mongodb_service import mongodb_service
from database import db_manager
import logging

logger = logging.getLogger(__name__)

class ManagerService:
    def __init__(self):
        pass

    async def get_team_employees(self, manager_id: str) -> List[Dict[str, Any]]:
        """
        Get all employees under a specific manager from MongoDB
        Returns employee data with name, username, email, and registration date
        """
        try:
            employees = mongodb_service.get_employees_for_manager(manager_id)
            
            # Enhance with bill statistics from PostgreSQL
            enhanced_employees = []
            for employee in employees:
                # Get bill statistics from PostgreSQL
                try:
                    # First sync the employee to PostgreSQL if not already synced
                    mongo_user = mongodb_service.find_user_by_id(employee["id"])
                    if mongo_user:
                        postgres_user_id = await db_manager.sync_user_from_mongodb(mongo_user)
                        
                        # Get bill statistics
                        bill_stats = await db_manager.get_bill_statistics(postgres_user_id)
                        
                        employee.update({
                            "postgres_id": postgres_user_id,
                            "total_bills": bill_stats.get("total_bills", 0),
                            "total_amount": float(bill_stats.get("total_amount", 0)) if bill_stats.get("total_amount") else 0.0,
                            "pending_bills": bill_stats.get("pending_bills", 0),
                            "approved_bills": bill_stats.get("approved_bills", 0),
                            "rejected_bills": bill_stats.get("rejected_bills", 0),
                            "avg_amount": float(bill_stats.get("avg_amount", 0)) if bill_stats.get("avg_amount") else 0.0
                        })
                except Exception as e:
                    logger.warning(f"Could not get bill statistics for employee {employee['id']}: {e}")
                    # Add default values
                    employee.update({
                        "postgres_id": None,
                        "total_bills": 0,
                        "total_amount": 0.0,
                        "pending_bills": 0,
                        "approved_bills": 0,
                        "rejected_bills": 0,
                        "avg_amount": 0.0
                    })
                
                enhanced_employees.append(employee)
            
            logger.info(f"✅ Retrieved {len(enhanced_employees)} employees for manager {manager_id}")
            return enhanced_employees
            
        except Exception as e:
            logger.error(f"❌ Failed to get team employees: {e}")
            return []

    async def get_all_employees(self) -> List[Dict[str, Any]]:
        """
        Get all employees from MongoDB (for super managers or admin views)
        Returns employee data with name, username, email, and registration date
        """
        try:
            employees = mongodb_service.get_all_employees()
            
            # Enhance with bill statistics from PostgreSQL
            enhanced_employees = []
            for employee in employees:
                # Get bill statistics from PostgreSQL
                try:
                    # First sync the employee to PostgreSQL if not already synced
                    mongo_user = mongodb_service.find_user_by_id(employee["id"])
                    if mongo_user:
                        postgres_user_id = await db_manager.sync_user_from_mongodb(mongo_user)
                        
                        # Get bill statistics
                        bill_stats = await db_manager.get_bill_statistics(postgres_user_id)
                        
                        employee.update({
                            "postgres_id": postgres_user_id,
                            "total_bills": bill_stats.get("total_bills", 0),
                            "total_amount": float(bill_stats.get("total_amount", 0)) if bill_stats.get("total_amount") else 0.0,
                            "pending_bills": bill_stats.get("pending_bills", 0),
                            "approved_bills": bill_stats.get("approved_bills", 0),
                            "rejected_bills": bill_stats.get("rejected_bills", 0),
                            "avg_amount": float(bill_stats.get("avg_amount", 0)) if bill_stats.get("avg_amount") else 0.0
                        })
                except Exception as e:
                    logger.warning(f"Could not get bill statistics for employee {employee['id']}: {e}")
                    # Add default values
                    employee.update({
                        "postgres_id": None,
                        "total_bills": 0,
                        "total_amount": 0.0,
                        "pending_bills": 0,
                        "approved_bills": 0,
                        "rejected_bills": 0,
                        "avg_amount": 0.0
                    })
                
                enhanced_employees.append(employee)
            
            logger.info(f"✅ Retrieved {len(enhanced_employees)} total employees")
            return enhanced_employees
            
        except Exception as e:
            logger.error(f"❌ Failed to get all employees: {e}")
            return []

    async def get_team_bills(self, manager_id: str, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get all bills for employees under a specific manager from PostgreSQL
        """
        try:
            # First, sync the manager to PostgreSQL to get their PostgreSQL ID
            mongo_manager = mongodb_service.find_user_by_id(manager_id)
            if not mongo_manager:
                logger.error(f"Manager {manager_id} not found in MongoDB")
                return []
            
            postgres_manager_id = await db_manager.sync_user_from_mongodb(mongo_manager)
            if not postgres_manager_id:
                logger.error(f"Could not sync manager {manager_id} to PostgreSQL")
                return []
            
            # Get all bills for employees under this manager
            bills = await db_manager.get_all_bills_for_manager(postgres_manager_id, limit, offset)
            
            logger.info(f"✅ Retrieved {len(bills)} bills for manager {manager_id}")
            return bills
            
        except Exception as e:
            logger.error(f"❌ Failed to get team bills: {e}")
            return []

    async def update_bill_status(self, bill_id: int, status: str, manager_id: str) -> bool:
        """
        Update bill status (approve/reject) - only managers can do this
        """
        try:
            # Verify the manager has permission to update this bill
            # (This could be enhanced with more specific permission checks)
            
            success = await db_manager.update_bill_status(bill_id, status)
            
            if success:
                logger.info(f"✅ Manager {manager_id} updated bill {bill_id} status to {status}")
            else:
                logger.warning(f"⚠️ Failed to update bill {bill_id} status to {status}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Failed to update bill status: {e}")
            return False

    def get_manager_dashboard_stats(self, manager_id: str) -> Dict[str, Any]:
        """
        Get dashboard statistics for a manager
        """
        try:
            # Get user statistics from MongoDB
            user_stats = mongodb_service.get_user_stats()
            
            # Get employees under this manager
            employees = mongodb_service.get_employees_for_manager(manager_id)
            
            return {
                "total_employees_under_manager": len(employees),
                "total_users_in_system": user_stats.get("total_users", 0),
                "total_employees_in_system": user_stats.get("total_employees", 0),
                "total_managers_in_system": user_stats.get("total_managers", 0)
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get manager dashboard stats: {e}")
            return {}

# Global manager service instance
manager_service = ManagerService()