from typing import Dict, List, Optional, Tuple
from decimal import Decimal
from datetime import datetime, timedelta
import json
import logging
from models.budget_models import (
    EmployeeDesignation, CityTier, ExpenseType, BudgetCap, 
    EmployeeBudgetProfile, BudgetValidationResult, CityMapping,
    FundCapsSession
)
from models.user_models import TokenData

logger = logging.getLogger(__name__)

class BudgetService:
    """Service for managing employee budget caps and validation"""
    
    def __init__(self):
        self.city_mappings = self._initialize_city_mappings()
        self.budget_matrix = self._initialize_budget_matrix()
        self.active_sessions: Dict[str, FundCapsSession] = {}
    
    def _initialize_city_mappings(self) -> Dict[str, CityMapping]:
        """Initialize city to tier mappings"""
        cities = {
            # Tier 1 Cities (Metro cities with highest allowances)
            "mumbai": CityMapping(city_name="Mumbai", city_tier=CityTier.TIER_1, state="Maharashtra", region="West"),
            "delhi": CityMapping(city_name="Delhi", city_tier=CityTier.TIER_1, state="Delhi", region="North"),
            "new delhi": CityMapping(city_name="New Delhi", city_tier=CityTier.TIER_1, state="Delhi", region="North"),
            "bangalore": CityMapping(city_name="Bangalore", city_tier=CityTier.TIER_1, state="Karnataka", region="South"),
            "bengaluru": CityMapping(city_name="Bengaluru", city_tier=CityTier.TIER_1, state="Karnataka", region="South"),
            "chennai": CityMapping(city_name="Chennai", city_tier=CityTier.TIER_1, state="Tamil Nadu", region="South"),
            "hyderabad": CityMapping(city_name="Hyderabad", city_tier=CityTier.TIER_1, state="Telangana", region="South"),
            "pune": CityMapping(city_name="Pune", city_tier=CityTier.TIER_1, state="Maharashtra", region="West"),
            "kolkata": CityMapping(city_name="Kolkata", city_tier=CityTier.TIER_1, state="West Bengal", region="East"),
            
            # Tier 2 Cities (Major cities with moderate allowances)
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
            "pimpri-chinchwad": CityMapping(city_name="Pimpri-Chinchwad", city_tier=CityTier.TIER_2, state="Maharashtra", region="West"),
            "patna": CityMapping(city_name="Patna", city_tier=CityTier.TIER_2, state="Bihar", region="East"),
            "vadodara": CityMapping(city_name="Vadodara", city_tier=CityTier.TIER_2, state="Gujarat", region="West"),
            "ghaziabad": CityMapping(city_name="Ghaziabad", city_tier=CityTier.TIER_2, state="Uttar Pradesh", region="North"),
            "ludhiana": CityMapping(city_name="Ludhiana", city_tier=CityTier.TIER_2, state="Punjab", region="North"),
            "agra": CityMapping(city_name="Agra", city_tier=CityTier.TIER_2, state="Uttar Pradesh", region="North"),
            "nashik": CityMapping(city_name="Nashik", city_tier=CityTier.TIER_2, state="Maharashtra", region="West"),
            "faridabad": CityMapping(city_name="Faridabad", city_tier=CityTier.TIER_2, state="Haryana", region="North"),
            "meerut": CityMapping(city_name="Meerut", city_tier=CityTier.TIER_2, state="Uttar Pradesh", region="North"),
            "rajkot": CityMapping(city_name="Rajkot", city_tier=CityTier.TIER_2, state="Gujarat", region="West"),
            "kalyan-dombivali": CityMapping(city_name="Kalyan-Dombivali", city_tier=CityTier.TIER_2, state="Maharashtra", region="West"),
        }
        
        return cities
    
    def _initialize_budget_matrix(self) -> Dict[str, Dict[str, Dict[str, Decimal]]]:
        """Initialize budget matrix: designation -> city_tier -> expense_type -> limits"""
        
        # Budget matrix structure: {designation: {city_tier: {expense_type: {daily: amount, monthly: amount}}}}
        budget_matrix = {
            # INTERN
            EmployeeDesignation.INTERN.value: {
                CityTier.TIER_1.value: {
                    ExpenseType.TRAVEL.value: {"daily": Decimal("2000"), "monthly": Decimal("15000"), "per_trip": Decimal("5000")},
                    ExpenseType.HOTEL.value: {"daily": Decimal("3000"), "monthly": Decimal("25000"), "per_trip": Decimal("8000")},
                    ExpenseType.FOOD.value: {"daily": Decimal("800"), "monthly": Decimal("12000"), "per_trip": Decimal("2000")},
                    ExpenseType.LOCAL_TRANSPORT.value: {"daily": Decimal("500"), "monthly": Decimal("5000"), "per_trip": Decimal("1500")},
                    ExpenseType.MISCELLANEOUS.value: {"daily": Decimal("300"), "monthly": Decimal("3000"), "per_trip": Decimal("1000")},
                },
                CityTier.TIER_2.value: {
                    ExpenseType.TRAVEL.value: {"daily": Decimal("1500"), "monthly": Decimal("12000"), "per_trip": Decimal("4000")},
                    ExpenseType.HOTEL.value: {"daily": Decimal("2000"), "monthly": Decimal("18000"), "per_trip": Decimal("6000")},
                    ExpenseType.FOOD.value: {"daily": Decimal("600"), "monthly": Decimal("9000"), "per_trip": Decimal("1500")},
                    ExpenseType.LOCAL_TRANSPORT.value: {"daily": Decimal("300"), "monthly": Decimal("3500"), "per_trip": Decimal("1000")},
                    ExpenseType.MISCELLANEOUS.value: {"daily": Decimal("200"), "monthly": Decimal("2000"), "per_trip": Decimal("700")},
                },
                CityTier.TIER_3.value: {
                    ExpenseType.TRAVEL.value: {"daily": Decimal("1000"), "monthly": Decimal("8000"), "per_trip": Decimal("3000")},
                    ExpenseType.HOTEL.value: {"daily": Decimal("1500"), "monthly": Decimal("12000"), "per_trip": Decimal("4000")},
                    ExpenseType.FOOD.value: {"daily": Decimal("400"), "monthly": Decimal("6000"), "per_trip": Decimal("1000")},
                    ExpenseType.LOCAL_TRANSPORT.value: {"daily": Decimal("200"), "monthly": Decimal("2500"), "per_trip": Decimal("700")},
                    ExpenseType.MISCELLANEOUS.value: {"daily": Decimal("150"), "monthly": Decimal("1500"), "per_trip": Decimal("500")},
                },
            },
            
            # ASSOCIATE
            EmployeeDesignation.ASSOCIATE.value: {
                CityTier.TIER_1.value: {
                    ExpenseType.TRAVEL.value: {"daily": Decimal("3000"), "monthly": Decimal("25000"), "per_trip": Decimal("8000")},
                    ExpenseType.HOTEL.value: {"daily": Decimal("4000"), "monthly": Decimal("35000"), "per_trip": Decimal("12000")},
                    ExpenseType.FOOD.value: {"daily": Decimal("1200"), "monthly": Decimal("18000"), "per_trip": Decimal("3000")},
                    ExpenseType.LOCAL_TRANSPORT.value: {"daily": Decimal("700"), "monthly": Decimal("8000"), "per_trip": Decimal("2000")},
                    ExpenseType.MISCELLANEOUS.value: {"daily": Decimal("500"), "monthly": Decimal("5000"), "per_trip": Decimal("1500")},
                },
                CityTier.TIER_2.value: {
                    ExpenseType.TRAVEL.value: {"daily": Decimal("2500"), "monthly": Decimal("20000"), "per_trip": Decimal("6000")},
                    ExpenseType.HOTEL.value: {"daily": Decimal("3000"), "monthly": Decimal("25000"), "per_trip": Decimal("9000")},
                    ExpenseType.FOOD.value: {"daily": Decimal("900"), "monthly": Decimal("13500"), "per_trip": Decimal("2200")},
                    ExpenseType.LOCAL_TRANSPORT.value: {"daily": Decimal("500"), "monthly": Decimal("6000"), "per_trip": Decimal("1500")},
                    ExpenseType.MISCELLANEOUS.value: {"daily": Decimal("350"), "monthly": Decimal("3500"), "per_trip": Decimal("1000")},
                },
                CityTier.TIER_3.value: {
                    ExpenseType.TRAVEL.value: {"daily": Decimal("2000"), "monthly": Decimal("15000"), "per_trip": Decimal("5000")},
                    ExpenseType.HOTEL.value: {"daily": Decimal("2500"), "monthly": Decimal("20000"), "per_trip": Decimal("7000")},
                    ExpenseType.FOOD.value: {"daily": Decimal("700"), "monthly": Decimal("10000"), "per_trip": Decimal("1800")},
                    ExpenseType.LOCAL_TRANSPORT.value: {"daily": Decimal("400"), "monthly": Decimal("4500"), "per_trip": Decimal("1200")},
                    ExpenseType.MISCELLANEOUS.value: {"daily": Decimal("250"), "monthly": Decimal("2500"), "per_trip": Decimal("800")},
                },
            },
            
            # SENIOR_ASSOCIATE
            EmployeeDesignation.SENIOR_ASSOCIATE.value: {
                CityTier.TIER_1.value: {
                    ExpenseType.TRAVEL.value: {"daily": Decimal("4000"), "monthly": Decimal("35000"), "per_trip": Decimal("12000")},
                    ExpenseType.HOTEL.value: {"daily": Decimal("5000"), "monthly": Decimal("45000"), "per_trip": Decimal("15000")},
                    ExpenseType.FOOD.value: {"daily": Decimal("1500"), "monthly": Decimal("22000"), "per_trip": Decimal("4000")},
                    ExpenseType.LOCAL_TRANSPORT.value: {"daily": Decimal("1000"), "monthly": Decimal("12000"), "per_trip": Decimal("3000")},
                    ExpenseType.MISCELLANEOUS.value: {"daily": Decimal("700"), "monthly": Decimal("7000"), "per_trip": Decimal("2000")},
                },
                CityTier.TIER_2.value: {
                    ExpenseType.TRAVEL.value: {"daily": Decimal("3500"), "monthly": Decimal("28000"), "per_trip": Decimal("9000")},
                    ExpenseType.HOTEL.value: {"daily": Decimal("4000"), "monthly": Decimal("35000"), "per_trip": Decimal("12000")},
                    ExpenseType.FOOD.value: {"daily": Decimal("1200"), "monthly": Decimal("18000"), "per_trip": Decimal("3000")},
                    ExpenseType.LOCAL_TRANSPORT.value: {"daily": Decimal("700"), "monthly": Decimal("8500"), "per_trip": Decimal("2200")},
                    ExpenseType.MISCELLANEOUS.value: {"daily": Decimal("500"), "monthly": Decimal("5000"), "per_trip": Decimal("1500")},
                },
                CityTier.TIER_3.value: {
                    ExpenseType.TRAVEL.value: {"daily": Decimal("3000"), "monthly": Decimal("22000"), "per_trip": Decimal("7000")},
                    ExpenseType.HOTEL.value: {"daily": Decimal("3500"), "monthly": Decimal("28000"), "per_trip": Decimal("10000")},
                    ExpenseType.FOOD.value: {"daily": Decimal("1000"), "monthly": Decimal("15000"), "per_trip": Decimal("2500")},
                    ExpenseType.LOCAL_TRANSPORT.value: {"daily": Decimal("600"), "monthly": Decimal("7000"), "per_trip": Decimal("1800")},
                    ExpenseType.MISCELLANEOUS.value: {"daily": Decimal("400"), "monthly": Decimal("4000"), "per_trip": Decimal("1200")},
                },
            },
            
            # MANAGER
            EmployeeDesignation.MANAGER.value: {
                CityTier.TIER_1.value: {
                    ExpenseType.TRAVEL.value: {"daily": Decimal("6000"), "monthly": Decimal("50000"), "per_trip": Decimal("18000")},
                    ExpenseType.HOTEL.value: {"daily": Decimal("7000"), "monthly": Decimal("60000"), "per_trip": Decimal("20000")},
                    ExpenseType.FOOD.value: {"daily": Decimal("2000"), "monthly": Decimal("30000"), "per_trip": Decimal("5000")},
                    ExpenseType.LOCAL_TRANSPORT.value: {"daily": Decimal("1500"), "monthly": Decimal("18000"), "per_trip": Decimal("4000")},
                    ExpenseType.MISCELLANEOUS.value: {"daily": Decimal("1000"), "monthly": Decimal("10000"), "per_trip": Decimal("3000")},
                },
                CityTier.TIER_2.value: {
                    ExpenseType.TRAVEL.value: {"daily": Decimal("5000"), "monthly": Decimal("40000"), "per_trip": Decimal("15000")},
                    ExpenseType.HOTEL.value: {"daily": Decimal("6000"), "monthly": Decimal("50000"), "per_trip": Decimal("18000")},
                    ExpenseType.FOOD.value: {"daily": Decimal("1600"), "monthly": Decimal("24000"), "per_trip": Decimal("4000")},
                    ExpenseType.LOCAL_TRANSPORT.value: {"daily": Decimal("1200"), "monthly": Decimal("15000"), "per_trip": Decimal("3500")},
                    ExpenseType.MISCELLANEOUS.value: {"daily": Decimal("800"), "monthly": Decimal("8000"), "per_trip": Decimal("2500")},
                },
                CityTier.TIER_3.value: {
                    ExpenseType.TRAVEL.value: {"daily": Decimal("4000"), "monthly": Decimal("32000"), "per_trip": Decimal("12000")},
                    ExpenseType.HOTEL.value: {"daily": Decimal("5000"), "monthly": Decimal("40000"), "per_trip": Decimal("15000")},
                    ExpenseType.FOOD.value: {"daily": Decimal("1400"), "monthly": Decimal("20000"), "per_trip": Decimal("3500")},
                    ExpenseType.LOCAL_TRANSPORT.value: {"daily": Decimal("1000"), "monthly": Decimal("12000"), "per_trip": Decimal("3000")},
                    ExpenseType.MISCELLANEOUS.value: {"daily": Decimal("600"), "monthly": Decimal("6000"), "per_trip": Decimal("2000")},
                },
            },
            
            # SENIOR_MANAGER
            EmployeeDesignation.SENIOR_MANAGER.value: {
                CityTier.TIER_1.value: {
                    ExpenseType.TRAVEL.value: {"daily": Decimal("8000"), "monthly": Decimal("70000"), "per_trip": Decimal("25000")},
                    ExpenseType.HOTEL.value: {"daily": Decimal("10000"), "monthly": Decimal("80000"), "per_trip": Decimal("30000")},
                    ExpenseType.FOOD.value: {"daily": Decimal("2500"), "monthly": Decimal("40000"), "per_trip": Decimal("7000")},
                    ExpenseType.LOCAL_TRANSPORT.value: {"daily": Decimal("2000"), "monthly": Decimal("25000"), "per_trip": Decimal("6000")},
                    ExpenseType.MISCELLANEOUS.value: {"daily": Decimal("1500"), "monthly": Decimal("15000"), "per_trip": Decimal("4000")},
                },
                CityTier.TIER_2.value: {
                    ExpenseType.TRAVEL.value: {"daily": Decimal("7000"), "monthly": Decimal("60000"), "per_trip": Decimal("20000")},
                    ExpenseType.HOTEL.value: {"daily": Decimal("8000"), "monthly": Decimal("65000"), "per_trip": Decimal("25000")},
                    ExpenseType.FOOD.value: {"daily": Decimal("2000"), "monthly": Decimal("32000"), "per_trip": Decimal("5500")},
                    ExpenseType.LOCAL_TRANSPORT.value: {"daily": Decimal("1600"), "monthly": Decimal("20000"), "per_trip": Decimal("5000")},
                    ExpenseType.MISCELLANEOUS.value: {"daily": Decimal("1200"), "monthly": Decimal("12000"), "per_trip": Decimal("3500")},
                },
                CityTier.TIER_3.value: {
                    ExpenseType.TRAVEL.value: {"daily": Decimal("6000"), "monthly": Decimal("50000"), "per_trip": Decimal("18000")},
                    ExpenseType.HOTEL.value: {"daily": Decimal("7000"), "monthly": Decimal("55000"), "per_trip": Decimal("20000")},
                    ExpenseType.FOOD.value: {"daily": Decimal("1800"), "monthly": Decimal("28000"), "per_trip": Decimal("5000")},
                    ExpenseType.LOCAL_TRANSPORT.value: {"daily": Decimal("1400"), "monthly": Decimal("18000"), "per_trip": Decimal("4500")},
                    ExpenseType.MISCELLANEOUS.value: {"daily": Decimal("1000"), "monthly": Decimal("10000"), "per_trip": Decimal("3000")},
                },
            },
            
            # DIRECTOR
            EmployeeDesignation.DIRECTOR.value: {
                CityTier.TIER_1.value: {
                    ExpenseType.TRAVEL.value: {"daily": Decimal("12000"), "monthly": Decimal("100000"), "per_trip": Decimal("40000")},
                    ExpenseType.HOTEL.value: {"daily": Decimal("15000"), "monthly": Decimal("120000"), "per_trip": Decimal("50000")},
                    ExpenseType.FOOD.value: {"daily": Decimal("3000"), "monthly": Decimal("50000"), "per_trip": Decimal("10000")},
                    ExpenseType.LOCAL_TRANSPORT.value: {"daily": Decimal("3000"), "monthly": Decimal("40000"), "per_trip": Decimal("10000")},
                    ExpenseType.MISCELLANEOUS.value: {"daily": Decimal("2000"), "monthly": Decimal("20000"), "per_trip": Decimal("6000")},
                },
                CityTier.TIER_2.value: {
                    ExpenseType.TRAVEL.value: {"daily": Decimal("10000"), "monthly": Decimal("85000"), "per_trip": Decimal("35000")},
                    ExpenseType.HOTEL.value: {"daily": Decimal("12000"), "monthly": Decimal("100000"), "per_trip": Decimal("40000")},
                    ExpenseType.FOOD.value: {"daily": Decimal("2500"), "monthly": Decimal("40000"), "per_trip": Decimal("8000")},
                    ExpenseType.LOCAL_TRANSPORT.value: {"daily": Decimal("2500"), "monthly": Decimal("35000"), "per_trip": Decimal("8000")},
                    ExpenseType.MISCELLANEOUS.value: {"daily": Decimal("1800"), "monthly": Decimal("18000"), "per_trip": Decimal("5000")},
                },
                CityTier.TIER_3.value: {
                    ExpenseType.TRAVEL.value: {"daily": Decimal("8000"), "monthly": Decimal("70000"), "per_trip": Decimal("25000")},
                    ExpenseType.HOTEL.value: {"daily": Decimal("10000"), "monthly": Decimal("80000"), "per_trip": Decimal("30000")},
                    ExpenseType.FOOD.value: {"daily": Decimal("2200"), "monthly": Decimal("35000"), "per_trip": Decimal("7000")},
                    ExpenseType.LOCAL_TRANSPORT.value: {"daily": Decimal("2000"), "monthly": Decimal("28000"), "per_trip": Decimal("7000")},
                    ExpenseType.MISCELLANEOUS.value: {"daily": Decimal("1500"), "monthly": Decimal("15000"), "per_trip": Decimal("4000")},
                },
            },
            
            # SENIOR_DIRECTOR
            EmployeeDesignation.SENIOR_DIRECTOR.value: {
                CityTier.TIER_1.value: {
                    ExpenseType.TRAVEL.value: {"daily": Decimal("15000"), "monthly": Decimal("150000"), "per_trip": Decimal("60000")},
                    ExpenseType.HOTEL.value: {"daily": Decimal("20000"), "monthly": Decimal("180000"), "per_trip": Decimal("70000")},
                    ExpenseType.FOOD.value: {"daily": Decimal("4000"), "monthly": Decimal("70000"), "per_trip": Decimal("15000")},
                    ExpenseType.LOCAL_TRANSPORT.value: {"daily": Decimal("4000"), "monthly": Decimal("60000"), "per_trip": Decimal("15000")},
                    ExpenseType.MISCELLANEOUS.value: {"daily": Decimal("3000"), "monthly": Decimal("30000"), "per_trip": Decimal("10000")},
                },
                CityTier.TIER_2.value: {
                    ExpenseType.TRAVEL.value: {"daily": Decimal("12000"), "monthly": Decimal("120000"), "per_trip": Decimal("50000")},
                    ExpenseType.HOTEL.value: {"daily": Decimal("18000"), "monthly": Decimal("150000"), "per_trip": Decimal("60000")},
                    ExpenseType.FOOD.value: {"daily": Decimal("3500"), "monthly": Decimal("60000"), "per_trip": Decimal("12000")},
                    ExpenseType.LOCAL_TRANSPORT.value: {"daily": Decimal("3500"), "monthly": Decimal("50000"), "per_trip": Decimal("12000")},
                    ExpenseType.MISCELLANEOUS.value: {"daily": Decimal("2500"), "monthly": Decimal("25000"), "per_trip": Decimal("8000")},
                },
                CityTier.TIER_3.value: {
                    ExpenseType.TRAVEL.value: {"daily": Decimal("10000"), "monthly": Decimal("100000"), "per_trip": Decimal("40000")},
                    ExpenseType.HOTEL.value: {"daily": Decimal("15000"), "monthly": Decimal("120000"), "per_trip": Decimal("50000")},
                    ExpenseType.FOOD.value: {"daily": Decimal("3000"), "monthly": Decimal("50000"), "per_trip": Decimal("10000")},
                    ExpenseType.LOCAL_TRANSPORT.value: {"daily": Decimal("3000"), "monthly": Decimal("40000"), "per_trip": Decimal("10000")},
                    ExpenseType.MISCELLANEOUS.value: {"daily": Decimal("2000"), "monthly": Decimal("20000"), "per_trip": Decimal("6000")},
                },
            },
            
            # VP (Vice President)
            EmployeeDesignation.VP.value: {
                CityTier.TIER_1.value: {
                    ExpenseType.TRAVEL.value: {"daily": Decimal("20000"), "monthly": Decimal("200000"), "per_trip": Decimal("80000")},
                    ExpenseType.HOTEL.value: {"daily": Decimal("25000"), "monthly": Decimal("250000"), "per_trip": Decimal("100000")},
                    ExpenseType.FOOD.value: {"daily": Decimal("5000"), "monthly": Decimal("100000"), "per_trip": Decimal("20000")},
                    ExpenseType.LOCAL_TRANSPORT.value: {"daily": Decimal("5000"), "monthly": Decimal("80000"), "per_trip": Decimal("20000")},
                    ExpenseType.MISCELLANEOUS.value: {"daily": Decimal("4000"), "monthly": Decimal("40000"), "per_trip": Decimal("15000")},
                },
                CityTier.TIER_2.value: {
                    ExpenseType.TRAVEL.value: {"daily": Decimal("18000"), "monthly": Decimal("180000"), "per_trip": Decimal("70000")},
                    ExpenseType.HOTEL.value: {"daily": Decimal("22000"), "monthly": Decimal("220000"), "per_trip": Decimal("85000")},
                    ExpenseType.FOOD.value: {"daily": Decimal("4500"), "monthly": Decimal("85000"), "per_trip": Decimal("18000")},
                    ExpenseType.LOCAL_TRANSPORT.value: {"daily": Decimal("4500"), "monthly": Decimal("70000"), "per_trip": Decimal("18000")},
                    ExpenseType.MISCELLANEOUS.value: {"daily": Decimal("3500"), "monthly": Decimal("35000"), "per_trip": Decimal("12000")},
                },
                CityTier.TIER_3.value: {
                    ExpenseType.TRAVEL.value: {"daily": Decimal("15000"), "monthly": Decimal("150000"), "per_trip": Decimal("60000")},
                    ExpenseType.HOTEL.value: {"daily": Decimal("20000"), "monthly": Decimal("180000"), "per_trip": Decimal("70000")},
                    ExpenseType.FOOD.value: {"daily": Decimal("4000"), "monthly": Decimal("70000"), "per_trip": Decimal("15000")},
                    ExpenseType.LOCAL_TRANSPORT.value: {"daily": Decimal("4000"), "monthly": Decimal("60000"), "per_trip": Decimal("15000")},
                    ExpenseType.MISCELLANEOUS.value: {"daily": Decimal("3000"), "monthly": Decimal("30000"), "per_trip": Decimal("10000")},
                },
            },
            
            # SVP (Senior Vice President)
            EmployeeDesignation.SVP.value: {
                CityTier.TIER_1.value: {
                    ExpenseType.TRAVEL.value: {"daily": Decimal("30000"), "monthly": Decimal("300000"), "per_trip": Decimal("120000")},
                    ExpenseType.HOTEL.value: {"daily": Decimal("35000"), "monthly": Decimal("350000"), "per_trip": Decimal("150000")},
                    ExpenseType.FOOD.value: {"daily": Decimal("7000"), "monthly": Decimal("150000"), "per_trip": Decimal("30000")},
                    ExpenseType.LOCAL_TRANSPORT.value: {"daily": Decimal("7000"), "monthly": Decimal("120000"), "per_trip": Decimal("30000")},
                    ExpenseType.MISCELLANEOUS.value: {"daily": Decimal("5000"), "monthly": Decimal("50000"), "per_trip": Decimal("20000")},
                },
                CityTier.TIER_2.value: {
                    ExpenseType.TRAVEL.value: {"daily": Decimal("25000"), "monthly": Decimal("250000"), "per_trip": Decimal("100000")},
                    ExpenseType.HOTEL.value: {"daily": Decimal("30000"), "monthly": Decimal("300000"), "per_trip": Decimal("120000")},
                    ExpenseType.FOOD.value: {"daily": Decimal("6000"), "monthly": Decimal("120000"), "per_trip": Decimal("25000")},
                    ExpenseType.LOCAL_TRANSPORT.value: {"daily": Decimal("6000"), "monthly": Decimal("100000"), "per_trip": Decimal("25000")},
                    ExpenseType.MISCELLANEOUS.value: {"daily": Decimal("4500"), "monthly": Decimal("45000"), "per_trip": Decimal("18000")},
                },
                CityTier.TIER_3.value: {
                    ExpenseType.TRAVEL.value: {"daily": Decimal("20000"), "monthly": Decimal("200000"), "per_trip": Decimal("80000")},
                    ExpenseType.HOTEL.value: {"daily": Decimal("25000"), "monthly": Decimal("250000"), "per_trip": Decimal("100000")},
                    ExpenseType.FOOD.value: {"daily": Decimal("5000"), "monthly": Decimal("100000"), "per_trip": Decimal("20000")},
                    ExpenseType.LOCAL_TRANSPORT.value: {"daily": Decimal("5000"), "monthly": Decimal("80000"), "per_trip": Decimal("20000")},
                    ExpenseType.MISCELLANEOUS.value: {"daily": Decimal("4000"), "monthly": Decimal("40000"), "per_trip": Decimal("15000")},
                },
            },
        }
        
        return budget_matrix
    
    def get_city_tier(self, city_name: str) -> CityTier:
        """Get city tier for a given city name"""
        city_key = city_name.lower().strip()
        
        if city_key in self.city_mappings:
            return self.city_mappings[city_key].city_tier
        
        # Default to Tier 3 for unknown cities
        logger.warning(f"City '{city_name}' not found in mappings, defaulting to Tier 3")
        return CityTier.TIER_3
    
    def get_budget_caps(self, designation: EmployeeDesignation, city_tier: CityTier) -> Dict[str, Dict[str, Decimal]]:
        """Get budget caps for a specific designation and city tier"""
        try:
            return self.budget_matrix[designation.value][city_tier.value]
        except KeyError:
            logger.error(f"Budget caps not found for designation: {designation}, city_tier: {city_tier}")
            # Return default minimal caps
            return {
                ExpenseType.TRAVEL.value: {"daily": Decimal("1000"), "monthly": Decimal("10000"), "per_trip": Decimal("3000")},
                ExpenseType.HOTEL.value: {"daily": Decimal("1500"), "monthly": Decimal("15000"), "per_trip": Decimal("5000")},
                ExpenseType.FOOD.value: {"daily": Decimal("500"), "monthly": Decimal("7500"), "per_trip": Decimal("1500")},
                ExpenseType.LOCAL_TRANSPORT.value: {"daily": Decimal("300"), "monthly": Decimal("3000"), "per_trip": Decimal("1000")},
                ExpenseType.MISCELLANEOUS.value: {"daily": Decimal("200"), "monthly": Decimal("2000"), "per_trip": Decimal("600")},
            }
    
    def create_employee_budget_profile(self, employee_id: str, designation: EmployeeDesignation, 
                                     work_city: str, travel_city: Optional[str] = None) -> EmployeeBudgetProfile:
        """Create a comprehensive budget profile for an employee"""
        
        work_city_tier = self.get_city_tier(work_city)
        travel_city_tier = self.get_city_tier(travel_city) if travel_city else work_city_tier
        
        # Use the higher tier (more expensive city) for budget allocation
        applicable_tier = work_city_tier if work_city_tier.value == CityTier.TIER_1.value else travel_city_tier
        
        budget_caps = self.get_budget_caps(designation, applicable_tier)
        
        profile = EmployeeBudgetProfile(
            employee_id=employee_id,
            designation=designation,
            work_city=work_city,
            city_tier=applicable_tier,
            travel_budget=budget_caps.get(ExpenseType.TRAVEL.value, {}),
            hotel_budget=budget_caps.get(ExpenseType.HOTEL.value, {}),
            food_budget=budget_caps.get(ExpenseType.FOOD.value, {}),
            local_transport_budget=budget_caps.get(ExpenseType.LOCAL_TRANSPORT.value, {}),
            miscellaneous_budget=budget_caps.get(ExpenseType.MISCELLANEOUS.value, {}),
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat()
        )
        
        return profile
    
    def create_fund_caps_session(self, employee_id: str, designation: EmployeeDesignation, 
                               work_city: str, travel_city: Optional[str] = None) -> FundCapsSession:
        """Create a session-based fund caps for real-time validation"""
        
        work_city_tier = self.get_city_tier(work_city)
        travel_city_tier = self.get_city_tier(travel_city) if travel_city else work_city_tier
        
        # Use the higher tier for budget allocation
        applicable_work_tier = work_city_tier
        applicable_travel_tier = travel_city_tier
        
        budget_caps = self.get_budget_caps(designation, applicable_work_tier)
        
        # Create session ID
        session_id = f"{employee_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        # Convert Decimal to dict format for session storage
        fund_caps = {}
        for expense_type, limits in budget_caps.items():
            fund_caps[expense_type] = {
                "daily_limit": limits["daily"],
                "monthly_limit": limits["monthly"],
                "per_trip_limit": limits.get("per_trip", Decimal("0"))
            }
        
        session = FundCapsSession(
            employee_id=employee_id,
            session_id=session_id,
            designation=designation,
            work_city_tier=applicable_work_tier,
            travel_city_tier=applicable_travel_tier,
            fund_caps=fund_caps,
            created_at=datetime.utcnow().isoformat(),
            expires_at=(datetime.utcnow() + timedelta(hours=8)).isoformat()  # 8-hour session
        )
        
        # Store in active sessions
        self.active_sessions[session_id] = session
        
        logger.info(f"Created fund caps session for employee {employee_id} with designation {designation}")
        
        return session
    
    def get_active_session(self, employee_id: str) -> Optional[FundCapsSession]:
        """Get active session for an employee"""
        for session_id, session in self.active_sessions.items():
            if (session.employee_id == employee_id and 
                datetime.fromisoformat(session.expires_at) > datetime.utcnow()):
                return session
        return None
    
    def validate_expense_against_budget(self, session: FundCapsSession, expense_type: ExpenseType, 
                                      amount: Decimal, current_daily_usage: Decimal = Decimal('0'),
                                      current_monthly_usage: Decimal = Decimal('0')) -> BudgetValidationResult:
        """Validate an expense against budget caps"""
        
        expense_caps = session.fund_caps.get(expense_type.value, {})
        daily_limit = expense_caps.get("daily_limit", Decimal('0'))
        monthly_limit = expense_caps.get("monthly_limit", Decimal('0'))
        
        # Calculate remaining budgets
        remaining_daily = daily_limit - current_daily_usage
        remaining_monthly = monthly_limit - current_monthly_usage
        
        # Check if expense is within budget
        is_within_daily = amount <= remaining_daily
        is_within_monthly = amount <= remaining_monthly
        is_within_budget = is_within_daily and is_within_monthly
        
        # Generate warnings and recommendations
        warning_message = None
        recommendation = None
        
        if not is_within_daily:
            warning_message = f"Expense exceeds daily limit by ₹{amount - remaining_daily:.2f}"
            recommendation = f"Consider splitting expense across multiple days or seek approval for excess amount"
        elif not is_within_monthly:
            warning_message = f"Expense exceeds monthly limit by ₹{amount - remaining_monthly:.2f}"
            recommendation = f"Monthly budget exceeded. Seek manager approval for additional funds"
        elif remaining_daily < daily_limit * Decimal('0.2'):  # Less than 20% remaining
            warning_message = f"Daily budget running low. Only ₹{remaining_daily:.2f} remaining"
            recommendation = f"Monitor remaining expenses for the day"
        elif remaining_monthly < monthly_limit * Decimal('0.2'):  # Less than 20% remaining
            warning_message = f"Monthly budget running low. Only ₹{remaining_monthly:.2f} remaining"
            recommendation = f"Plan remaining monthly expenses carefully"
        
        return BudgetValidationResult(
            is_within_budget=is_within_budget,
            expense_type=expense_type,
            amount=amount,
            daily_limit=daily_limit,
            monthly_limit=monthly_limit,
            current_daily_usage=current_daily_usage,
            current_monthly_usage=current_monthly_usage,
            remaining_daily_budget=remaining_daily,
            remaining_monthly_budget=remaining_monthly,
            warning_message=warning_message,
            recommendation=recommendation
        )
    
    def get_designation_from_string(self, designation_str: str) -> EmployeeDesignation:
        """Convert string to EmployeeDesignation enum"""
        designation_mapping = {
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
        return designation_mapping.get(key, EmployeeDesignation.ASSOCIATE)  # Default to Associate
    
    def cleanup_expired_sessions(self):
        """Remove expired sessions"""
        current_time = datetime.utcnow()
        expired_sessions = [
            session_id for session_id, session in self.active_sessions.items()
            if datetime.fromisoformat(session.expires_at) <= current_time
        ]
        
        for session_id in expired_sessions:
            del self.active_sessions[session_id]
        
        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired budget sessions")

# Global budget service instance
budget_service = BudgetService()