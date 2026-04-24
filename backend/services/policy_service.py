from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, date
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class PolicyViolationType(str, Enum):
    AMOUNT_EXCEEDED = "amount_exceeded"
    INVALID_CATEGORY = "invalid_category"
    MISSING_RECEIPT = "missing_receipt"
    DUPLICATE_SUBMISSION = "duplicate_submission"
    INVALID_DATE = "invalid_date"
    INSUFFICIENT_DOCUMENTATION = "insufficient_documentation"

class PolicySeverity(str, Enum):
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class PolicyViolation:
    def __init__(self, violation_type: PolicyViolationType, severity: PolicySeverity, 
                 message: str, field: Optional[str] = None, suggested_action: Optional[str] = None):
        self.violation_type = violation_type
        self.severity = severity
        self.message = message
        self.field = field
        self.suggested_action = suggested_action
        self.timestamp = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "violation_type": self.violation_type.value,
            "severity": self.severity.value,
            "message": self.message,
            "field": self.field,
            "suggested_action": self.suggested_action,
            "timestamp": self.timestamp.isoformat()
        }

class ExpensePolicy:
    """Base class for expense policies"""
    
    def __init__(self, name: str, description: str, enabled: bool = True):
        self.name = name
        self.description = description
        self.enabled = enabled

    def validate(self, bill_data: Dict[str, Any], user_data: Dict[str, Any]) -> List[PolicyViolation]:
        """Override this method in subclasses to implement specific policy validation"""
        return []

class AmountLimitPolicy(ExpensePolicy):
    """Policy to check if expense amount exceeds limits"""
    
    def __init__(self, daily_limit: float = 500.0, monthly_limit: float = 5000.0, 
                 single_transaction_limit: float = 1000.0):
        super().__init__(
            name="Amount Limit Policy",
            description="Validates expense amounts against daily, monthly, and single transaction limits"
        )
        self.daily_limit = daily_limit
        self.monthly_limit = monthly_limit
        self.single_transaction_limit = single_transaction_limit

    def validate(self, bill_data: Dict[str, Any], user_data: Dict[str, Any]) -> List[PolicyViolation]:
        violations = []
        amount = bill_data.get('amount', 0)
        
        # Single transaction limit check
        if amount > self.single_transaction_limit:
            violations.append(PolicyViolation(
                violation_type=PolicyViolationType.AMOUNT_EXCEEDED,
                severity=PolicySeverity.ERROR,
                message=f"Amount ${amount:.2f} exceeds single transaction limit of ${self.single_transaction_limit:.2f}",
                field="amount",
                suggested_action="Split into multiple transactions or get manager approval"
            ))
        
        # Daily limit check (would require database query to check other bills for the same day)
        # This is a placeholder - in real implementation, you'd query the database
        
        return violations

class CategoryPolicy(ExpensePolicy):
    """Policy to validate expense categories"""
    
    def __init__(self, allowed_categories: List[str] = None, 
                 category_limits: Dict[str, float] = None):
        super().__init__(
            name="Category Policy",
            description="Validates expense categories and category-specific limits"
        )
        self.allowed_categories = allowed_categories or [
            "food", "transport", "lodging", "fuel", "entertainment", 
            "office_supplies", "communication", "medical", "miscellaneous"
        ]
        self.category_limits = category_limits or {
            "entertainment": 200.0,
            "food": 100.0,
            "miscellaneous": 50.0
        }

    def validate(self, bill_data: Dict[str, Any], user_data: Dict[str, Any]) -> List[PolicyViolation]:
        violations = []
        category = bill_data.get('category', '').lower()
        amount = bill_data.get('amount', 0)
        
        # Check if category is allowed
        if category and category not in self.allowed_categories:
            violations.append(PolicyViolation(
                violation_type=PolicyViolationType.INVALID_CATEGORY,
                severity=PolicySeverity.WARNING,
                message=f"Category '{category}' is not in the approved list",
                field="category",
                suggested_action=f"Use one of: {', '.join(self.allowed_categories)}"
            ))
        
        # Check category-specific limits
        if category in self.category_limits and amount > self.category_limits[category]:
            violations.append(PolicyViolation(
                violation_type=PolicyViolationType.AMOUNT_EXCEEDED,
                severity=PolicySeverity.WARNING,
                message=f"Amount ${amount:.2f} exceeds limit for category '{category}' (${self.category_limits[category]:.2f})",
                field="amount",
                suggested_action="Reduce amount or change category"
            ))
        
        return violations

