"""
Trip-based Budget Management Service

This service manages budget allocation for official company trips only.
Employees get budget allocations only when they are on approved company work/travel.
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, date, timedelta
from decimal import Decimal
import uuid

from models.budget_models import (
    EmployeeDesignation, CityTier, ExpenseType, OfficialTrip, TripStatus,
    TripRequest, TripApproval, ActiveTripSession, TripBudgetValidationResult,
    BudgetCap, CityMapping
)
from utils import clean_decimal

logger = logging.getLogger(__name__)

class TripBudgetService:
    """Service for managing trip-based budget allocations"""
    
    def __init__(self):
        # In-memory storage for demo (in production, use database)
        self.official_trips: Dict[str, OfficialTrip] = {}
        self.active_trip_sessions: Dict[str, ActiveTripSession] = {}
        self.is_loaded = False
        
        # Budget matrix - daily rates for different designations and city tiers
        self.daily_budget_matrix = self._initialize_budget_matrix()
        
        # City tier mappings
        self.city_mappings = self._initialize_city_mappings()
    
    def _initialize_budget_matrix(self) -> Dict[str, Dict[str, Dict[str, Decimal]]]:
        """Initialize the budget matrix with daily rates"""
        return {
            # Intern budgets
            EmployeeDesignation.INTERN.value: {
                CityTier.TIER_1.value: {
                    ExpenseType.TRAVEL.value: Decimal('2000'),
                    ExpenseType.HOTEL.value: Decimal('3000'),
                    ExpenseType.FOOD.value: Decimal('800'),
                    ExpenseType.LOCAL_TRANSPORT.value: Decimal('500'),
                    ExpenseType.MISCELLANEOUS.value: Decimal('300')
                },
                CityTier.TIER_2.value: {
                    ExpenseType.TRAVEL.value: Decimal('1500'),
                    ExpenseType.HOTEL.value: Decimal('2000'),
                    ExpenseType.FOOD.value: Decimal('600'),
                    ExpenseType.LOCAL_TRANSPORT.value: Decimal('400'),
                    ExpenseType.MISCELLANEOUS.value: Decimal('200')
                },
                CityTier.TIER_3.value: {
                    ExpenseType.TRAVEL.value: Decimal('1000'),
                    ExpenseType.HOTEL.value: Decimal('1500'),
                    ExpenseType.FOOD.value: Decimal('500'),
                    ExpenseType.LOCAL_TRANSPORT.value: Decimal('300'),
                    ExpenseType.MISCELLANEOUS.value: Decimal('200')
                }
            },
            # Associate budgets
            EmployeeDesignation.ASSOCIATE.value: {
                CityTier.TIER_1.value: {
                    ExpenseType.TRAVEL.value: Decimal('3000'),
                    ExpenseType.HOTEL.value: Decimal('4000'),
                    ExpenseType.FOOD.value: Decimal('1200'),
                    ExpenseType.LOCAL_TRANSPORT.value: Decimal('700'),
                    ExpenseType.MISCELLANEOUS.value: Decimal('500')
                },
                CityTier.TIER_2.value: {
                    ExpenseType.TRAVEL.value: Decimal('2500'),
                    ExpenseType.HOTEL.value: Decimal('3000'),
                    ExpenseType.FOOD.value: Decimal('900'),
                    ExpenseType.LOCAL_TRANSPORT.value: Decimal('600'),
                    ExpenseType.MISCELLANEOUS.value: Decimal('400')
                },
                CityTier.TIER_3.value: {
                    ExpenseType.TRAVEL.value: Decimal('2000'),
                    ExpenseType.HOTEL.value: Decimal('2500'),
                    ExpenseType.FOOD.value: Decimal('700'),
                    ExpenseType.LOCAL_TRANSPORT.value: Decimal('500'),
                    ExpenseType.MISCELLANEOUS.value: Decimal('300')
                }
            },
            # Senior Associate budgets
            EmployeeDesignation.SENIOR_ASSOCIATE.value: {
                CityTier.TIER_1.value: {
                    ExpenseType.TRAVEL.value: Decimal('4000'),
                    ExpenseType.HOTEL.value: Decimal('5000'),
                    ExpenseType.FOOD.value: Decimal('1500'),
                    ExpenseType.LOCAL_TRANSPORT.value: Decimal('800'),
                    ExpenseType.MISCELLANEOUS.value: Decimal('700')
                },
                CityTier.TIER_2.value: {
                    ExpenseType.TRAVEL.value: Decimal('3500'),
                    ExpenseType.HOTEL.value: Decimal('4000'),
                    ExpenseType.FOOD.value: Decimal('1200'),
                    ExpenseType.LOCAL_TRANSPORT.value: Decimal('700'),
                    ExpenseType.MISCELLANEOUS.value: Decimal('600')
                },
                CityTier.TIER_3.value: {
                    ExpenseType.TRAVEL.value: Decimal('3000'),
                    ExpenseType.HOTEL.value: Decimal('3500'),
                    ExpenseType.FOOD.value: Decimal('1000'),
                    ExpenseType.LOCAL_TRANSPORT.value: Decimal('600'),
                    ExpenseType.MISCELLANEOUS.value: Decimal('500')
                }
            },
            # Manager budgets
            EmployeeDesignation.MANAGER.value: {
                CityTier.TIER_1.value: {
                    ExpenseType.TRAVEL.value: Decimal('6000'),
                    ExpenseType.HOTEL.value: Decimal('7000'),
                    ExpenseType.FOOD.value: Decimal('2000'),
                    ExpenseType.LOCAL_TRANSPORT.value: Decimal('1000'),
                    ExpenseType.MISCELLANEOUS.value: Decimal('1000')
                },
                CityTier.TIER_2.value: {
                    ExpenseType.TRAVEL.value: Decimal('5000'),
                    ExpenseType.HOTEL.value: Decimal('6000'),
                    ExpenseType.FOOD.value: Decimal('1600'),
                    ExpenseType.LOCAL_TRANSPORT.value: Decimal('800'),
                    ExpenseType.MISCELLANEOUS.value: Decimal('800')
                },
                CityTier.TIER_3.value: {
                    ExpenseType.TRAVEL.value: Decimal('4000'),
                    ExpenseType.HOTEL.value: Decimal('5000'),
                    ExpenseType.FOOD.value: Decimal('1400'),
                    ExpenseType.LOCAL_TRANSPORT.value: Decimal('700'),
                    ExpenseType.MISCELLANEOUS.value: Decimal('700')
                }
            },
            # Senior Manager budgets
            EmployeeDesignation.SENIOR_MANAGER.value: {
                CityTier.TIER_1.value: {
                    ExpenseType.TRAVEL.value: Decimal('8000'),
                    ExpenseType.HOTEL.value: Decimal('10000'),
                    ExpenseType.FOOD.value: Decimal('2500'),
                    ExpenseType.LOCAL_TRANSPORT.value: Decimal('1200'),
                    ExpenseType.MISCELLANEOUS.value: Decimal('1300')
                },
                CityTier.TIER_2.value: {
                    ExpenseType.TRAVEL.value: Decimal('7000'),
                    ExpenseType.HOTEL.value: Decimal('8000'),
                    ExpenseType.FOOD.value: Decimal('2000'),
                    ExpenseType.LOCAL_TRANSPORT.value: Decimal('1000'),
                    ExpenseType.MISCELLANEOUS.value: Decimal('1000')
                },
                CityTier.TIER_3.value: {
                    ExpenseType.TRAVEL.value: Decimal('6000'),
                    ExpenseType.HOTEL.value: Decimal('7000'),
                    ExpenseType.FOOD.value: Decimal('1800'),
                    ExpenseType.LOCAL_TRANSPORT.value: Decimal('900'),
                    ExpenseType.MISCELLANEOUS.value: Decimal('900')
                }
            },
            # Director budgets
            EmployeeDesignation.DIRECTOR.value: {
                CityTier.TIER_1.value: {
                    ExpenseType.TRAVEL.value: Decimal('12000'),
                    ExpenseType.HOTEL.value: Decimal('15000'),
                    ExpenseType.FOOD.value: Decimal('3000'),
                    ExpenseType.LOCAL_TRANSPORT.value: Decimal('1500'),
                    ExpenseType.MISCELLANEOUS.value: Decimal('2000')
                },
                CityTier.TIER_2.value: {
                    ExpenseType.TRAVEL.value: Decimal('10000'),
                    ExpenseType.HOTEL.value: Decimal('12000'),
                    ExpenseType.FOOD.value: Decimal('2500'),
                    ExpenseType.LOCAL_TRANSPORT.value: Decimal('1200'),
                    ExpenseType.MISCELLANEOUS.value: Decimal('1500')
                },
                CityTier.TIER_3.value: {
                    ExpenseType.TRAVEL.value: Decimal('8000'),
                    ExpenseType.HOTEL.value: Decimal('10000'),
                    ExpenseType.FOOD.value: Decimal('2200'),
                    ExpenseType.LOCAL_TRANSPORT.value: Decimal('1000'),
                    ExpenseType.MISCELLANEOUS.value: Decimal('1300')
                }
            },
            # Senior Director budgets
            EmployeeDesignation.SENIOR_DIRECTOR.value: {
                CityTier.TIER_1.value: {
                    ExpenseType.TRAVEL.value: Decimal('15000'),
                    ExpenseType.HOTEL.value: Decimal('20000'),
                    ExpenseType.FOOD.value: Decimal('4000'),
                    ExpenseType.LOCAL_TRANSPORT.value: Decimal('2000'),
                    ExpenseType.MISCELLANEOUS.value: Decimal('3000')
                },
                CityTier.TIER_2.value: {
                    ExpenseType.TRAVEL.value: Decimal('12000'),
                    ExpenseType.HOTEL.value: Decimal('15000'),
                    ExpenseType.FOOD.value: Decimal('3000'),
                    ExpenseType.LOCAL_TRANSPORT.value: Decimal('1500'),
                    ExpenseType.MISCELLANEOUS.value: Decimal('2000')
                },
                CityTier.TIER_3.value: {
                    ExpenseType.TRAVEL.value: Decimal('10000'),
                    ExpenseType.HOTEL.value: Decimal('12000'),
                    ExpenseType.FOOD.value: Decimal('2500'),
                    ExpenseType.LOCAL_TRANSPORT.value: Decimal('1200'),
                    ExpenseType.MISCELLANEOUS.value: Decimal('1500')
                }
            },
            # VP budgets
            EmployeeDesignation.VP.value: {
                CityTier.TIER_1.value: {
                    ExpenseType.TRAVEL.value: Decimal('20000'),
                    ExpenseType.HOTEL.value: Decimal('25000'),
                    ExpenseType.FOOD.value: Decimal('5000'),
                    ExpenseType.LOCAL_TRANSPORT.value: Decimal('2500'),
                    ExpenseType.MISCELLANEOUS.value: Decimal('5000')
                },
                CityTier.TIER_2.value: {
                    ExpenseType.TRAVEL.value: Decimal('18000'),
                    ExpenseType.HOTEL.value: Decimal('22000'),
                    ExpenseType.FOOD.value: Decimal('4000'),
                    ExpenseType.LOCAL_TRANSPORT.value: Decimal('2000'),
                    ExpenseType.MISCELLANEOUS.value: Decimal('3000')
                },
                CityTier.TIER_3.value: {
                    ExpenseType.TRAVEL.value: Decimal('15000'),
                    ExpenseType.HOTEL.value: Decimal('20000'),
                    ExpenseType.FOOD.value: Decimal('3500'),
                    ExpenseType.LOCAL_TRANSPORT.value: Decimal('1800'),
                    ExpenseType.MISCELLANEOUS.value: Decimal('2500')
                }
            },
            # SVP budgets
            EmployeeDesignation.SVP.value: {
                CityTier.TIER_1.value: {
                    ExpenseType.TRAVEL.value: Decimal('25000'),
                    ExpenseType.HOTEL.value: Decimal('35000'),
                    ExpenseType.FOOD.value: Decimal('6000'),
                    ExpenseType.LOCAL_TRANSPORT.value: Decimal('3000'),
                    ExpenseType.MISCELLANEOUS.value: Decimal('6000')
                },
                CityTier.TIER_2.value: {
                    ExpenseType.TRAVEL.value: Decimal('22000'),
                    ExpenseType.HOTEL.value: Decimal('30000'),
                    ExpenseType.FOOD.value: Decimal('5000'),
                    ExpenseType.LOCAL_TRANSPORT.value: Decimal('2500'),
                    ExpenseType.MISCELLANEOUS.value: Decimal('4000')
                },
                CityTier.TIER_3.value: {
                    ExpenseType.TRAVEL.value: Decimal('20000'),
                    ExpenseType.HOTEL.value: Decimal('25000'),
                    ExpenseType.FOOD.value: Decimal('4000'),
                    ExpenseType.LOCAL_TRANSPORT.value: Decimal('2000'),
                    ExpenseType.MISCELLANEOUS.value: Decimal('3000')
                }
            }
        }
    
    def _initialize_city_mappings(self) -> Dict[str, CityMapping]:
        """Initialize city to tier mappings"""
        cities = {
            # Tier 1 cities
            "mumbai": CityMapping(city_name="Mumbai", city_tier=CityTier.TIER_1, state="Maharashtra", region="West"),
            "delhi": CityMapping(city_name="Delhi", city_tier=CityTier.TIER_1, state="Delhi", region="North"),
            "bangalore": CityMapping(city_name="Bangalore", city_tier=CityTier.TIER_1, state="Karnataka", region="South"),
            "chennai": CityMapping(city_name="Chennai", city_tier=CityTier.TIER_1, state="Tamil Nadu", region="South"),
            "hyderabad": CityMapping(city_name="Hyderabad", city_tier=CityTier.TIER_1, state="Telangana", region="South"),
            "pune": CityMapping(city_name="Pune", city_tier=CityTier.TIER_1, state="Maharashtra", region="West"),
            "kolkata": CityMapping(city_name="Kolkata", city_tier=CityTier.TIER_1, state="West Bengal", region="East"),
            
            # Tier 2 cities
            "ahmedabad": CityMapping(city_name="Ahmedabad", city_tier=CityTier.TIER_2, state="Gujarat", region="West"),
            "surat": CityMapping(city_name="Surat", city_tier=CityTier.TIER_2, state="Gujarat", region="West"),
            "jaipur": CityMapping(city_name="Jaipur", city_tier=CityTier.TIER_2, state="Rajasthan", region="North"),
            "lucknow": CityMapping(city_name="Lucknow", city_tier=CityTier.TIER_2, state="Uttar Pradesh", region="North"),
            "kanpur": CityMapping(city_name="Kanpur", city_tier=CityTier.TIER_2, state="Uttar Pradesh", region="North"),
            "nagpur": CityMapping(city_name="Nagpur", city_tier=CityTier.TIER_2, state="Maharashtra", region="Central"),
            "indore": CityMapping(city_name="Indore", city_tier=CityTier.TIER_2, state="Madhya Pradesh", region="Central"),
            "thane": CityMapping(city_name="Thane", city_tier=CityTier.TIER_2, state="Maharashtra", region="West"),
            "bhopal": CityMapping(city_name="Bhopal", city_tier=CityTier.TIER_2, state="Madhya Pradesh", region="Central"),
            "visakhapatnam": CityMapping(city_name="Visakhapatnam", city_tier=CityTier.TIER_2, state="Andhra Pradesh", region="South"),
            "pimpri": CityMapping(city_name="Pimpri-Chinchwad", city_tier=CityTier.TIER_2, state="Maharashtra", region="West"),
            "patna": CityMapping(city_name="Patna", city_tier=CityTier.TIER_2, state="Bihar", region="East"),
            "vadodara": CityMapping(city_name="Vadodara", city_tier=CityTier.TIER_2, state="Gujarat", region="West"),
            "ghaziabad": CityMapping(city_name="Ghaziabad", city_tier=CityTier.TIER_2, state="Uttar Pradesh", region="North"),
            "ludhiana": CityMapping(city_name="Ludhiana", city_tier=CityTier.TIER_2, state="Punjab", region="North"),
            "agra": CityMapping(city_name="Agra", city_tier=CityTier.TIER_2, state="Uttar Pradesh", region="North"),
            "nashik": CityMapping(city_name="Nashik", city_tier=CityTier.TIER_2, state="Maharashtra", region="West"),
            "faridabad": CityMapping(city_name="Faridabad", city_tier=CityTier.TIER_2, state="Haryana", region="North"),
            "meerut": CityMapping(city_name="Meerut", city_tier=CityTier.TIER_2, state="Uttar Pradesh", region="North"),
            "rajkot": CityMapping(city_name="Rajkot", city_tier=CityTier.TIER_2, state="Gujarat", region="West"),
            "kalyan": CityMapping(city_name="Kalyan-Dombivali", city_tier=CityTier.TIER_2, state="Maharashtra", region="West"),
            "vasai": CityMapping(city_name="Vasai-Virar", city_tier=CityTier.TIER_2, state="Maharashtra", region="West"),
            "varanasi": CityMapping(city_name="Varanasi", city_tier=CityTier.TIER_2, state="Uttar Pradesh", region="North"),
            "srinagar": CityMapping(city_name="Srinagar", city_tier=CityTier.TIER_2, state="Jammu and Kashmir", region="North"),
            "aurangabad": CityMapping(city_name="Aurangabad", city_tier=CityTier.TIER_2, state="Maharashtra", region="West"),
            "dhanbad": CityMapping(city_name="Dhanbad", city_tier=CityTier.TIER_2, state="Jharkhand", region="East"),
            "amritsar": CityMapping(city_name="Amritsar", city_tier=CityTier.TIER_2, state="Punjab", region="North"),
            "navi mumbai": CityMapping(city_name="Navi Mumbai", city_tier=CityTier.TIER_2, state="Maharashtra", region="West"),
            "allahabad": CityMapping(city_name="Allahabad", city_tier=CityTier.TIER_2, state="Uttar Pradesh", region="North"),
            "ranchi": CityMapping(city_name="Ranchi", city_tier=CityTier.TIER_2, state="Jharkhand", region="East"),
            "howrah": CityMapping(city_name="Howrah", city_tier=CityTier.TIER_2, state="West Bengal", region="East"),
            "coimbatore": CityMapping(city_name="Coimbatore", city_tier=CityTier.TIER_2, state="Tamil Nadu", region="South"),
            "jabalpur": CityMapping(city_name="Jabalpur", city_tier=CityTier.TIER_2, state="Madhya Pradesh", region="Central"),
            "gwalior": CityMapping(city_name="Gwalior", city_tier=CityTier.TIER_2, state="Madhya Pradesh", region="Central"),
        }
        
        return cities
    
    def get_city_tier(self, city_name: str) -> CityTier:
        """Get city tier for a given city"""
        city_key = city_name.lower().strip()
        
        if city_key in self.city_mappings:
            return self.city_mappings[city_key].city_tier
        
        logger.warning(f"City '{city_name}' not found in mappings, defaulting to Tier 3")
        return CityTier.TIER_3
    
    def get_designation_from_string(self, designation_str: str) -> EmployeeDesignation:
        """Convert designation string to enum"""
        designation_map = {
            "intern": EmployeeDesignation.INTERN,
            "associate": EmployeeDesignation.ASSOCIATE,
            "senior associate": EmployeeDesignation.SENIOR_ASSOCIATE,
            "senior_associate": EmployeeDesignation.SENIOR_ASSOCIATE,
            "manager": EmployeeDesignation.MANAGER,
            "senior manager": EmployeeDesignation.SENIOR_MANAGER,
            "senior_manager": EmployeeDesignation.SENIOR_MANAGER,
            "director": EmployeeDesignation.DIRECTOR,
            "senior director": EmployeeDesignation.SENIOR_DIRECTOR,
            "senior_director": EmployeeDesignation.SENIOR_DIRECTOR,
            "vp": EmployeeDesignation.VP,
            "vice president": EmployeeDesignation.VP,
            "svp": EmployeeDesignation.SVP,
            "senior vice president": EmployeeDesignation.SVP,
        }
        
        key = designation_str.lower().strip()
        return designation_map.get(key, EmployeeDesignation.ASSOCIATE)
    
    def calculate_trip_budget(
        self, 
        designation: EmployeeDesignation, 
        destination_city: str, 
        duration_days: int
    ) -> Dict[str, Decimal]:
        """Calculate total budget allocation for a trip"""
        
        city_tier = self.get_city_tier(destination_city)
        daily_rates = self.daily_budget_matrix[designation.value][city_tier.value]
        
        trip_budget = {}
        for expense_type, daily_rate in daily_rates.items():
            trip_budget[expense_type] = daily_rate * duration_days
        
        return trip_budget
    
    async def create_trip_request(
        self,
        employee_id: str,
        employee_name: str,
        designation: EmployeeDesignation,
        trip_purpose: str,
        destination_city: str,
        start_date: date,
        end_date: date
    ) -> OfficialTrip:
        """Create a new trip request"""
        
        # Calculate trip duration
        duration_days = (end_date - start_date).days + 1
        
        # Get destination city tier
        destination_tier = self.get_city_tier(destination_city)
        
        # Calculate budget allocation
        allocated_budget = self.calculate_trip_budget(designation, destination_city, duration_days)
        total_allocated = sum(allocated_budget.values())
        
        # Generate trip ID
        trip_id = f"{employee_id}_{start_date.strftime('%Y%m%d')}_{uuid.uuid4().hex[:8]}"
        
        # Create trip object
        trip = OfficialTrip(
            trip_id=trip_id,
            employee_id=employee_id,
            employee_name=employee_name,
            designation=designation,
            trip_purpose=trip_purpose,
            destination_city=destination_city,
            destination_tier=destination_tier,
            start_date=start_date,
            end_date=end_date,
            duration_days=duration_days,
            allocated_budget=allocated_budget,
            total_allocated=total_allocated,
            remaining_budget=total_allocated,
            status=TripStatus.PENDING
        )
        
        # Store trip in memory
        self.official_trips[trip_id] = trip
        
        # Store pending trip in PostgreSQL database
        try:
            from database import db_manager
            
            # Get employee PostgreSQL ID
            from services.mongodb_service import mongodb_service
            employee_mongo_user = mongodb_service.find_user_by_id(employee_id)
            employee_pg_id = None
            if employee_mongo_user:
                pg_user = await db_manager.get_user_by_email(employee_mongo_user.get('email'))
                employee_pg_id = pg_user['id'] if pg_user else None
            
            if employee_pg_id:
                pending_trip_data = {
                    'trip_id': trip_id,
                    'employee_id': employee_pg_id,
                    'employee_name': employee_name,
                    'trip_purpose': trip_purpose,
                    'destination_city': destination_city,
                    'start_date': start_date,
                    'end_date': end_date,
                    'duration_days': duration_days,
                    'designation': designation.value,
                    'city_tier': destination_tier.value,
                    'allocated_budget': float(total_allocated),
                    'total_bills': 0,
                    'total_amount': 0,
                    'budget_utilization': 0,
                    'trip_status': 'pending',
                    'submission_status': 'not_submitted'
                }
                await db_manager.create_completed_trip(pending_trip_data)
                logger.info(f"Persisted pending trip {trip_id} to database")
        except Exception as e:
            logger.warning(f"Failed to persist pending trip {trip_id} to database: {e}")
        
        logger.info(f"Created trip request {trip_id} for employee {employee_id}")
        return trip
    
    async def approve_trip(
        self,
        trip_id: str,
        approved_by: str,
        budget_adjustments: Optional[Dict[str, Decimal]] = None
    ) -> OfficialTrip:
        """Approve a trip request"""
        
        if trip_id not in self.official_trips:
            raise ValueError(f"Trip {trip_id} not found")
        
        trip = self.official_trips[trip_id]
        
        # Apply budget adjustments if provided
        if budget_adjustments:
            for expense_type, adjustment in budget_adjustments.items():
                if expense_type in trip.allocated_budget:
                    trip.allocated_budget[expense_type] = adjustment
            
            # Recalculate totals
            trip.total_allocated = sum(trip.allocated_budget.values())
            trip.remaining_budget = trip.total_allocated - trip.expenses_submitted
        
        # Update trip status
        trip.status = TripStatus.APPROVED
        trip.approved_by = approved_by
        trip.approved_at = datetime.utcnow()
        trip.updated_at = datetime.utcnow()
        
        # Store approved trip in PostgreSQL database
        try:
            from database import db_manager
            
            # Get employee PostgreSQL ID
            from services.mongodb_service import mongodb_service
            employee_mongo_user = mongodb_service.find_user_by_id(trip.employee_id)
            if employee_mongo_user:
                employee_pg_user = await db_manager.get_user_by_email(employee_mongo_user.get('email'))
                if employee_pg_user:
                    # Get manager PostgreSQL ID
                    manager_mongo_user = mongodb_service.find_user_by_id(approved_by)
                    manager_pg_id = None
                    if manager_mongo_user:
                        manager_pg_user = await db_manager.get_user_by_email(manager_mongo_user.get('email'))
                        if manager_pg_user:
                            manager_pg_id = manager_pg_user['id']
                    
                    # Create completed trip record
                    completed_trip_data = {
                        'trip_id': trip.trip_id,
                        'employee_id': employee_pg_user['id'],
                        'employee_name': trip.employee_name,
                        'trip_purpose': trip.trip_purpose,
                        'destination_city': trip.destination_city,
                        'start_date': trip.start_date,
                        'end_date': trip.end_date,
                        'duration_days': trip.duration_days,
                        'designation': trip.designation.value if trip.designation else 'Associate',
                        'city_tier': trip.destination_tier.value if trip.destination_tier else 'Tier 2',
                        'allocated_budget': float(trip.total_allocated),
                        'total_bills': 0,
                        'total_amount': 0.0,
                        'budget_utilization': 0.0,
                        'trip_status': 'approved',
                        'submission_status': 'not_submitted',
                        'manager_id': manager_pg_id,
                        'approved_by': manager_pg_id,
                        'approved_at': trip.approved_at
                    }
                    
                    await db_manager.create_completed_trip(completed_trip_data)
                    logger.info(f"Stored approved trip {trip_id} in PostgreSQL database")
        except Exception as e:
            logger.warning(f"Failed to store approved trip in PostgreSQL: {e}")
            # Don't fail the approval if database storage fails
        
        logger.info(f"Trip {trip_id} approved by {approved_by}")
        return trip
    
    def reject_trip(
        self,
        trip_id: str,
        rejected_by: str,
        rejection_reason: str
    ) -> OfficialTrip:
        """Reject a trip request"""
        
        if trip_id not in self.official_trips:
            raise ValueError(f"Trip {trip_id} not found")
        
        trip = self.official_trips[trip_id]
        
        # Update trip status
        trip.status = TripStatus.REJECTED
        trip.rejected_by = rejected_by
        trip.rejected_at = datetime.utcnow()
        trip.rejection_reason = rejection_reason
        trip.updated_at = datetime.utcnow()
        
        logger.info(f"Trip {trip_id} rejected by {rejected_by}: {rejection_reason}")
        return trip
    
    def activate_trip(self, trip_id: str) -> ActiveTripSession:
        """Activate a trip for expense submission"""
        
        if trip_id not in self.official_trips:
            raise ValueError(f"Trip {trip_id} not found")
        
        trip = self.official_trips[trip_id]
        
        if trip.status != TripStatus.APPROVED:
            raise ValueError(f"Trip {trip_id} is not approved")
        
        # Check if trip is within date range
        today = date.today()
        if today < trip.start_date or today > trip.end_date:
            logger.warning(f"Trip {trip_id} is not within active date range")
        
        # Create active session
        session = ActiveTripSession(
            trip_id=trip_id,
            employee_id=trip.employee_id,
            designation=trip.designation,
            destination_tier=trip.destination_tier,
            allocated_budgets=trip.allocated_budget.copy(),
            used_budgets={expense_type: Decimal('0') for expense_type in trip.allocated_budget.keys()},
            remaining_budgets=trip.allocated_budget.copy(),
            trip_start=trip.start_date,
            trip_end=trip.end_date,
            is_active=True
        )
        
        # Store active session
        self.active_trip_sessions[trip.employee_id] = session
        
        # Update trip status
        trip.status = TripStatus.ACTIVE
        trip.updated_at = datetime.utcnow()
        
        logger.info(f"Activated trip {trip_id} for employee {trip.employee_id}")
        return session
    
    def get_active_trip_session(self, employee_id: str) -> Optional[ActiveTripSession]:
        """Get active trip session for an employee"""
        return self.active_trip_sessions.get(employee_id)
    
    def validate_trip_expense(
        self,
        employee_id: str,
        expense_type: ExpenseType,
        amount: Decimal
    ) -> TripBudgetValidationResult:
        """Validate an expense against active trip budget"""
        
        session = self.get_active_trip_session(employee_id)
        
        if not session:
            return TripBudgetValidationResult(
                is_within_budget=False,
                expense_type=expense_type,
                amount=amount,
                trip_id="",
                allocated_budget=Decimal('0'),
                used_budget=Decimal('0'),
                remaining_budget=Decimal('0'),
                warning_message="No active trip found. Expenses can only be submitted during approved company trips.",
                recommendation="Please ensure you have an approved and active trip before submitting expenses."
            )
        
        expense_type_str = expense_type.value
        allocated = session.allocated_budgets.get(expense_type_str, Decimal('0'))
        used = session.used_budgets.get(expense_type_str, Decimal('0'))
        remaining = session.remaining_budgets.get(expense_type_str, Decimal('0'))
        
        # Check if expense is within budget
        is_within_budget = amount <= remaining
        
        # Prepare validation result
        result = TripBudgetValidationResult(
            is_within_budget=is_within_budget,
            expense_type=expense_type,
            amount=amount,
            trip_id=session.trip_id,
            allocated_budget=allocated,
            used_budget=used,
            remaining_budget=remaining
        )
        
        if not is_within_budget:
            excess_amount = amount - remaining
            result.warning_message = f"Expense exceeds remaining trip budget by ₹{excess_amount:.2f}"
            result.recommendation = "Consider reducing the expense amount or seek manager approval for budget increase"
        elif remaining - amount < allocated * Decimal('0.2'):  # Less than 20% remaining
            result.warning_message = f"Trip budget running low. Only ₹{remaining - amount:.2f} will remain after this expense"
            result.recommendation = "Monitor remaining expenses carefully for the rest of the trip"
        
        return result
    
    def record_trip_expense(
        self,
        employee_id: str,
        expense_type: ExpenseType,
        amount: Decimal
    ) -> bool:
        """Record an expense against active trip budget"""
        
        session = self.get_active_trip_session(employee_id)
        if not session:
            return False
        
        expense_type_str = expense_type.value
        
        # Update used and remaining budgets
        if expense_type_str in session.used_budgets:
            session.used_budgets[expense_type_str] += amount
            session.remaining_budgets[expense_type_str] -= amount
            
            # Update trip record
            if session.trip_id in self.official_trips:
                trip = self.official_trips[session.trip_id]
                trip.expenses_submitted += amount
                trip.remaining_budget -= amount
                trip.updated_at = datetime.utcnow()
            
            logger.info(f"Recorded expense of ₹{amount} for {expense_type_str} in trip {session.trip_id}")
            return True
        
        return False
    
    def get_employee_trips(
        self, 
        employee_id: str, 
        status: Optional[TripStatus] = None
    ) -> List[OfficialTrip]:
        """Get all trips for an employee"""
        
        trips = [trip for trip in self.official_trips.values() if trip.employee_id == employee_id]
        
        if status:
            trips = [trip for trip in trips if trip.status == status]
        
        # Sort by start date (most recent first)
        trips.sort(key=lambda x: x.start_date, reverse=True)
        
        return trips
    
    def get_trip_by_id(self, trip_id: str) -> Optional[OfficialTrip]:
        """Get trip by ID"""
        return self.official_trips.get(trip_id)
    
    async def complete_trip(self, trip_id: str) -> OfficialTrip:
        """Mark trip as completed and store in database"""
        from database import db_manager
        
        if trip_id not in self.official_trips:
            raise ValueError(f"Trip {trip_id} not found")
        
        trip = self.official_trips[trip_id]
        trip.status = TripStatus.COMPLETED
        trip.updated_at = datetime.utcnow()
        
        # Remove active session if exists
        if trip.employee_id in self.active_trip_sessions:
            session = self.active_trip_sessions[trip.employee_id]
            if session.trip_id == trip_id:
                del self.active_trip_sessions[trip.employee_id]
        
        # Store completed trip in database for persistent access
        try:
            # Get bills associated with this trip to calculate totals
            bills = await db_manager.get_bills_by_trip(trip_id)
            total_bills = len(bills)
            total_amount = sum(float(clean_decimal(bill.get('amount', 0))) for bill in bills)
            budget_utilization = (total_amount / float(clean_decimal(trip.total_allocated))) * 100 if trip.total_allocated > 0 else 0
            
            # Get employee info for the completed trip record
            from services.mongodb_service import mongodb_service
            mongo_user = mongodb_service.find_user_by_id(trip.employee_id)
            employee_name = mongo_user.get('full_name', 'Unknown') if mongo_user else 'Unknown'
            
            # Get PostgreSQL user ID
            pg_user = await db_manager.get_user_by_email(mongo_user.get('email')) if mongo_user else None
            employee_pg_id = pg_user['id'] if pg_user else None
            
            if employee_pg_id:
                completed_trip_data = {
                    'trip_id': trip_id,
                    'employee_id': employee_pg_id,
                    'employee_name': employee_name,
                    'trip_purpose': trip.trip_purpose,
                    'destination_city': trip.destination_city,
                    'start_date': trip.start_date,
                    'end_date': trip.end_date,
                    'duration_days': trip.duration_days,
                    'designation': trip.designation.value,
                    'city_tier': trip.destination_tier.value,
                    'allocated_budget': float(trip.total_allocated),
                    'total_bills': total_bills,
                    'total_amount': total_amount,
                    'budget_utilization': round(budget_utilization, 2),
                    'trip_status': 'completed',
                    'submission_status': 'not_submitted',
                    'manager_id': pg_user.get('manager_id') if pg_user else None
                }
                
                completed_trip_id = await db_manager.create_completed_trip(completed_trip_data)
                if completed_trip_id:
                    logger.info(f"Trip {trip_id} stored in completed trips database with ID {completed_trip_id}")
                else:
                    logger.warning(f"Failed to store completed trip {trip_id} in database")
            else:
                logger.warning(f"Could not find PostgreSQL user for trip {trip_id}")
                
        except Exception as e:
            logger.error(f"Error storing completed trip {trip_id}: {e}")
            # Don't fail the completion if database storage fails
        
        logger.info(f"Trip {trip_id} marked as completed")
        return trip
    
    async def submit_trip_for_approval(
        self,
        trip_id: str,
        employee_id: str,
        manager_id: int,
        submission_notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Submit a completed trip with all bills for manager approval"""
        from database import db_manager
        
        if trip_id not in self.official_trips:
            raise ValueError(f"Trip {trip_id} not found")
        
        trip = self.official_trips[trip_id]
        
        if trip.status != TripStatus.COMPLETED:
            raise ValueError(f"Trip {trip_id} must be completed before submission")
        
        # Get all bills for this trip
        trip_bills = await db_manager.get_trip_bills(trip_id)
        
        if not trip_bills:
            raise ValueError(f"No bills found for trip {trip_id}")
        
        # Calculate totals
        total_bills = len(trip_bills)
        total_amount = sum(clean_decimal(bill['amount']) for bill in trip_bills)
        budget_utilization = (total_amount / trip.total_allocated * 100) if trip.total_allocated > 0 else 0
        
        # Create trip submission
        # Handle both integer and string employee IDs
        if isinstance(employee_id, str):
            try:
                employee_id_int = int(employee_id)
            except ValueError:
                raise ValueError(f"Invalid employee_id format: {employee_id}. Expected integer or numeric string.")
        else:
            employee_id_int = employee_id
            
        submission_data = {
            'trip_id': trip_id,
            'employee_id': employee_id_int,
            'employee_name': trip.employee_name,
            'trip_purpose': trip.trip_purpose,
            'destination_city': trip.destination_city,
            'start_date': trip.start_date,
            'end_date': trip.end_date,
            'duration_days': trip.duration_days,
            'total_bills': total_bills,
            'total_amount': float(total_amount),
            'allocated_budget': float(trip.total_allocated),
            'budget_utilization': float(budget_utilization),
            'manager_id': manager_id
        }
        
        submission_id = await db_manager.create_trip_submission(submission_data)
        
        # Update all bills to indicate they're part of a trip submission
        await db_manager.update_bills_trip_status(trip_id, 'trip_submitted')
        
        # Update completed trip status to indicate it's been submitted
        await db_manager.update_completed_trip_submission_status(trip_id, 'submitted')
        
        logger.info(f"Trip {trip_id} submitted for approval with {total_bills} bills totaling {total_amount}")
        
        return {
            'submission_id': submission_id,
            'trip_id': trip_id,
            'total_bills': total_bills,
            'total_amount': float(total_amount),
            'budget_utilization': float(budget_utilization),
            'message': f'Trip submitted successfully with {total_bills} bills for manager approval'
        }
    
    def cleanup_expired_sessions(self):
        """Clean up expired trip sessions"""
        today = date.today()
        expired_sessions = []
        
        for employee_id, session in self.active_trip_sessions.items():
            if session.trip_end < today:
                expired_sessions.append(employee_id)
                
                # Mark trip as completed if still active
                if session.trip_id in self.official_trips:
                    trip = self.official_trips[session.trip_id]
                    if trip.status == TripStatus.ACTIVE:
                        trip.status = TripStatus.COMPLETED
                        trip.updated_at = datetime.utcnow()
        
        # Remove expired sessions
        for employee_id in expired_sessions:
            del self.active_trip_sessions[employee_id]
            logger.info(f"Cleaned up expired trip session for employee {employee_id}")
        
        logger.info(f"Cleaned up {len(expired_sessions)} expired trip sessions")

    async def update_trip_justification(self, trip_id: str, justification: str) -> bool:
        """Update justification for a rejected trip"""
        from database import db_manager
        
        # Update in memory if it exists
        if trip_id in self.official_trips:
            self.official_trips[trip_id].justification = justification
            # If it was rejected, move it back to pending for manager to see it again
            if self.official_trips[trip_id].status == TripStatus.REJECTED:
                self.official_trips[trip_id].status = TripStatus.PENDING
            self.official_trips[trip_id].updated_at = datetime.utcnow()
        
        # Update in persistent database
        return await db_manager.update_trip_justification(trip_id, justification)

    async def load_from_db(self):
        """Load all trips from the persistent database into memory"""
        if self.is_loaded:
            return
            
        try:
            from database import db_manager
            from models.budget_models import TripStatus, CityTier, EmployeeDesignation
            from services.mongodb_service import mongodb_service
            
            # Fetch all completed/approved/pending trips
            query = "SELECT * FROM app_completed_trips"
            db_trips = await db_manager.execute_query(query)
            
            # Pre-fetch users to map SQLite IDs to MongoDB IDs
            user_mapping = {} # pg_id -> mongo_id
            
            for db_trip in db_trips:
                trip_id = db_trip['trip_id']
                if trip_id in self.official_trips:
                    continue
                
                pg_employee_id = db_trip['employee_id']
                if pg_employee_id not in user_mapping:
                    # Get user email from SQLite
                    pg_user = await db_manager.get_user_by_id(pg_employee_id)
                    if pg_user:
                        email = pg_user['email']
                        # Get user from MongoDB
                        mongo_user = mongodb_service.find_user_by_email(email)
                        if mongo_user:
                            user_mapping[pg_employee_id] = str(mongo_user['_id'])
                
                mongo_id = user_mapping.get(pg_employee_id)
                if not mongo_id:
                    logger.warning(f"Could not map SQLite user {pg_employee_id} to MongoDB for trip {trip_id}")
                    # Use the integer ID as a fallback string
                    mongo_id = str(pg_employee_id)
                
                # Parse dates
                start_date = db_trip['start_date']
                if isinstance(start_date, str):
                    start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                
                end_date = db_trip['end_date']
                if isinstance(end_date, str):
                    end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
                
                # Reconstruct designation and tier
                designation = self.get_designation_from_string(db_trip['designation'])
                city_tier = CityTier(db_trip['city_tier'])
                
                # Recalculate duration and budget
                duration_days = (end_date - start_date).days + 1
                allocated_budget = self.calculate_trip_budget(designation, db_trip['destination_city'], duration_days)
                total_allocated = clean_decimal(db_trip['allocated_budget'])
                
                # Create OfficialTrip object
                trip = OfficialTrip(
                    trip_id=trip_id,
                    employee_id=mongo_id,
                    employee_name=db_trip['employee_name'],
                    designation=designation,
                    trip_purpose=db_trip['trip_purpose'],
                    destination_city=db_trip['destination_city'],
                    destination_tier=city_tier,
                    start_date=start_date,
                    end_date=end_date,
                    duration_days=duration_days,
                    allocated_budget=allocated_budget,
                    total_allocated=total_allocated,
                    remaining_budget=total_allocated - clean_decimal(db_trip['total_amount']),
                    status=TripStatus(db_trip['trip_status']),
                    approved_by=str(db_trip.get('approved_by')) if db_trip.get('approved_by') else None,
                    approved_at=db_trip.get('approved_at'),
                    rejection_reason=db_trip.get('rejection_reason'),
                    justification=db_trip.get('justification'),
                    expenses_submitted=clean_decimal(db_trip['total_amount']),
                    created_at=db_trip.get('created_at') if isinstance(db_trip.get('created_at'), datetime) else datetime.utcnow(),
                    updated_at=db_trip.get('updated_at') if isinstance(db_trip.get('updated_at'), datetime) else datetime.utcnow()
                )
                
                self.official_trips[trip_id] = trip
                
            self.is_loaded = True
            logger.info(f"Successfully loaded {len(db_trips)} trips from database into memory")
            
        except Exception as e:
            logger.error(f"Error loading trips from database: {e}")
            import traceback
            logger.error(traceback.format_exc())

    async def sync_trip_status(self, trip_id: str):
        """Reload a specific trip from database to sync its status"""
        try:
            from database import db_manager
            from models.budget_models import TripStatus, CityTier
            
            # Fetch updated trip from DB
            query = "SELECT * FROM app_completed_trips WHERE trip_id = ?"
            db_trip = await db_manager.fetch_one(query, trip_id)
            
            if not db_trip:
                return
                
            # Update in-memory object if it exists
            if trip_id in self.official_trips:
                trip = self.official_trips[trip_id]
                trip.status = TripStatus(db_trip['trip_status'])
                trip.rejection_reason = db_trip.get('rejection_reason')
                trip.expenses_submitted = clean_decimal(db_trip['total_amount'])
                trip.remaining_budget = trip.total_allocated - trip.expenses_submitted
                trip.updated_at = datetime.utcnow()
                logger.info(f"Synced in-memory trip {trip_id} status to {trip.status}")
                
        except Exception as e:
            logger.error(f"Error syncing trip status for {trip_id}: {e}")

# Global service instance
trip_budget_service = TripBudgetService()