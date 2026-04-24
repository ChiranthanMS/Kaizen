import re
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from models.bill_models import ParsedFinancialData, ParsedLineItem, BillType
import json

logger = logging.getLogger(__name__)

class PreciseBillParser:
    """
    Precise financial document parser that converts raw OCR text into clean JSON
    following the exact schema requirements.
    """
    
    def __init__(self):
        # Date patterns for various formats
        self.date_patterns = [
            r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})',  # YYYY-MM-DD or YYYY/MM/DD
            r'(\d{1,2}[-/]\d{1,2}[-/]\d{4})',  # DD-MM-YYYY or MM-DD-YYYY
            r'(\d{1,2}[-/]\d{1,2}[-/]\d{2})',  # DD-MM-YY or MM-DD-YY
            r'(\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s+\d{2,4})',
            r'((?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s+\d{1,2},?\s+\d{2,4})',
        ]
        
        # Amount patterns with currency symbols
        self.amount_patterns = [
            r'(?:total\s*amount|total\s*due|grand\s*total|amount\s*paid|total)\s*[:\-]?\s*(?:₹|rs\.?|\$|€|£|inr|usd|eur|gbp)?\s*([0-9][\d,]*(?:[\.,]\d{1,2})?)',
            r'(?:₹|rs\.?|\$|€|£)\s*([0-9][\d,]*(?:[\.,]\d{1,2})?)\s*(?:total|amount)?',
            r'([0-9][\d,]*(?:[\.,]\d{1,2})?)\s*(?:usd|inr|eur|gbp|aed|sar|cad|aud|sgd|myr|zar|rs\.?|dollars?)\b',
        ]
        
        # Tax patterns
        self.tax_patterns = [
            r'(?:tax|igst|cgst|sgst|vat|sales\s+tax|service\s+tax)\s*[:\-]?\s*(?:₹|rs\.?|\$|€|£)?\s*([0-9][\d,]*(?:[\.,]\d{1,2})?)',
            r'(?:tax\s*rate|tax\s*%)\s*[:\-]?\s*([0-9]+(?:[\.,]\d{1,2})?)\s*%?',
        ]
        
        # Subtotal patterns
        self.subtotal_patterns = [
            r'(?:sub\s*total|subtotal|net\s*amount|before\s*tax)\s*[:\-]?\s*(?:₹|rs\.?|\$|€|£)?\s*([0-9][\d,]*(?:[\.,]\d{1,2})?)',
        ]
        
        # Discount patterns
        self.discount_patterns = [
            r'(?:discount|savings|off|reduction)\s*[:\-]?\s*(?:₹|rs\.?|\$|€|£)?\s*([0-9][\d,]*(?:[\.,]\d{1,2})?)',
        ]
        
        # Currency patterns
        self.currency_patterns = [
            r'(?:₹|rs\.?|inr)',  # Indian Rupee
            r'(?:\$|usd|dollars?)',  # US Dollar
            r'(?:€|eur|euros?)',  # Euro
            r'(?:£|gbp|pounds?)',  # British Pound
            r'(?:aed)',  # UAE Dirham
            r'(?:sar)',  # Saudi Riyal
            r'(?:cad)',  # Canadian Dollar
            r'(?:aud)',  # Australian Dollar
            r'(?:sgd)',  # Singapore Dollar
            r'(?:myr)',  # Malaysian Ringgit
            r'(?:zar)',  # South African Rand
        ]
        
        # Bill type classification keywords
        self.bill_type_keywords = {
            BillType.RENT: [
                'hotel', 'motel', 'inn', 'resort', 'lodge', 'accommodation', 'stay',
                'booking', 'reservation', 'room', 'suite', 'hostel', 'b&b', 'airbnb',
                'apartment', 'lodging', 'rent', 'rental'
            ],
            BillType.TRAVEL: [
                'taxi', 'uber', 'lyft', 'bus', 'train', 'flight', 'airline', 'airport',
                'metro', 'subway', 'transport', 'travel', 'cab', 'railway', 'airways',
                'parking', 'toll', 'gas station', 'fuel', 'petrol', 'diesel'
            ],
            BillType.FOOD: [
                'restaurant', 'cafe', 'food', 'dining', 'meal', 'breakfast', 'lunch', 'dinner',
                'pizza', 'burger', 'coffee', 'bar', 'pub', 'kitchen', 'bistro', 'grill',
                'bakery', 'deli', 'catering', 'fast food', 'takeaway', 'delivery', 'groceries'
            ]
        }
        
        # Currency code mapping
        self.currency_mapping = {
            '₹': 'INR', 'rs': 'INR', 'inr': 'INR',
            '$': 'USD', 'usd': 'USD', 'dollars': 'USD', 'dollar': 'USD',
            '€': 'EUR', 'eur': 'EUR', 'euros': 'EUR', 'euro': 'EUR',
            '£': 'GBP', 'gbp': 'GBP', 'pounds': 'GBP', 'pound': 'GBP',
            'aed': 'AED', 'sar': 'SAR', 'cad': 'CAD', 'aud': 'AUD',
            'sgd': 'SGD', 'myr': 'MYR', 'zar': 'ZAR'
        }

    def parse_bill_text(self, raw_text: str) -> Dict[str, Any]:
        """
        Convert raw OCR text into clean JSON following the exact schema.
        Returns only valid JSON, no explanations or extra text.
        """
        try:
            if not raw_text or not raw_text.strip():
                return self._empty_response()
            
            # Clean and normalize text
            cleaned_text = self._clean_text(raw_text)
            
            # Extract all components
            date = self._extract_date(cleaned_text)
            vendor = self._extract_vendor(cleaned_text)
            bill_type = self._classify_bill_type(cleaned_text, vendor)
            currency = self._extract_currency(cleaned_text)
            subtotal = self._extract_subtotal(cleaned_text)
            tax_rate, tax_amount = self._extract_tax_info(cleaned_text)
            total_amount = self._extract_total_amount(cleaned_text)
            discount_amount = self._extract_discount(cleaned_text)
            remarks = self._extract_remarks(cleaned_text)
            line_items = self._extract_line_items(cleaned_text)
            
            # Build response according to exact schema
            result = {
                "date": date,
                "vendor": vendor,
                "bill_type": bill_type,
                "currency": currency,
                "subtotal": subtotal,
                "tax_rate_percent": tax_rate,
                "tax_amount": tax_amount,
                "total_amount": total_amount,
                "discount_amount": discount_amount,
                "remarks": remarks,
                "line_items": line_items
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error parsing bill text: {str(e)}")
            return self._empty_response()
    
    def _empty_response(self) -> Dict[str, Any]:
        """Return empty response following the schema"""
        return {
            "date": None,
            "vendor": None,
            "bill_type": None,
            "currency": None,
            "subtotal": None,
            "tax_rate_percent": None,
            "tax_amount": None,
            "total_amount": None,
            "discount_amount": None,
            "remarks": None,
            "line_items": []
        }
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize OCR text"""
        if not text:
            return ""
        
        # Keep original text structure for vendor extraction
        self._original_text = text
        
        # Normalize whitespace and line breaks for pattern matching
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return text.lower()
    
    def _extract_date(self, text: str) -> Optional[str]:
        """Extract and format date as YYYY-MM-DD"""
        for pattern in self.date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                date_str = matches[0]
                # Try to parse and format as YYYY-MM-DD
                try:
                    # Handle different date formats
                    if re.match(r'\d{4}[-/]\d{1,2}[-/]\d{1,2}', date_str):
                        # Already in YYYY-MM-DD format
                        return date_str.replace('/', '-')
                    elif re.match(r'\d{1,2}[-/]\d{1,2}[-/]\d{4}', date_str):
                        # DD-MM-YYYY or MM-DD-YYYY format
                        parts = re.split(r'[-/]', date_str)
                        # Assume DD-MM-YYYY format
                        return f"{parts[2]}-{parts[1].zfill(2)}-{parts[0].zfill(2)}"
                    elif re.match(r'\d{1,2}[-/]\d{1,2}[-/]\d{2}', date_str):
                        # DD-MM-YY format
                        parts = re.split(r'[-/]', date_str)
                        year = int(parts[2])
                        if year < 50:
                            year += 2000
                        else:
                            year += 1900
                        return f"{year}-{parts[1].zfill(2)}-{parts[0].zfill(2)}"
                    else:
                        # Try parsing month names
                        parsed_date = self._parse_text_date(date_str)
                        if parsed_date:
                            return parsed_date.strftime('%Y-%m-%d')
                except Exception:
                    continue
        return None
    
    def _parse_text_date(self, date_str: str) -> Optional[datetime]:
        """Parse dates with month names"""
        month_map = {
            'jan': 1, 'january': 1, 'feb': 2, 'february': 2, 'mar': 3, 'march': 3,
            'apr': 4, 'april': 4, 'may': 5, 'jun': 6, 'june': 6,
            'jul': 7, 'july': 7, 'aug': 8, 'august': 8, 'sep': 9, 'september': 9,
            'oct': 10, 'october': 10, 'nov': 11, 'november': 11, 'dec': 12, 'december': 12
        }
        
        try:
            # Extract components
            parts = re.findall(r'\w+', date_str.lower())
            day, month, year = None, None, None
            
            for part in parts:
                if part in month_map:
                    month = month_map[part]
                elif part.isdigit():
                    num = int(part)
                    if num > 31:  # Likely year
                        year = num
                    elif day is None:
                        day = num
            
            if day and month and year:
                if year < 100:
                    year += 2000 if year < 50 else 1900
                return datetime(year, month, day)
        except Exception:
            pass
        return None
    
    def _extract_vendor(self, text: str) -> Optional[str]:
        """Extract vendor name"""
        # Use original text for better vendor extraction
        original_text = getattr(self, '_original_text', text)
        
        # Look for common vendor patterns
        vendor_patterns = [
            r'(?:merchant|vendor|store)[:\s]*([^\n\r]+)',
            r'thank\s+you\s+for\s+visiting\s+([^\n\r]+)',
            r'welcome\s+to\s+([^\n\r]+)',
        ]
        
        for pattern in vendor_patterns:
            matches = re.findall(pattern, original_text, re.IGNORECASE)
            if matches:
                vendor = matches[0].strip()
                if len(vendor) > 2:
                    return vendor.title()
        
        # Look for business names in the first few lines of original text
        lines = [line.strip() for line in original_text.split('\n') if line.strip()][:5]
        for line in lines:
            # Skip lines that look like addresses or dates
            if re.search(r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}', line):
                continue
            if re.search(r'\d+\s+\w+\s+street|avenue|road|blvd', line, re.IGNORECASE):
                continue
            
            # Look for business-like names (all caps or title case)
            words = line.split()
            if len(words) >= 1 and len(words) <= 4:
                # Check if it looks like a business name
                if all(word.isupper() for word in words if word.isalpha()):
                    # All caps business name
                    clean_name = ' '.join(word for word in words if word.isalpha() or word in ['&', 'AND'])
                    if len(clean_name) > 3:
                        return clean_name.title()
                elif any(word[0].isupper() for word in words if word.isalpha()):
                    # Title case business name
                    clean_name = ' '.join(word for word in words if word.isalpha() or word in ['&', 'AND'])
                    if len(clean_name) > 3:
                        return clean_name.title()
        
        return None
    
    def _classify_bill_type(self, text: str, vendor: str = None) -> Optional[str]:
        """Classify bill type based on content"""
        combined_text = f"{text} {vendor or ''}".lower()
        
        # Count keyword matches for each type
        type_scores = {}
        for bill_type, keywords in self.bill_type_keywords.items():
            score = sum(1 for keyword in keywords if keyword in combined_text)
            if score > 0:
                type_scores[bill_type] = score
        
        if type_scores:
            # Return the type with highest score
            best_type = max(type_scores, key=type_scores.get)
            return best_type.value
        
        return None
    
    def _extract_currency(self, text: str) -> Optional[str]:
        """Extract currency and return ISO code"""
        for pattern in self.currency_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                currency_symbol = matches[0].lower()
                return self.currency_mapping.get(currency_symbol, currency_symbol.upper())
        
        return None
    
    def _extract_subtotal(self, text: str) -> Optional[float]:
        """Extract subtotal amount"""
        for pattern in self.subtotal_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                amount_str = matches[0]
                amount = self._parse_amount(amount_str)
                if amount is not None:
                    return amount
        return None
    
    def _extract_tax_info(self, text: str) -> tuple[Optional[float], Optional[float]]:
        """Extract tax rate and tax amount"""
        tax_rate = None
        tax_amount = None
        
        # Look for tax rate patterns first
        rate_patterns = [
            r'tax\s*\(([0-9]+(?:[\.,]\d{1,2})?)\s*%\)',
            r'(?:tax\s*rate|tax\s*%)\s*[:\-]?\s*([0-9]+(?:[\.,]\d{1,2})?)\s*%?',
        ]
        
        for pattern in rate_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                rate_str = matches[0]
                rate = self._parse_amount(rate_str)
                if rate is not None and rate <= 100:
                    tax_rate = rate
                    break
        
        # Look for tax amount patterns
        amount_patterns = [
            r'(?:tax|igst|cgst|sgst|vat|sales\s+tax|service\s+tax)\s*[:\-]?\s*(?:₹|rs\.?|\$|€|£)?\s*([0-9][\d,]*(?:[\.,]\d{1,2})?)',
        ]
        
        for pattern in amount_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                amount_str = matches[0]
                amount = self._parse_amount(amount_str)
                if amount is not None and amount > 0:
                    tax_amount = amount
                    break
        
        return tax_rate, tax_amount
    
    def _extract_total_amount(self, text: str) -> Optional[float]:
        """Extract total amount"""
        # Look for total amount patterns first
        total_patterns = [
            r'(?:total\s*amount|total\s*due|grand\s*total|total)\s*[:\-]?\s*(?:₹|rs\.?|\$|€|£)?\s*([0-9][\d,]*(?:[\.,]\d{1,2})?)',
            r'(?:₹|rs\.?|\$|€|£)\s*([0-9][\d,]*(?:[\.,]\d{1,2})?)\s*(?:total)',
        ]
        
        for pattern in total_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                amount_str = matches[-1]  # Take the last match (likely the final total)
                amount = self._parse_amount(amount_str)
                if amount is not None:
                    return amount
        
        # Fallback to general amount patterns
        for pattern in self.amount_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                amount_str = matches[-1]  # Take the last match
                amount = self._parse_amount(amount_str)
                if amount is not None:
                    return amount
        return None
    
    def _extract_discount(self, text: str) -> Optional[float]:
        """Extract discount amount"""
        for pattern in self.discount_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                amount_str = matches[0]
                amount = self._parse_amount(amount_str)
                if amount is not None:
                    return amount
        return None
    
    def _extract_remarks(self, text: str) -> Optional[str]:
        """Extract remarks like thank you messages"""
        remark_patterns = [
            r'(thank\s+you[^.!?\n]*[.!?]?)',
            r'(we\s+appreciate[^.!?\n]*[.!?]?)',
            r'(visit\s+again[^.!?\n]*[.!?]?)',
        ]
        
        for pattern in remark_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                return matches[0].strip().title()
        
        return None
    
    def _extract_line_items(self, text: str) -> List[Dict[str, Any]]:
        """Extract line items with description, quantity, unit_price, total_price"""
        line_items = []
        
        # Use original text for better line item extraction
        original_text = getattr(self, '_original_text', text)
        
        # Split text into lines for better parsing
        lines = [line.strip() for line in original_text.split('\n') if line.strip()]
        
        for line in lines:
            # Skip lines that are clearly not line items
            if any(keyword in line.lower() for keyword in ['subtotal', 'total', 'tax', 'discount', 'thank', 'date', 'address']):
                continue
            
            # Pattern 1: "2x Cheeseburger $8.50 $17.00" or "2 x Cheeseburger $8.50 $17.00"
            pattern1 = r'(\d+)\s*x?\s*([a-zA-Z][a-zA-Z\s\-&]+?)\s+\$?([0-9]+(?:\.[0-9]{1,2})?)\s+\$?([0-9]+(?:\.[0-9]{1,2})?)'
            match1 = re.search(pattern1, line, re.IGNORECASE)
            
            if match1:
                qty_str, description, price1_str, price2_str = match1.groups()
                try:
                    quantity = float(qty_str)
                    price1 = float(price1_str)
                    price2 = float(price2_str)
                    
                    # Determine unit price and total price
                    if abs(quantity * price1 - price2) < 0.01:
                        unit_price = price1
                        total_price = price2
                    else:
                        unit_price = price2 / quantity if quantity > 0 else price2
                        total_price = price2
                    
                    line_items.append({
                        "description": description.strip().title(),
                        "quantity": quantity,
                        "unit_price": unit_price,
                        "total_price": total_price
                    })
                    continue
                except ValueError:
                    pass
            
            # Pattern 2: "Cheeseburger 2 $8.50 $17.00"
            pattern2 = r'([a-zA-Z][a-zA-Z\s\-&]+?)\s+(\d+)\s+\$?([0-9]+(?:\.[0-9]{1,2})?)\s+\$?([0-9]+(?:\.[0-9]{1,2})?)'
            match2 = re.search(pattern2, line, re.IGNORECASE)
            
            if match2:
                description, qty_str, price1_str, price2_str = match2.groups()
                try:
                    quantity = float(qty_str)
                    price1 = float(price1_str)
                    price2 = float(price2_str)
                    
                    # Determine unit price and total price
                    if abs(quantity * price1 - price2) < 0.01:
                        unit_price = price1
                        total_price = price2
                    else:
                        unit_price = price2 / quantity if quantity > 0 else price2
                        total_price = price2
                    
                    line_items.append({
                        "description": description.strip().title(),
                        "quantity": quantity,
                        "unit_price": unit_price,
                        "total_price": total_price
                    })
                    continue
                except ValueError:
                    pass
            
            # Pattern 3: Simple "Item Name $price"
            pattern3 = r'([a-zA-Z][a-zA-Z\s\-&]+?)\s+\$?([0-9]+(?:\.[0-9]{1,2})?)'
            match3 = re.search(pattern3, line, re.IGNORECASE)
            
            if match3 and len(line.split()) <= 4:  # Avoid matching long sentences
                description, price_str = match3.groups()
                try:
                    price = float(price_str)
                    if price > 0 and price < 10000:  # Reasonable price range
                        line_items.append({
                            "description": description.strip().title(),
                            "quantity": 1.0,
                            "unit_price": price,
                            "total_price": price
                        })
                except ValueError:
                    pass
        
        return line_items[:10]  # Limit to 10 items
    
    def _parse_amount(self, amount_str: str) -> Optional[float]:
        """Parse amount string to float, handling various formats"""
        if not amount_str:
            return None
        
        try:
            # Remove currency symbols and spaces
            cleaned = re.sub(r'[₹$€£,\s]', '', amount_str)
            
            # Handle decimal separators
            if '.' in cleaned:
                return float(cleaned)
            else:
                return float(cleaned)
                
        except (ValueError, TypeError):
            return None

# Create service instance
precise_bill_parser = PreciseBillParser()