class DatePolicy(ExpensePolicy):
    """Policy to validate expense dates"""
    
    def __init__(self, max_days_old: int = 30, allow_future_dates: bool = False):
        super().__init__(
            name="Date Policy",
            description="Validates expense dates for reasonable timeframes"
        )
        self.max_days_old = max_days_old
        self.allow_future_dates = allow_future_dates

    def validate(self, bill_data: Dict[str, Any], user_data: Dict[str, Any]) -> List[PolicyViolation]:
        violations = []
        expense_date = bill_data.get('date')
        
        if not expense_date:
            violations.append(PolicyViolation(
                violation_type=PolicyViolationType.INVALID_DATE,
                severity=PolicySeverity.WARNING,
                message="Expense date is missing",
                field="date",
                suggested_action="Provide a valid expense date"
            ))
            return violations
        
        # Convert string date to date object if needed
        if isinstance(expense_date, str):
            try:
                expense_date = datetime.strptime(expense_date, '%Y-%m-%d').date()
            except ValueError:
                violations.append(PolicyViolation(
                    violation_type=PolicyViolationType.INVALID_DATE,
                    severity=PolicySeverity.ERROR,
                    message="Invalid date format. Use YYYY-MM-DD",
                    field="date",
                    suggested_action="Correct the date format"
                ))
                return violations
        
        today = date.today()
        days_diff = (today - expense_date).days
        
        # Check if date is too old
        if days_diff > self.max_days_old:
            violations.append(PolicyViolation(
                violation_type=PolicyViolationType.INVALID_DATE,
                severity=PolicySeverity.WARNING,
                message=f"Expense date is {days_diff} days old (limit: {self.max_days_old} days)",
                field="date",
                suggested_action="Submit expenses within the allowed timeframe"
            ))
        
        # Check if date is in the future
        if days_diff < 0 and not self.allow_future_dates:
            violations.append(PolicyViolation(
                violation_type=PolicyViolationType.INVALID_DATE,
                severity=PolicySeverity.ERROR,
                message="Future dates are not allowed",
                field="date",
                suggested_action="Use current or past dates only"
            ))
        
        return violations

class PolicyService:
    """Service to manage and execute expense policies"""
    
    def __init__(self):
        self.policies: List[ExpensePolicy] = []
        self._initialize_default_policies()

    def _initialize_default_policies(self):
        """Initialize default policies"""
        self.policies = [
            AmountLimitPolicy(),
            CategoryPolicy(),
            DatePolicy()
        ]

    def add_policy(self, policy: ExpensePolicy):
        """Add a custom policy"""
        self.policies.append(policy)

    def remove_policy(self, policy_name: str):
        """Remove a policy by name"""
        self.policies = [p for p in self.policies if p.name != policy_name]

    def validate_expense(self, bill_data: Dict[str, Any], user_data: Dict[str, Any]) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Validate an expense against all active policies
        
        Returns:
            Tuple of (is_valid, violations_list)
        """
        all_violations = []
        
        for policy in self.policies:
            if not policy.enabled:
                continue
                
            try:
                violations = policy.validate(bill_data, user_data)
                all_violations.extend(violations)
            except Exception as e:
                logger.error(f"Error executing policy {policy.name}: {str(e)}")
                # Add a system violation
                all_violations.append(PolicyViolation(
                    violation_type=PolicyViolationType.INSUFFICIENT_DOCUMENTATION,
                    severity=PolicySeverity.WARNING,
                    message=f"Policy validation error: {policy.name}",
                    suggested_action="Contact system administrator"
                ))
        
        # Convert violations to dictionaries
        violation_dicts = [v.to_dict() for v in all_violations]
        
        # Determine if expense is valid (no critical errors)
        has_critical_errors = any(v.severity == PolicySeverity.CRITICAL for v in all_violations)
        has_errors = any(v.severity == PolicySeverity.ERROR for v in all_violations)
        
        is_valid = not (has_critical_errors or has_errors)
        
        return is_valid, violation_dicts

    def get_policy_summary(self) -> Dict[str, Any]:
        """Get summary of all policies"""
        return {
            "total_policies": len(self.policies),
            "active_policies": len([p for p in self.policies if p.enabled]),
            "policies": [
                {
                    "name": p.name,
                    "description": p.description,
                    "enabled": p.enabled
                }
                for p in self.policies
            ]
        }

# Global policy service instance
policy_service = PolicyService()