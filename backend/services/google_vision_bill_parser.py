import re
import logging
from datetime import datetime, date
from typing import Optional, Tuple, List, Dict, Any
import json

logger = logging.getLogger(__name__)

class GoogleVisionBillParser:
    """
    Enhanced bill parser that uses Google Vision OCR text to extract structured financial data.
    This replaces the Gemini-based parsing with rule-based extraction optimized for Google Vision OCR output.
    """
    
    def __init__(self):
        # Enhanced patterns for better accuracy - focusing on actual totals
        self.amount_patterns = [
            # Primary total patterns - most specific first
            r'(?:total\s*amount|grand\s*total|total\s*due|amount\s*payable|final\s*amount|net\s*amount)\s*[:\-]?\s*(?:₹|rs\.?|\$|€|£)?\s*([0-9][\d,]*(?:[\.,]\d{1,2})?)',
            r'(?:total|amount)\s*[:\-]?\s*(?:₹|rs\.?|\$|€|£)?\s*([0-9][\d,]*(?:[\.,]\d{1,2})?)',
            # Flexible total patterns to handle variations like "Total 840", "Total: ₹840.00"
            r'total\s+([0-9][\d,]*(?:[\.,]\d{1,2})?)',
            r'total\s*:\s*(?:₹|rs\.?|\$|€|£)?\s*([0-9][\d,]*(?:[\.,]\d{1,2})?)',
            r'total\s*amount\s*:\s*(?:₹|rs\.?|\$|€|£)?\s*([0-9][\d,]*(?:[\.,]\d{1,2})?)',
            # Currency symbol patterns with total context
            r'(?:₹|rs\.?|\$|€|£)\s*([0-9][\d,]*(?:[\.,]\d{1,2})?)\s*(?:total|amount|grand\s*total)',
        ]
        
        # Patterns to exclude when looking for amounts (Bill No, Bill ID, etc.)
        self.exclude_amount_patterns = [
            r'(?:bill\s*no\.?|bill\s*id|invoice\s*no\.?|receipt\s*no\.?|order\s*no\.?|transaction\s*id)\s*[:\-]?\s*([0-9]+)',
            r'(?:phone|mobile|contact)\s*[:\-]?\s*([0-9]+)',
            r'(?:table\s*no\.?|table)\s*[:\-]?\s*([0-9]+)',
        ]
        
        self.tax_patterns = [
            r'(?:tax|gst|igst|cgst|sgst|vat|service\s*tax|sales\s*tax)\s*[:\-@]?\s*(?:₹|rs\.?|\$|€|£)?\s*([0-9][\d,]*(?:[\.,]\d{1,2})?)',
            r'(?:tax|gst)\s*(?:\d+%?)?\s*[:\-]?\s*(?:₹|rs\.?|\$|€|£)?\s*([0-9][\d,]*(?:[\.,]\d{1,2})?)',
        ]
        
        self.subtotal_patterns = [
            r'(?:sub\s*total|subtotal|net\s*amount|before\s*tax|amount\s*before\s*tax)\s*[:\-]?\s*(?:₹|rs\.?|\$|€|£)?\s*([0-9][\d,]*(?:[\.,]\d{1,2})?)',
        ]
        
        self.discount_patterns = [
            r'(?:discount|savings|off|reduction|less)\s*[:\-]?\s*(?:₹|rs\.?|\$|€|£)?\s*([0-9][\d,]*(?:[\.,]\d{1,2})?)',
        ]
        
        # Enhanced date patterns with better regex for dd/mm/yyyy, dd-mm-yyyy, yyyy-mm-dd
        self.date_patterns = [
            # Explicit date labels with "Date:" prefix
            r'(?:date|bill\s*date|invoice\s*date|transaction\s*date|receipt\s*date)\s*[:\-]?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(?:date|bill\s*date|invoice\s*date|transaction\s*date|receipt\s*date)\s*[:\-]?\s*(\d{2,4}[/-]\d{1,2}[/-]\d{1,2})',
            # Standard date formats (dd/mm/yyyy, dd-mm-yyyy, yyyy-mm-dd)
            r'\b(\d{1,2}[/-]\d{1,2}[/-]20\d{2})\b',  # dd/mm/yyyy or dd-mm-yyyy
            r'\b(20\d{2}[/-]\d{1,2}[/-]\d{1,2})\b',  # yyyy-mm-dd or yyyy/mm/dd
            r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2})\b',    # dd/mm/yy or dd-mm-yy
            # Date with time (often more reliable)
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\s+\d{1,2}:\d{2}',
            r'(\d{2,4}[/-]\d{1,2}[/-]\d{1,2})\s+\d{1,2}:\d{2}',
            # Month name formats
            r'(?:date|bill\s*date|invoice\s*date|transaction\s*date|receipt\s*date)\s*[:\-]?\s*(\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s+\d{2,4})',
            r'(?:date|bill\s*date|invoice\s*date|transaction\s*date|receipt\s*date)\s*[:\-]?\s*((?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s+\d{1,2},?\s+\d{2,4})',
            r'\b(\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s+20\d{2})\b',
            r'\b((?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s+\d{1,2},?\s+20\d{2})\b',
        ]
        
        # Enhanced vendor patterns - extract from first block before contact info
        self.vendor_patterns = [
            r'(?:merchant|vendor|store|business|company)[:\s]*([^\n\r]+)',
            r'(?:^|\n)([A-Z][A-Z\s&.,]+(?:LLC|INC|CORP|LTD|PVT|PRIVATE|LIMITED)?)',
            r'thank\s+you\s+for\s+visiting\s+([^\n\r]+)',
            r'welcome\s+to\s+([^\n\r]+)',
            r'([A-Z][A-Za-z\s&.,]{3,30})\s*(?:restaurant|cafe|hotel|store|shop|mart|mall)',
        ]
        
        # Patterns to identify where vendor name section ends
        self.vendor_end_patterns = [
            r'(?:contact|e-mail|email|phone|mobile|address|website)',
        ]
        
        # Bill type classification keywords
        self.bill_type_keywords = {
            'food': [
                'restaurant', 'cafe', 'food', 'dining', 'meal', 'breakfast', 'lunch', 'dinner',
                'pizza', 'burger', 'coffee', 'bar', 'pub', 'kitchen', 'bistro', 'grill',
                'bakery', 'deli', 'catering', 'fast food', 'takeaway', 'delivery', 'swiggy', 'zomato'
            ],
            'travel': [
                'taxi', 'uber', 'ola', 'lyft', 'bus', 'train', 'flight', 'airline', 'airport',
                'metro', 'subway', 'transport', 'travel', 'cab', 'railway', 'airways',
                'parking', 'toll', 'ticket', 'booking', 'irctc', 'makemytrip', 'goibibo'
            ],
            'rent': [
                'rent', 'rental', 'lease', 'accommodation', 'room', 'apartment', 'flat',
                'house', 'property', 'housing', 'lodging', 'stay', 'residence'
            ]
        }
        
        # Currency detection patterns
        self.currency_patterns = [
            (r'₹|rs\.?|rupees?|inr', 'INR'),
            (r'\$|dollars?|usd', 'USD'),
            (r'€|euros?|eur', 'EUR'),
            (r'£|pounds?|gbp', 'GBP'),
        ]

    def parse_bill_data(self, raw_text: str, filename: str = None) -> Dict[str, Any]:
        """
        Parse OCR text from Google Vision and extract structured bill data
        Returns a dictionary with the required JSON format
        """
        try:
            if not raw_text or len(raw_text.strip()) < 10:
                raise ValueError("Insufficient text for parsing")
            
            # Clean and normalize text
            cleaned_text = self._clean_text(raw_text)
            
            # Extract all components
            employee_name = self._extract_employee_name(cleaned_text)
            bill_type = self._classify_bill_type(cleaned_text, filename)
            vendor = self._extract_vendor(cleaned_text, filename)
            date_str = self._extract_date(cleaned_text)
            amount = self._extract_amount(cleaned_text)
            
            # Create the required JSON structure
            result = {
                "employee_name": employee_name,
                "bill_type": bill_type,
                "vendor": vendor,
                "date": date_str,  # Keep as string to avoid Pydantic validation errors
                "amount": amount,
                "raw_text": raw_text
            }
            
            logger.info(f"Successfully parsed bill data: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error parsing bill data: {str(e)}")
            # Return a basic structure with raw text
            return {
                "employee_name": None,
                "bill_type": "food",  # Default fallback
                "vendor": None,
                "date": None,
                "amount": None,
                "raw_text": raw_text
            }
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize OCR text while preserving line structure"""
        if not text:
            return ""
        
        # First normalize line breaks
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # Clean each line individually to preserve line structure
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Normalize whitespace within each line
            line = re.sub(r'\s+', ' ', line).strip()
            
            # Remove common OCR artifacts
            line = re.sub(r'[|]{2,}', '', line)
            line = re.sub(r'-{3,}', '-', line)
            line = re.sub(r'_{3,}', '', line)
            
            if line:  # Only keep non-empty lines
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def _extract_employee_name(self, text: str) -> Optional[str]:
        """
        Extract employee name from bill text
        This is a placeholder - in practice, you might get this from the authenticated user
        """
        # Look for common patterns that might indicate customer/employee name
        patterns = [
            r'(?:customer|name|bill\s*to|sold\s*to)[:\s]*([A-Za-z\s]{3,30})',
            r'(?:mr\.?|ms\.?|mrs\.?)\s*([A-Za-z\s]{3,30})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                name = match.group(1).strip().title()
                if len(name) > 2 and not re.search(r'\d', name):
                    return name
        
        return None
    
    def _classify_bill_type(self, text: str, filename: str = None) -> str:
        """Classify bill type based on content and filename"""
        text_lower = text.lower()
        filename_lower = (filename or "").lower()
        
        # Check filename first
        for bill_type, keywords in self.bill_type_keywords.items():
            for keyword in keywords:
                if keyword in filename_lower:
                    return bill_type
        
        # Check text content
        type_scores = {}
        for bill_type, keywords in self.bill_type_keywords.items():
            score = 0
            for keyword in keywords:
                score += text_lower.count(keyword)
            type_scores[bill_type] = score
        
        # Return the type with highest score, default to 'food'
        if type_scores:
            best_type = max(type_scores, key=type_scores.get)
            if type_scores[best_type] > 0:
                return best_type
        
        return 'food'  # Default fallback
    
    def _extract_vendor(self, text: str, filename: str = None) -> Optional[str]:
        """Extract vendor/merchant name from first block before contact info"""
        lines = text.split('\n')
        
        # Look for vendor name in first few lines, stopping at contact info
        for i, line in enumerate(lines[:8]):  # Check first 8 lines max
            line = line.strip()
            if not line:
                continue
                
            # Stop if we hit contact information
            if any(re.search(pattern, line, re.IGNORECASE) for pattern in self.vendor_end_patterns):
                break
                
            # Skip common non-vendor lines
            if re.search(r'(?:receipt|bill|invoice|tax|total|amount|date|time|table)', line, re.IGNORECASE):
                continue
                
            # Check if this line looks like a business name
            if (len(line) > 2 and len(line) < 50 and 
                re.match(r'^[A-Za-z\s&.,\'-]+$', line) and 
                not re.search(r'\d{3,}', line)):
                
                # Check if this looks like a main business name (usually all caps or title case)
                if (re.match(r'^[A-Z][A-Z\s&.,\'-]+$', line) or  # All caps
                    re.match(r'^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*$', line)):  # Title case
                    # This looks like a main business name - return it immediately
                    return self._clean_vendor_name(line)
                elif i == 0:  # If it's the first line, use it as fallback
                    return self._clean_vendor_name(line)
        
        # Fallback: Try specific vendor patterns if line-by-line approach failed
        for pattern in self.vendor_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                vendor = match.group(1).strip()
                if len(vendor) > 2 and len(vendor) < 50:
                    # Clean up the vendor name to remove extra text
                    words = vendor.split()
                    if len(words) <= 4:
                        return self._clean_vendor_name(vendor)
                    else:
                        return self._clean_vendor_name(' '.join(words[:3]))
        
        return None
    
    def _clean_vendor_name(self, vendor: str) -> str:
        """Clean and format vendor name"""
        vendor = re.sub(r'\s+', ' ', vendor).strip()
        vendor = re.sub(r'[^\w\s&.,\'-]', '', vendor)
        return vendor.title()
    
    def _extract_date(self, text: str) -> Optional[str]:
        """Extract and normalize date to YYYY-MM-DD format"""
        for pattern in self.date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                date_str = match.group(1).strip()
                normalized_date = self._normalize_date(date_str)
                if normalized_date:
                    return normalized_date
        
        return None
    
    def _normalize_date(self, date_str: str) -> Optional[str]:
        """Normalize various date formats to YYYY-MM-DD"""
        if not date_str:
            return None
        
        # Common date formats to try
        formats = [
            '%d/%m/%Y', '%m/%d/%Y', '%Y/%m/%d',
            '%d-%m-%Y', '%m-%d-%Y', '%Y-%m-%d',
            '%d/%m/%y', '%m/%d/%y', '%y/%m/%d',
            '%d-%m-%y', '%m-%d-%y', '%y-%m-%d',
            '%d %b %Y', '%d %B %Y',
            '%b %d, %Y', '%B %d, %Y',
            '%b %d %Y', '%B %d %Y'
        ]
        
        for fmt in formats:
            try:
                parsed_date = datetime.strptime(date_str, fmt)
                # Handle 2-digit years
                if parsed_date.year < 1950:
                    parsed_date = parsed_date.replace(year=parsed_date.year + 2000)
                return parsed_date.strftime('%Y-%m-%d')
            except ValueError:
                continue
        
        return None
    
    def _extract_amount(self, text: str) -> Optional[float]:
        """Extract the main bill amount, focusing on totals and excluding Bill No/ID"""
        amounts = []
        excluded_numbers = set()
        
        # First, identify numbers to exclude (Bill No, Bill ID, etc.)
        for pattern in self.exclude_amount_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                excluded_num = self._parse_amount(match.group(1))
                if excluded_num:
                    excluded_numbers.add(excluded_num)
        
        # Extract potential amounts using our patterns
        for pattern in self.amount_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                amount_str = match.group(1)
                amount = self._parse_amount(amount_str)
                
                # Skip if this amount should be excluded
                if amount and amount > 0 and amount not in excluded_numbers:
                    # Get the context around the match to prioritize total-related amounts
                    start_pos = max(0, match.start() - 50)
                    end_pos = min(len(text), match.end() + 50)
                    context = text[start_pos:end_pos].lower()
                    
                    # Assign priority based on context
                    priority = 0
                    if any(keyword in context for keyword in ['total', 'grand total', 'amount']):
                        priority = 3  # Highest priority for total-related amounts
                    elif any(keyword in context for keyword in ['₹', 'rs', '$', '€', '£']):
                        priority = 2  # Medium priority for currency-related amounts
                    else:
                        priority = 1  # Lower priority for standalone numbers
                    
                    amounts.append((amount, priority))
        
        if not amounts:
            return None
        
        # Sort by priority first, then by amount (descending)
        amounts.sort(key=lambda x: (x[1], x[0]), reverse=True)
        
        # Filter out unreasonably large amounts (> 100,000)
        reasonable_amounts = [(amt, pri) for amt, pri in amounts if amt <= 100000]
        
        if reasonable_amounts:
            # Return the highest priority, largest reasonable amount
            return reasonable_amounts[0][0]
        elif amounts:
            # Fallback to any amount if no reasonable ones found
            return amounts[0][0]
        
        return None
    
    def _parse_amount(self, amount_str: str) -> Optional[float]:
        """Parse amount string to float"""
        if not amount_str:
            return None
        
        try:
            # Remove currency symbols and clean
            cleaned = re.sub(r'[₹$€£,\s]', '', amount_str)
            
            # Handle decimal separators
            if '.' in cleaned:
                # Assume last dot is decimal separator
                parts = cleaned.split('.')
                if len(parts) == 2 and len(parts[1]) <= 2:
                    return float(cleaned)
                else:
                    # Multiple dots, treat as thousands separator except last
                    cleaned = ''.join(parts[:-1]) + '.' + parts[-1]
                    return float(cleaned)
            else:
                return float(cleaned)
                
        except (ValueError, TypeError):
            return None

# Global instance
google_vision_bill_parser = GoogleVisionBillParser()